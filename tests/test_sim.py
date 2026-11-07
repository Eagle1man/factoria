"""Сценарии симуляции: воспроизводимость и физические исходы."""
from __future__ import annotations

import pytest
from factoria.sim.runner import run_scenario


def test_nominal_runs_clean():
    result = run_scenario("nominal", seed=1, horizon_s=120)
    metrics = result["metrics"]
    assert metrics["alarms"] == 0
    assert metrics["max_temp"] < 80
    assert metrics["output_index"] > 0
    assert metrics["uptime_pct"] > 95


def test_overload_stops_line():
    result = run_scenario("overload", seed=1, horizon_s=180)
    metrics = result["metrics"]
    assert metrics["alarms"] >= 1
    assert metrics["first_alarm_s"] is not None
    assert metrics["uptime_pct"] < 100
    assert any(event.get("detail") == 102 for event in result["events"] if event["kind"] == "alarm")


def test_hot_start_refuses_then_allows():
    result = run_scenario("hot_start", seed=1, horizon_s=30)
    refused = [event for event in result["events"] if event["kind"] == "refused"]
    assert refused, result["events"]
    assert refused[0]["detail"] == "BadInvalidState"
    assert any(
        event["kind"] == "alarm" and event.get("detail") == 101 for event in result["events"]
    )


def test_recipe_change_is_recorded():
    result = run_scenario("recipe_change", seed=1, horizon_s=60)
    assert result["metrics"]["final_recipe"] == "R4"


def test_same_seed_same_result():
    first = run_scenario("noisy", seed=42, horizon_s=120)
    second = run_scenario("noisy", seed=42, horizon_s=120)
    assert first["repro_hash"] == second["repro_hash"]
    assert first["metrics"] == second["metrics"]


def test_different_seed_differs():
    first = run_scenario("noisy", seed=42, horizon_s=120)
    second = run_scenario("noisy", seed=43, horizon_s=120)
    assert first["repro_hash"] != second["repro_hash"]


def test_unknown_scenario_rejected():
    with pytest.raises(ValueError):
        run_scenario("nope", seed=1, horizon_s=60)


def test_horizon_limits():
    with pytest.raises(ValueError):
        run_scenario("nominal", seed=1, horizon_s=5)
    with pytest.raises(ValueError):
        run_scenario("nominal", seed=1, horizon_s=7200)
