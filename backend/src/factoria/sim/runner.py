"""Запуск сценария симуляции: события, метрики, воспроизводимый хеш."""
from __future__ import annotations

import hashlib
import json
import random
from typing import Any

from factoria.sim.scenarios import SCENARIOS
from factoria.simulator.line_physics import LineState
from factoria.tags.registry import load_registry

MAX_HORIZON_S = 3600
DT = 0.5


def _line(seed: int) -> LineState:
    registry = load_registry()
    th = registry.thresholds
    return LineState(
        line_id="SIM",
        speed_threshold=th["speed_threshold"],
        speed_max=th["speed_max"],
        speed_delta_interlock=th["speed_delta_interlock"],
        temp_alarm=th["temp_alarm"],
        load_alarm=th["load_alarm"],
        load_alarm_hold_s=th["load_alarm_hold_s"],
        recipes=registry.recipes,
    )


def run_scenario(name: str, seed: int, horizon_s: int) -> dict[str, Any]:
    if name not in SCENARIOS:
        raise ValueError(f"неизвестный сценарий: {name}")
    if not 10 <= horizon_s <= MAX_HORIZON_S:
        raise ValueError(f"горизонт должен быть 10..{MAX_HORIZON_S} c")

    scenario = SCENARIOS[name]
    line = _line(seed)
    rng = random.Random(seed)
    scenario.prepare(line, rng)

    events: list[dict[str, Any]] = []
    steps = int(horizon_s / DT)
    output = 0.0
    load_sum = 0.0
    running_steps = 0
    max_temp = line.temp
    prev_alarm = line.alarm
    first_alarm: float | None = None

    for step in range(steps):
        t = step * DT
        scenario.control(t, horizon_s, line, events)
        line.step(DT)
        if scenario.noise:
            line.load = min(100.0, max(0.0, line.load + rng.uniform(-scenario.noise, scenario.noise)))

        output += line.pv * DT
        load_sum += line.load
        running_steps += 1 if line.running else 0
        max_temp = max(max_temp, line.temp)

        if line.alarm != prev_alarm:
            events.append(
                {
                    "t": round(t + DT, 2),
                    "kind": "alarm",
                    "action": "alarm",
                    "detail": line.alarm,
                }
            )
            if line.alarm and first_alarm is None:
                first_alarm = round(t + DT, 2)
            prev_alarm = line.alarm

    metrics = {
        "output_index": round(output / 1200, 2),
        "max_temp": round(max_temp, 2),
        "avg_load": round(load_sum / steps, 2),
        "uptime_pct": round(running_steps / steps * 100, 2),
        "alarms": sum(1 for event in events if event["kind"] == "alarm" and event["detail"]),
        "first_alarm_s": first_alarm,
        "final_recipe": line.recipe,
    }
    payload = {
        "scenario": name,
        "seed": seed,
        "horizon_s": horizon_s,
        "metrics": metrics,
        "events": events,
    }
    payload["repro_hash"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()[:16]
    return payload
