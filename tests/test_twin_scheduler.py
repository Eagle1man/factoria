"""Автоматические снимки двойника по расписанию."""
from __future__ import annotations

import asyncio

from sqlalchemy import delete, func, select

from factoria.adapters.stub import StubAdapter
from factoria.realtime.cache import TagCache
from factoria.storage.db import create_all, session_factory
from factoria.storage.models import TwinVersion
from factoria.tags.registry import load_registry
from factoria.twin_scheduler import take_snapshot


def _clear() -> None:
    async def clear() -> None:
        await create_all()
        async with session_factory() as session:
            await session.execute(delete(TwinVersion))
            await session.commit()

    asyncio.run(clear())


def _count() -> int:
    async def count() -> int:
        async with session_factory() as session:
            return int(await session.scalar(select(func.count()).select_from(TwinVersion)) or 0)

    return asyncio.run(count())


def make_cache(quality: str = "GOOD") -> TagCache:
    registry = load_registry()
    cache = TagCache(registry)
    for tag in registry.tags:
        cache.update(tag.id, "R1" if tag.type == "string" else 0.0, quality=quality)
    return cache


def test_take_snapshot_writes_row():
    _clear()
    registry = load_registry()
    saved = asyncio.run(take_snapshot(registry, make_cache(), StubAdapter()))

    assert saved["coverage_pct"] == 100.0
    assert saved["tags_total"] == 21
    assert _count() == 1


def test_take_snapshot_reflects_bad_quality():
    _clear()
    registry = load_registry()
    saved = asyncio.run(take_snapshot(registry, make_cache("BAD"), StubAdapter()))

    assert saved["coverage_pct"] == 0.0
    assert saved["tags_good"] == 0
    assert saved["warnings"]

def test_take_snapshot_skips_empty_cache():
    import pytest

    from factoria.realtime.cache import TagCache
    from factoria.twin_scheduler import NoDataYet

    _clear()
    registry = load_registry()
    empty = TagCache(registry)
    with pytest.raises(NoDataYet):
        asyncio.run(take_snapshot(registry, empty, StubAdapter()))
    assert _count() == 0
