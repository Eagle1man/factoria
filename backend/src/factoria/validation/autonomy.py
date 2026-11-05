"""Матрица автономности (ТЗ §6.4), этап 4a: A1 по умолчанию, A2 за флагом."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SAFE_DELTA = 60.0          # 5% от диапазона 0..1200
SAFE_TARGET = 400.0        # speed_threshold
TEMP_LIMIT = 80.0
LOAD_LIMIT = 95.0


@dataclass(frozen=True)
class AutonomyDecision:
    level: str                 # A0 | A1 | A2
    code: str | None = None
    detail: str | None = None


def _value(values: dict[str, Any], tag: str) -> float | None:
    item = values.get(tag) or {}
    raw = item.get("v")
    return float(raw) if isinstance(raw, (int, float)) and not isinstance(raw, bool) else None


def _quality(values: dict[str, Any], tag: str) -> str:
    return (values.get(tag) or {}).get("q", "BAD")


def resolve_autonomy(
    command_type: str,
    line_id: str,
    params: dict[str, Any],
    values: dict[str, Any],
    max_level: str,
) -> AutonomyDecision:
    """Возвращает уровень для команды.

    A2 разрешён только для set_setpoint и только при выполнении всех условий
    §6.4 одновременно. Любое сомнение — A1 (подтверждение человека).
    """
    if command_type != "set_setpoint":
        return AutonomyDecision("A1")

    target = params.get("setpoint_value")
    current = _value(values, f"{line_id}.Speed.SP")
    if not isinstance(target, (int, float)) or current is None:
        return AutonomyDecision("A1")

    if max_level != "A2":
        return AutonomyDecision("A1")

    for tag in (f"{line_id}.Speed.SP", f"{line_id}.Temp.PV", f"{line_id}.Load.Pct"):
        if _quality(values, tag) != "GOOD":
            return AutonomyDecision("A0", "DATA_STALE", f"{tag}: качество {_quality(values, tag)}")

    temp = _value(values, f"{line_id}.Temp.PV")
    load = _value(values, f"{line_id}.Load.Pct")
    if temp is None or load is None:
        return AutonomyDecision("A1")

    if temp > TEMP_LIMIT or load > LOAD_LIMIT:
        return AutonomyDecision("A1")

    delta = abs(float(target) - current)
    if delta <= SAFE_DELTA and float(target) <= SAFE_TARGET:
        return AutonomyDecision("A2")

    return AutonomyDecision("A1")
