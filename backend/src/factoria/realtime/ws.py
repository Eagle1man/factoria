"""WebSocket: snapshot, delta, resume (ТЗ §5.4)."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from factoria.auth.rbac import PERMISSIONS
from factoria.auth.security import decode_token
from factoria.realtime.cache import TagCache

LOG = logging.getLogger("ws")

router = APIRouter()

MAX_SUBSCRIBE_TAGS = 21
REDISCONNECT_POLICY = (1, 2, 5, 10)  # информативно: клиент реализует сам (ТЗ §8.3)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class WsSession:
    def __init__(self, ws: WebSocket, cache: TagCache, role: str) -> None:
        self.ws = ws
        self.cache = cache
        self.role = role
        self.tags: list[str] = []
        self.delta_only = True
        self.min_interval = 0.1
        self.queue: asyncio.Queue | None = None
        self._last_sent = 0.0

    async def run(self) -> None:
        sender = asyncio.create_task(self._send_loop(), name="ws-sender")
        try:
            while True:
                raw = await self.ws.receive_text()
                try:
                    message = json.loads(raw)
                except json.JSONDecodeError:
                    await self._error("bad_json")
                    continue
                await self._handle(message)
        except WebSocketDisconnect:
            pass
        finally:
            sender.cancel()
            if self.queue is not None:
                self.cache.unsubscribe(self.queue)

    async def _handle(self, message: dict) -> None:
        kind = message.get("type")
        if kind == "subscribe":
            await self._subscribe(message)
        elif kind == "resume":
            await self._resume(int(message.get("last_seq", 0)))
        elif kind == "ping":
            await self.ws.send_json({"type": "pong", "ts": _now_iso()})
        else:
            await self._error("unknown_message")

    async def _subscribe(self, message: dict) -> None:
        known = set(self.cache.known_tags())
        requested = message.get("tags") or sorted(known)
        if not isinstance(requested, list) or len(requested) > MAX_SUBSCRIBE_TAGS:
            await self._error("bad_tags")
            return
        unknown = [t for t in requested if t not in known]
        if unknown:
            await self.ws.send_json({"type": "error", "code": "unknown_tags", "tags": unknown})
            return

        if self.queue is not None:
            self.cache.unsubscribe(self.queue)
        self.tags = requested
        self.delta_only = bool(message.get("delta_only", True))
        self.min_interval = max(0.0, float(message.get("min_interval_ms", 100)) / 1000)
        self.queue = self.cache.subscribe()

        snapshot = self.cache.snapshot(self.tags)
        await self.ws.send_json({"type": "snapshot", **snapshot})
        stale = [t for t in self.tags if snapshot["values"].get(t, {}).get("q") != "GOOD"]
        if stale:
            await self.ws.send_json({"type": "error", "code": "stale", "tags": stale})

    async def _resume(self, last_seq: int) -> None:
        deltas, complete = self.cache.deltas_since(last_seq)
        if not complete:
            await self.ws.send_json({"type": "snapshot", **self.cache.snapshot(self.tags or None)})
            return
        await self.ws.send_json({"type": "resumed", "from": last_seq, "count": len(deltas)})
        for item in deltas:
            await self.ws.send_json({"type": "delta", "seq": item["seq"], "values": item["values"]})

    async def _send_loop(self) -> None:
        loop = asyncio.get_running_loop()
        buffer: dict[str, dict] = {}
        last_seq = 0
        try:
            while True:
                if self.queue is None:
                    await asyncio.sleep(0.05)
                    continue
                seq, values = await self.queue.get()
                if self.tags:
                    values = {t: v for t, v in values.items() if t in self.tags}
                    if not values:
                        continue
                buffer.update(values)
                last_seq = seq

                elapsed = loop.time() - self._last_sent
                if elapsed < self.min_interval:
                    await asyncio.sleep(self.min_interval - elapsed)
                while not self.queue.empty():
                    seq2, more = self.queue.get_nowait()
                    if self.tags:
                        more = {t: v for t, v in more.items() if t in self.tags}
                    buffer.update(more)
                    last_seq = seq2

                if self.delta_only and buffer and all(v["q"] == "BAD" for v in buffer.values()):
                    # BAD-качество не прячем: клиент обязан гасить показания (ТЗ §8.3)
                    pass
                await self.ws.send_json({"type": "delta", "seq": last_seq, "values": buffer})
                buffer = {}
                self._last_sent = loop.time()
        except (WebSocketDisconnect, RuntimeError):
            return
        except asyncio.CancelledError:
            raise

    async def _error(self, code: str) -> None:
        try:
            await self.ws.send_json({"type": "error", "code": code})
        except RuntimeError:
            pass


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token", "")
    try:
        payload = decode_token(token)
    except Exception:  # noqa: BLE001
        await websocket.close(code=4401)
        return

    role = payload.get("role", "")
    if role not in PERMISSIONS["read"]:
        await websocket.close(code=4403)
        return

    await websocket.accept()
    cache: TagCache = websocket.app.state.cache
    session = WsSession(websocket, cache, role)
    await session.run()
