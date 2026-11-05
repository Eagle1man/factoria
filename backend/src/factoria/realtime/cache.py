"""Кэш тегов с качеством, seq и воспроизведением дельт (ТЗ §5.4)."""
from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

GOOD = "GOOD"
STALE = "STALE"
BAD = "BAD"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class TagValue:
    v: Any
    q: str
    ts: datetime


class TagCache:
    """Единственный источник состояния тегов для API и WS (в памяти)."""

    def __init__(self, registry, *, ring_size: int = 2048) -> None:
        self._max_age = {t.id: t.max_age_seconds for t in registry.tags}
        self._deadband = {t.id: t.deadband for t in registry.tags}
        self._values: dict[str, TagValue] = {}
        self._seq = 0
        self._ring: deque[tuple[int, dict[str, dict[str, Any]]]] = deque(maxlen=ring_size)
        self._listeners: set[asyncio.Queue] = set()
        self.source: str = "unknown"
        self.source_changed_at: datetime | None = None

    # ---------- состояние ----------

    @property
    def seq(self) -> int:
        return self._seq

    def known_tags(self) -> list[str]:
        return list(self._max_age)

    def update(
        self,
        tag: str,
        value: Any,
        *,
        quality: str = GOOD,
        ts: datetime | None = None,
    ) -> None:
        if tag not in self._max_age:
            return
        ts = ts or utcnow()
        old = self._values.get(tag)
        self._values[tag] = TagValue(value, quality, ts)

        if old is None or old.q != quality or self._changed(tag, old.v, value):
            self._emit({tag: {"v": value, "q": quality, "ts": ts.isoformat()}})

    def _changed(self, tag: str, old: Any, new: Any) -> bool:
        band = self._deadband.get(tag, 0.0)
        if isinstance(old, (int, float)) and isinstance(new, (int, float)):
            return abs(float(new) - float(old)) >= band
        return old != new

    def _emit(self, payload: dict[str, dict[str, Any]]) -> None:
        self._seq += 1
        self._ring.append((self._seq, payload))
        for queue in list(self._listeners):
            try:
                queue.put_nowait((self._seq, payload))
            except asyncio.QueueFull:
                pass

    def mark_source_down(self) -> None:
        self.source = "down"
        self.source_changed_at = utcnow()
        for tag, val in list(self._values.items()):
            self.update(tag, val.v, quality=BAD, ts=val.ts)

    def mark_source_up(self) -> None:
        self.source = "connected"
        self.source_changed_at = utcnow()

    # ---------- чтение ----------

    def effective_quality(self, tag: str, now: datetime | None = None) -> str:
        val = self._values.get(tag)
        if val is None:
            return BAD
        if self.source == "down":
            return BAD
        age = ((now or utcnow()) - val.ts).total_seconds()
        if age > 2 * self._max_age.get(tag, 3.0):
            return STALE
        return val.q

    def snapshot(self, tags: list[str] | None = None) -> dict[str, Any]:
        wanted = tags or self.known_tags()
        values: dict[str, dict[str, Any]] = {}
        now = utcnow()
        for tag in wanted:
            val = self._values.get(tag)
            if val is None:
                values[tag] = {"v": None, "q": BAD, "ts": None}
            else:
                values[tag] = {
                    "v": val.v,
                    "q": self.effective_quality(tag, now),
                    "ts": val.ts.isoformat(),
                }
        return {"seq": self._seq, "snapshot_ts": now.isoformat(), "values": values}

    def deltas_since(self, last_seq: int) -> tuple[list[dict[str, Any]], bool]:
        """Возвращает (дельты, полный_ли) — можно ли доиграть с last_seq."""
        if last_seq >= self._seq:
            return [], True
        if not self._ring:
            return [], False
        complete = last_seq + 1 >= self._ring[0][0]
        items = [{"seq": s, "values": p} for s, p in self._ring if s > last_seq]
        return items, complete

    # ---------- подписки ----------

    def subscribe(self, maxsize: int = 512) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._listeners.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._listeners.discard(queue)
