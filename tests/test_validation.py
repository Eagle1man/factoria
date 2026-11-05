"""Валидация: стадии, interlocks, allowlist, коридор A2 (ТЗ §6)."""
from __future__ import annotations

from factoria.contract.loader import get_contract
from factoria.tags.registry import load_registry
from factoria.validation.autonomy import resolve_autonomy
from factoria.validation.pipeline import load_interlocks, validate_command

GOOD = "GOOD"


def values(sp=0.0, temp=40.0, load=30.0, quality=GOOD) -> dict:
    return {
        "L1.Speed.SP": {"v": sp, "q": quality},
        "L1.Temp.PV": {"v": temp, "q": quality},
        "L1.Load.Pct": {"v": load, "q": quality},
    }


def payload(command_type="set_setpoint", params=None, line="L1") -> dict:
    return {
        "command_id": "018f0000-0000-7000-8000-000000000001",
        "type": command_type,
        "target": {"line_id": line},
        "params": {"setpoint_value": 300} if params is None else params,
        "requested_by": {"kind": "agent", "id": "prod#1"},
        "correlation_id": "018f0000-0000-7000-8000-000000000002",
    }


def run(body, *, v=None, max_autonomy="A1", allowed=("L1", "L2", "L3")):
    return validate_command(
        body,
        contract=get_contract(),
        registry=load_registry(),
        values=values() if v is None else v,
        max_autonomy=max_autonomy,
        allowed_targets=list(allowed),
        interlocks=load_interlocks(),
    )


def test_ok_goes_to_approval_for_a1():
    result = run(payload())
    assert result.ok is True
    assert result.status == "AWAITING_APPROVAL"
    assert [stage.stage for stage in result.trace] == [
        "schema_check",
        "range_check",
        "interlock_check",
        "autonomy_check",
        "approval_gate",
    ]


def test_schema_error():
    result = run(payload(params={}))
    assert result.ok is False
    assert result.code == "SCHEMA_001"
    assert result.trace[-1].stage == "schema_check"


def test_unknown_line_is_range_error():
    result = run(payload(line="L9"))
    assert result.code == "RANGE_001"


def test_delta_interlock():
    result = run(payload(params={"setpoint_value": 900}), v=values(sp=0.0))
    assert result.code == "INTERLOCK_001"


def test_delta_below_threshold_allowed():
    result = run(payload(params={"setpoint_value": 799}), v=values(sp=0.0))
    assert result.ok is True


def test_hot_line_high_setpoint_interlock():
    result = run(payload(params={"setpoint_value": 500}), v=values(temp=85.0))
    assert result.code == "INTERLOCK_002"


def test_hot_line_low_setpoint_allowed():
    result = run(payload(params={"setpoint_value": 300}), v=values(temp=85.0))
    assert result.ok is True


def test_overload_reallocate_interlock():
    result = run(
        payload(command_type="reallocate_job", params={"job_id": "job-1"}),
        v=values(load=96.0),
    )
    assert result.code == "INTERLOCK_004"


def test_stale_data_blocks_command():
    result = run(payload(), v=values(quality="STALE"))
    assert result.code == "DATA_STALE"
    assert result.ok is False


def test_allowlist_blocks_target():
    result = run(payload(), allowed=("L2",))
    assert result.code == "AUTONOMY_001"
    assert result.autonomy == "A0"


def test_a2_corridor_lower_bound():
    # delta 59 и target 399 -> A2
    decision = resolve_autonomy(
        "set_setpoint", "L1", {"setpoint_value": 399}, values(sp=340.0), max_level="A2"
    )
    assert decision.level == "A2"


def test_a2_corridor_delta_boundary():
    assert (
        resolve_autonomy(
            "set_setpoint", "L1", {"setpoint_value": 400}, values(sp=340.0), max_level="A2"
        ).level
        == "A2"
    )
    assert (
        resolve_autonomy(
            "set_setpoint", "L1", {"setpoint_value": 401}, values(sp=340.0), max_level="A2"
        ).level
        == "A1"
    )


def test_a2_corridor_target_boundary():
    assert (
        resolve_autonomy(
            "set_setpoint", "L1", {"setpoint_value": 400}, values(sp=360.0), max_level="A2"
        ).level
        == "A2"
    )
    assert (
        resolve_autonomy(
            "set_setpoint", "L1", {"setpoint_value": 460}, values(sp=400.0), max_level="A2"
        ).level
        == "A1"
    )


def test_a2_disabled_by_flag():
    decision = resolve_autonomy(
        "set_setpoint", "L1", {"setpoint_value": 380}, values(sp=340.0), max_level="A1"
    )
    assert decision.level == "A1"


def test_a2_not_applied_to_other_commands():
    decision = resolve_autonomy(
        "switch_recipe", "L1", {"recipe_id": "R2"}, values(), max_level="A2"
    )
    assert decision.level == "A1"


def test_a2_refused_on_stale_data():
    decision = resolve_autonomy(
        "set_setpoint",
        "L1",
        {"setpoint_value": 380},
        values(sp=340.0, quality="STALE"),
        max_level="A2",
    )
    assert decision.level == "A0"
    assert decision.code == "DATA_STALE"
