"""Цифровой двойник: структура, покрытие, честные предупреждения."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from factoria.adapters.stub import StubAdapter
from factoria.model.semantic import build_semantic
from factoria.model.twin import build_twin, twin_version
from factoria.realtime.cache import TagCache
from factoria.tags.registry import load_registry


def full_cache(registry, quality: str = "GOOD") -> TagCache:
    cache = TagCache(registry)
    for tag in registry.tags:
        value = 0.0 if tag.type != "string" else "R1"
        cache.update(tag.id, value, quality=quality)
    return cache


def test_semantic_structure():
    registry = load_registry()
    model = build_semantic(registry, StubAdapter().list_open_orders())
    assert len(model.by_kind("line")) == 3
    assert len(model.by_kind("tag")) == 21
    assert len(model.by_kind("order")) == 5
    assert len(model.by_kind("spec")) == 3
    assert any(relation.kind == "has_signal" for relation in model.relations)
    assert any("не связаны с линиями" in warning for warning in model.warnings)


def test_twin_full_coverage():
    registry = load_registry()
    model = build_semantic(registry, StubAdapter().list_open_orders())
    twin = build_twin(registry, full_cache(registry), model)

    assert twin["status"] == "EXPERIMENTAL"
    assert twin["metrics"]["coverage_pct"] == 100.0
    assert twin["metrics"]["tags_good"] == 21
    assert twin["metrics"]["accuracy"] is None
    assert any("Точность двойника не измерена" in warning for warning in twin["warnings"])


def test_twin_reports_missing_data():
    registry = load_registry()
    model = build_semantic(registry, StubAdapter().list_open_orders())
    cache = full_cache(registry)
    cache.update("L2.Temp.PV", 42.0, quality="BAD")
    twin = build_twin(registry, cache, model)

    assert twin["metrics"]["tags_good"] == 20
    assert twin["metrics"]["coverage_pct"] < 100
    assert any("L2.Temp.PV" in warning for warning in twin["warnings"])


def test_twin_freshness_is_real():
    registry = load_registry()
    model = build_semantic(registry, StubAdapter().list_open_orders())
    cache = TagCache(registry)
    old = datetime.now(timezone.utc) - timedelta(seconds=4)
    for tag in registry.tags:
        cache.update(tag.id, 1.0, quality="GOOD", ts=old)
    twin = build_twin(registry, cache, model)
    assert twin["metrics"]["freshness_sec"] >= 3.5


def test_twin_version_is_stable():
    registry = load_registry()
    assert twin_version(registry) == twin_version(registry)
    assert twin_version(registry).startswith("twin-")
