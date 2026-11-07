from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from factoria.realtime.cache import BAD, GOOD, STALE, TagCache
from factoria.tags.registry import load_registry


@pytest.fixture()
def cache() -> TagCache:
    return TagCache(load_registry())


def test_update_increments_seq_and_delta(cache: TagCache):
    cache.update("L1.Speed.PV", 100.0)
    assert cache.seq == 1
    cache.update("L1.Speed.PV", 101.0)
    assert cache.seq == 2
    deltas, complete = cache.deltas_since(0)
    assert complete is True
    assert len(deltas) == 2
    assert deltas[-1]["values"]["L1.Speed.PV"]["v"] == 101.0


def test_deadband_suppresses_small_changes(cache: TagCache):
    cache.update("L1.Speed.PV", 100.0)
    seq = cache.seq
    cache.update("L1.Speed.PV", 100.2)  # deadband 0.5
    assert cache.seq == seq
    cache.update("L1.Speed.PV", 101.0)
    assert cache.seq == seq + 1


def test_quality_becomes_stale_after_two_max_age(cache: TagCache):
    old = datetime.now(timezone.utc) - timedelta(seconds=10)
    cache.update("L1.Speed.PV", 100.0, ts=old)
    assert cache.effective_quality("L1.Speed.PV") == STALE


def test_source_down_marks_everything_bad(cache: TagCache):
    cache.update("L1.Speed.PV", 100.0)
    cache.update("L2.Temp.PV", 45.0)
    cache.mark_source_down()
    assert cache.effective_quality("L1.Speed.PV") == BAD
    assert cache.snapshot()["values"]["L2.Temp.PV"]["q"] == BAD


def test_resume_incomplete_after_ring_overflow():
    cache = TagCache(load_registry(), ring_size=3)
    for value in range(10):
        cache.update("L1.Speed.PV", float(value))
    _deltas, complete = cache.deltas_since(0)
    assert complete is False


def test_resume_from_last_seq(cache: TagCache):
    cache.update("L1.Speed.PV", 1.0)
    cache.update("L1.Speed.PV", 2.0)
    deltas, complete = cache.deltas_since(1)
    assert complete is True
    assert len(deltas) == 1
    assert deltas[0]["seq"] == 2


def test_snapshot_contains_all_21_tags(cache: TagCache):
    snap = cache.snapshot()
    assert len(snap["values"]) == 21
    assert snap["values"]["L3.Recipe.ID"]["q"] == BAD


def test_subscriber_receives_updates(cache: TagCache):
    async def scenario():
        queue = cache.subscribe()
        cache.update("L1.Speed.PV", 500.0)
        seq, values = await asyncio.wait_for(queue.get(), timeout=1)
        return seq, values

    seq, values = asyncio.run(scenario())
    assert seq == 1
    assert values["L1.Speed.PV"]["v"] == 500.0
    assert values["L1.Speed.PV"]["q"] == GOOD


def test_unknown_tag_ignored(cache: TagCache):
    cache.update("L9.Nope", 1.0)
    assert cache.seq == 0
