"""История версий двойника: срезы, дельты, сравнение."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from factoria.adapters.stub import StubAdapter
from factoria.model.history import compare, list_versions, save_snapshot
from factoria.model.semantic import build_semantic
from factoria.model.twin import build_twin
from factoria.realtime.cache import TagCache
from sqlalchemy import delete

from factoria.storage.db import create_all, session_factory
from factoria.storage.models import TwinVersion
from factoria.tags.registry import load_registry


def reset_history() -> None:
    async def clear() -> None:
        await create_all()
        async with session_factory() as session:
            await session.execute(delete(TwinVersion))
            await session.commit()

    asyncio.run(clear())


def make_twin(quality: str = "GOOD", bad_tag: str | None = None) -> dict:
    registry = load_registry()
    cache = TagCache(registry)
    for tag in registry.tags:
        value = "R1" if tag.type == "string" else 0.0
        q = "BAD" if tag.id == bad_tag else quality
        cache.update(tag.id, value, quality=q)
    model = build_semantic(registry, StubAdapter().list_open_orders())
    return build_twin(registry, cache, model)


def test_snapshot_roundtrip():
    reset_history()

    async def scenario():
        async with session_factory() as session:
            first = await save_snapshot(session, make_twin())
            versions = await list_versions(session)
        return first, versions

    first, versions = asyncio.run(scenario())
    assert first["coverage_pct"] == 100.0
    assert versions[0]["id"] == first["id"]
    assert versions[0]["delta"]["coverage_pct"] is None


def test_second_snapshot_has_delta():
    reset_history()

    async def scenario():
        async with session_factory() as session:
            await save_snapshot(session, make_twin())
            await save_snapshot(session, make_twin(bad_tag="L2.Temp.PV"))
            return await list_versions(session)

    versions = asyncio.run(scenario())
    newest, previous = versions[0], versions[1]
    assert newest["tags_good"] < previous["tags_good"]
    assert newest["delta"]["tags_good"] < 0
    assert newest["delta"]["coverage_pct"] < 0


def test_compare_two_versions():
    first = {"id": 1, "built_at": "2026-11-07T10:00:00", "coverage_pct": 100.0,
             "tags_good": 21, "freshness_sec": 0.2, "version": "twin-a"}
    second = {"id": 2, "built_at": "2026-11-07T10:15:00", "coverage_pct": 95.2,
              "tags_good": 20, "freshness_sec": 0.9, "version": "twin-a"}
    result = compare(first, second)
    assert result["coverage_pct"] == -4.8
    assert result["tags_good"] == -1
    assert result["version_changed"] is False


def test_snapshot_has_warnings():
    twin = make_twin(bad_tag="L3.Load.Pct")
    assert any("L3.Load.Pct" in warning for warning in twin["warnings"])
    assert twin["metrics"]["accuracy"] is None
    assert twin["built_at"] is not None
    assert datetime.fromisoformat(twin["built_at"]).tzinfo is not None
