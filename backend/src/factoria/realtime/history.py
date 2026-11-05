"""Запись истории тегов в SQLite с ретенцией (ТЗ §3.1, R-011)."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from factoria.config import get_settings
from factoria.storage.db import session_factory
from factoria.storage.models import TagHistory

LOG = logging.getLogger("history")


class HistoryWriter:
    def __init__(self, *, retention_h: int | None = None, flush_s: float = 1.0) -> None:
        settings = get_settings()
        self.retention_h = retention_h or settings.tag_history_retention_h
        self.flush_s = flush_s
        self.queue: asyncio.Queue[tuple[str, float, str, datetime]] = asyncio.Queue(maxsize=5000)
        self._task: asyncio.Task | None = None

    def offer(self, tag: str, value, quality: str, ts: datetime) -> None:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return
        try:
            self.queue.put_nowait((tag, float(value), quality, ts))
        except asyncio.QueueFull:
            LOG.warning("очередь истории переполнена, запись пропущена")

    async def run(self) -> None:
        next_cleanup = datetime.now(timezone.utc) + timedelta(minutes=10)
        while True:
            await asyncio.sleep(self.flush_s)
            await self._flush()
            now = datetime.now(timezone.utc)
            if now >= next_cleanup:
                await self.cleanup()
                next_cleanup = now + timedelta(minutes=10)

    async def _flush(self) -> None:
        batch: list[tuple[str, float, str, datetime]] = []
        while not self.queue.empty() and len(batch) < 500:
            batch.append(self.queue.get_nowait())
        if not batch:
            return
        seen: dict[tuple[datetime, str], tuple[str, float, str]] = {}
        for tag, value, quality, ts in batch:
            seen[(ts, tag)] = (tag, value, quality)
        async with session_factory() as session:
            session.add_all(
                TagHistory(ts=ts, tag=tag, value=value, quality=quality)
                for (ts, _tag), (tag, value, quality) in seen.items()
            )
            await session.commit()

    async def cleanup(self) -> None:
        threshold = datetime.now(timezone.utc) - timedelta(hours=self.retention_h)
        async with session_factory() as session:
            result = await session.execute(delete(TagHistory).where(TagHistory.ts < threshold))
            await session.commit()
            LOG.info("ретенция: удалено строк %s", result.rowcount)

    def start(self) -> asyncio.Task:
        self._task = asyncio.create_task(self.run(), name="history-writer")
        return self._task

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            await self._flush()


writer = HistoryWriter()
