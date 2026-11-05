"""Контракт команд: схемы и границы из одного JSON (ADR-116)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from factoria.contract.loader import ContractError, get_contract, validate_envelope


def test_contract_has_five_commands():
    contract = get_contract()
    assert set(contract.commands) == {
        "set_setpoint",
        "switch_recipe",
        "line_start",
        "line_stop",
        "reallocate_job",
    }
    assert all(spec.risk == "A1" for spec in contract.commands.values())
    assert all(spec.requires_evidence for spec in contract.commands.values())


def test_setpoint_bounds_enforced():
    model = get_contract().param_model("set_setpoint")
    assert model.model_validate({"setpoint_value": 400}).setpoint_value == 400
    with pytest.raises(ValidationError):
        model.model_validate({"setpoint_value": 1201})
    with pytest.raises(ValidationError):
        model.model_validate({"setpoint_value": -1})


def test_extra_parameter_rejected():
    model = get_contract().param_model("set_setpoint")
    with pytest.raises(ValidationError):
        model.model_validate({"setpoint_value": 400, "speed": 900})


def test_recipe_enum_enforced():
    model = get_contract().param_model("switch_recipe")
    assert model.model_validate({"recipe_id": "R3"}).recipe_id == "R3"
    with pytest.raises(ValidationError):
        model.model_validate({"recipe_id": "R9"})


def test_no_params_command():
    model = get_contract().param_model("line_start")
    assert model.model_validate({}) is not None
    with pytest.raises(ValidationError):
        model.model_validate({"mode": "fast"})


def test_unknown_command_type():
    with pytest.raises(ContractError):
        get_contract().spec("emergency_stop")


def test_envelope_requires_fields():
    contract = get_contract()
    with pytest.raises(ContractError):
        validate_envelope(contract, {"type": "line_start"})
    validate_envelope(
        contract,
        {
            "command_id": "018f0000-0000-7000-8000-000000000001",
            "type": "line_start",
            "target": {"line_id": "L1"},
            "params": {},
            "requested_by": {"kind": "agent", "id": "logist#1"},
            "correlation_id": "018f0000-0000-7000-8000-000000000002",
        },
    )


def test_evidence_limited():
    contract = get_contract()
    payload = {
        "command_id": "018f0000-0000-7000-8000-000000000001",
        "type": "line_start",
        "target": {"line_id": "L1"},
        "params": {},
        "requested_by": {"kind": "agent", "id": "a"},
        "correlation_id": "018f0000-0000-7000-8000-000000000002",
        "evidence": [f"call-{index}" for index in range(contract.max_evidence + 1)],
    }
    with pytest.raises(ContractError):
        validate_envelope(contract, payload)
