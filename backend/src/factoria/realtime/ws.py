"""WebSocket: snapshot, delta, resume и command_status (ТЗ §5.4)."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from factoria.auth.rbac import PERMISSIONS
from factoria.auth.tickets import tickets
from factoria.realtime.cache import TagCache
from factoria.realtime.events import EventBus

router = APIRouter()

MAX_SUBSCRIBE_TAGS = 21


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class WsSession:
    """Три задачи: дельты, события шины, отправка. Отправка — одна, без гонок."""

    def __init__(self, ws: WebSocket, cache: TagCache, role: str, bus: EventBus) -> None:
        self.ws = ws
        self.cache = cache
        self.role = role
        self.bus = bus
        self.tags: list[str] = []
        self.delta_only = True
        self.min_interval = 0.1
        self.queue: asyncio.Queue | None = None
        self.events: asyncio.Queue = bus.subscribe()
        self.outgoing: asyncio.Queue = asyncio.Queue(maxsize=1024)

    async def run(self) -> None:
        deltas = asyncio.create_task(self._delta_loop(), name="ws-deltas")
        events = asyncio.create_task(self._event_loop(), name="ws-events")
        sender = asyncio.create_task(self._sender_loop(), name="ws-sender")
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
            for task in (deltas, events, sender):
                task.cancel()
            if self.queue is not None:
                self.cache.unsubscribe(self.queue)
            self.bus.unsubscribe(self.events)

    async def _handle(self, message: dict) -> None:
        kind = message.get("type")
        if kind == "subscribe":
            await self._subscribe(message)
        elif kind == "resume":
            await self._resume(int(message.get("last_seq", 0)))
        elif kind == "ping":
            await self.outgoing.put({"type": "pong", "ts": _now_iso()})
        else:
            await self._error("unknown_message")

    async def _subscribe(self, message: dict) -> None:
        known = set(self.cache.known_tags())
        requested = message.get("tags") or sorted(known)
        if not isinstance(requested, list) or len(requested) > MAX_SUBSCRIBE_TAGS:
            await self._error("bad_tags")
            return
        unknown = [tag for tag in requested if tag not in known]
        if unknown:
            await self.outgoing.put({"type": "error", "code": "unknown_tags", "tags": unknown})
            return

        if self.queue is not None:
            self.cache.unsubscribe(self.queue)
        self.tags = requested
        self.delta_only = bool(message.get("delta_only", True))
        self.min_interval = max(0.0, float(message.get("min_interval_ms", 100)) / 1000)
        self.queue = self.cache.subscribe()

        snapshot = self.cache.snapshot(self.tags)
        await self.outgoing.put({"type": "snapshot", **snapshot})
        stale = [tag for tag in self.tags if snapshot["values"].get(tag, {}).get("q") != "GOOD"]
        if stale:
            await self.outgoing.put({"type": "error", "code": "stale", "tags": stale})

    async def _resume(self, last_seq: int) -> None:
        deltas, complete = self.cache.deltas_since(last_seq)
        if not complete:
            await self.outgoing.put({"type": "snapshot", **self.cache.snapshot(self.tags or None)})
            return
        await self.outgoing.put({"type": "resumed", "from": last_seq, "count": len(deltas)})
        for item in deltas:
            await self.outgoing.put(
                {"type": "delta", "seq": item["seq"], "values": item["values"]}
            )

    async def _delta_loop(self) -> None:
        loop = asyncio.get_running_loop()
        buffer: dict[str, dict[str, Any]] = {}
        last_seq = 0
        try:
            while True:
                if self.queue is None:
                    await asyncio.sleep(0.05)
                    continue
                seq, values = await self.queue.get()
                if self.tags:
                    values = {tag: value for tag, value in values.items() if tag in self.tags}
                    if not values:
                        continue
                buffer.update(values)
                last_seq = seq

                elapsed = loop.time() - getattr(self, "_last_sent", 0.0)
                if elapsed < self.min_interval:
                    await asyncio.sleep(self.min_interval - elapsed)
                while not self.queue.empty():
                    seq2, more = self.queue.get_nowait()
                    if self.tags:
                        more = {tag: value for tag, value in more.items() if tag in self.tags}
                    buffer.update(more)
                    last_seq = seq2

                await self.outgoing.put(
                    {"type": "delta", "seq": last_seq, "values": buffer}
                )
                buffer = {}
                self._last_sent = loop.time()
        except asyncio.CancelledError:
            raise

    async def _event_loop(self) -> None:
        try:
            while True:
                event = await self.events.get()
                await self.outgoing.put(event)
        except asyncio.CancelledError:
            raise

    async def _sender_loop(self) -> None:
        try:
            while True:
                message = await self.outgoing.get()
                await self.ws.send_json(message)
        except (WebSocketDisconnect, RuntimeError):
            return
        except asyncio.CancelledError:
            raise

    async def _error(self, code: str) -> None:
        await self.outgoing.put({"type": "error", "code": code})


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket) -> None:
    ticket = tickets.consume(websocket.query_params.get("ticket", ""))
    if ticket is None:
        await websocket.close(code=4401)
        return

    role = ticket.role
    if role not in PERMISSIONS["read"]:
        await websocket.close(code=4403)
        return

    await websocket.accept()
    cache: TagCache = websocket.app.state.cache
    bus: EventBus = websocket.app.state.events
    session = WsSession(websocket, cache, role, bus)
    await session.run()
