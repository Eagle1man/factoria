"""Конвейер валидации: 5 стадий (ТЗ §6.1). Этап 4a — стадии 1–3 + ворота A1."""
from __future__ import annotations

import operator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml

from factoria.contract.loader import CommandSpec, Contract
from factoria.validation.autonomy import resolve_autonomy

INTERLOCKS_PATH = Path(__file__).with_name("interlocks.yaml")

OPS: dict[str, Callable[[float, float], bool]] = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
}


@dataclass
class Stage:
    stage: str
    ok: bool
    code: str | None = None
    detail: str | None = None


@dataclass
class ValidationResult:
    ok: bool
    status: str
    autonomy: str
    trace: list[Stage] = field(default_factory=list)
    code: str | None = None
    detail: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "status": self.status,
            "autonomy": self.autonomy,
            "trace": [stage.__dict__ for stage in self.trace],
            "code": self.code,
            "detail": self.detail,
        }


def load_interlocks(path: Path | str | None = None) -> list[dict[str, Any]]:
    raw = yaml.safe_load((Path(path) if path else INTERLOCKS_PATH).read_text(encoding="utf-8"))
    return list(raw.get("rules", []))


def _num(values: dict[str, Any], tag: str) -> float | None:
    item = values.get(tag) or {}
    raw = item.get("v")
    return float(raw) if isinstance(raw, (int, float)) and not isinstance(raw, bool) else None


def _check(value: float | None, op: str, limit: float) -> bool:
    if value is None:
        return False
    return OPS[op](value, limit)


def validate_command(
    payload: dict[str, Any],
    *,
    contract: Contract,
    registry,
    values: dict[str, Any],
    max_autonomy: str,
    allowed_targets: list[str],
    interlocks: list[dict[str, Any]] | None = None,
) -> ValidationResult:
    trace: list[Stage] = []
    command_type = str(payload.get("type", ""))
    target = payload.get("target") or {}
    line_id = str(target.get("line_id", ""))
    params: dict[str, Any] = payload.get("params") or {}

    # --- 1. schema_check -------------------------------------------------
    try:
        spec: CommandSpec = contract.spec(command_type)
        contract.param_model(command_type).model_validate(params)
        trace.append(Stage("schema_check", True))
    except Exception as exc:  # noqa: BLE001 - любая ошибка схемы = SCHEMA_001
        trace.append(Stage("schema_check", False, "SCHEMA_001", str(exc)))
        return ValidationResult(False, "REJECTED", "A1", trace, "SCHEMA_001", str(exc))

    # --- 2. range_check --------------------------------------------------
    if line_id not in registry.lines:
        trace.append(Stage("range_check", False, "RANGE_001", f"линия {line_id!r} не найдена"))
        return ValidationResult(False, "REJECTED", "A1", trace, "RANGE_001", "линия не найдена")

    if command_type == "set_setpoint":
        tag = registry.tag(f"{line_id}.Speed.SP")
        value = float(params["setpoint_value"])
        if tag.min is not None and value < tag.min or tag.max is not None and value > tag.max:
            detail = f"уставка {value} вне {tag.min}..{tag.max}"
            trace.append(Stage("range_check", False, "RANGE_001", detail))
            return ValidationResult(False, "REJECTED", "A1", trace, "RANGE_001", detail)

    if command_type == "switch_recipe" and params.get("recipe_id") not in registry.recipes:
        detail = f"рецепт {params.get('recipe_id')!r} не из {registry.recipes}"
        trace.append(Stage("range_check", False, "RANGE_001", detail))
        return ValidationResult(False, "REJECTED", "A1", trace, "RANGE_001", detail)
    trace.append(Stage("range_check", True))

    # --- 3. interlock_check ----------------------------------------------
    current_sp = _num(values, f"{line_id}.Speed.SP")
    context = {
        "abs_delta": (
            abs(float(params["setpoint_value"]) - current_sp)
            if command_type == "set_setpoint" and current_sp is not None
            else None
        ),
        "Temp.PV": _num(values, f"{line_id}.Temp.PV"),
        "Load.Pct": _num(values, f"{line_id}.Load.Pct"),
        "setpoint_value": params.get("setpoint_value"),
    }

    used_tags = [f"{line_id}.Speed.SP", f"{line_id}.Temp.PV", f"{line_id}.Load.Pct"]
    bad = [tag for tag in used_tags if (values.get(tag) or {}).get("q", "BAD") != "GOOD"]
    if bad:
        detail = f"нет достоверных данных: {', '.join(bad)}"
        trace.append(Stage("interlock_check", False, "DATA_STALE", detail))
        return ValidationResult(False, "REJECTED", "A1", trace, "DATA_STALE", detail)

    for rule in interlocks if interlocks is not None else load_interlocks():
        if rule.get("applies_to") and command_type not in rule["applies_to"]:
            continue
        when = rule["when"]
        key = when.get("param") or when.get("tag")
        value = context.get(key)
        if not _check(value, when["op"], float(when["value"])):
            continue
        and_param = rule.get("and_param")
        if and_param:
            if not _check(
                context.get(and_param["param"]), and_param["op"], float(and_param["value"])
            ):
                continue
        detail = rule.get("detail") or rule["id"]
        trace.append(Stage("interlock_check", False, rule["code"], detail))
        return ValidationResult(False, "REJECTED", "A1", trace, rule["code"], detail)
    trace.append(Stage("interlock_check", True))

    # --- 4. autonomy_check -----------------------------------------------
    if line_id not in allowed_targets:
        detail = f"линия {line_id} вне allowlist {allowed_targets}"
        trace.append(Stage("autonomy_check", False, "AUTONOMY_001", detail))
        return ValidationResult(False, "REJECTED", "A0", trace, "AUTONOMY_001", detail)

    decision = resolve_autonomy(command_type, line_id, params, values, max_autonomy)
    if decision.level == "A0":
        trace.append(Stage("autonomy_check", False, decision.code, decision.detail))
        return ValidationResult(False, "REJECTED", "A0", trace, decision.code, decision.detail)
    trace.append(Stage("autonomy_check", True, detail=f"уровень {decision.level}"))

    # --- 5. approval_gate ------------------------------------------------
    status = "AWAITING_APPROVAL" if decision.level == "A1" else "APPROVED"
    trace.append(Stage("approval_gate", True, detail=status))
    return ValidationResult(True, status, decision.level, trace)
