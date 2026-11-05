"""Загрузка контракта команд (ADR-116): один JSON — источник схем и границ."""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, create_model

CONTRACT_PATH = Path(__file__).with_name("commands.json")


class ContractError(ValueError):
    pass


@dataclass(frozen=True)
class ParamSpec:
    type: str
    min: float | None = None
    max: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    values: tuple[str, ...] = ()


@dataclass(frozen=True)
class CommandSpec:
    type: str
    title: str
    risk: str
    requires_evidence: bool
    params: dict[str, ParamSpec]


@dataclass(frozen=True)
class Contract:
    version: int
    envelope_required: tuple[str, ...]
    max_evidence: int
    commands: dict[str, CommandSpec]
    codes: dict[str, str]

    def spec(self, command_type: str) -> CommandSpec:
        if command_type not in self.commands:
            raise ContractError(f"неизвестный тип команды: {command_type}")
        return self.commands[command_type]

    def param_model(self, command_type: str) -> type[BaseModel]:
        return _param_model(self, command_type)


def _parse_param(raw: dict[str, Any]) -> ParamSpec:
    kind = raw.get("type")
    if kind == "float":
        return ParamSpec("float", min=raw.get("min"), max=raw.get("max"))
    if kind == "string":
        return ParamSpec(
            "string", min_length=raw.get("min_length"), max_length=raw.get("max_length")
        )
    if kind == "enum":
        return ParamSpec("enum", values=tuple(raw.get("values", ())))
    raise ContractError(f"неизвестный тип параметра: {kind}")


def load_contract(path: Path | str | None = None) -> Contract:
    path = Path(path) if path else CONTRACT_PATH
    raw = json.loads(path.read_text(encoding="utf-8"))
    commands = {
        name: CommandSpec(
            type=name,
            title=body.get("title", name),
            risk=body.get("risk", "A1"),
            requires_evidence=bool(body.get("requires_evidence", True)),
            params={
                param: _parse_param(spec) for param, spec in body.get("params", {}).items()
            },
        )
        for name, body in raw["commands"].items()
    }
    if not commands:
        raise ContractError("контракт не содержит команд")
    return Contract(
        version=int(raw.get("version", 1)),
        envelope_required=tuple(
            raw.get("envelope", {}).get(
                "required",
                ("command_id", "type", "target", "params", "requested_by", "correlation_id"),
            )
        ),
        max_evidence=int(raw.get("envelope", {}).get("max_evidence", 20)),
        commands=commands,
        codes=dict(raw.get("codes", {})),
    )


@lru_cache
def get_contract() -> Contract:
    return load_contract()


_MODEL_CACHE: dict[str, type[BaseModel]] = {}


def _param_model(contract: Contract, command_type: str) -> type[BaseModel]:
    cached = _MODEL_CACHE.get(command_type)
    if cached is not None:
        return cached
    spec = contract.spec(command_type)
    fields: dict[str, Any] = {}
    for name, param in spec.params.items():
        if param.type == "float":
            fields[name] = (float, Field(ge=param.min, le=param.max))
        elif param.type == "string":
            fields[name] = (str, Field(min_length=param.min_length, max_length=param.max_length))
        elif param.type == "enum":
            literal = Literal.__getitem__(param.values)  # type: ignore[attr-defined]
            fields[name] = (literal, ...)
        else:  # pragma: no cover - защищено в _parse_param
            raise ContractError(param.type)
    model = create_model(  # type: ignore[call-overload]
        f"{command_type.title().replace('_', '')}Params",
        __config__=ConfigDict(extra="forbid"),
        **fields,
    )
    _MODEL_CACHE[command_type] = model
    return model


def validate_envelope(contract: Contract, payload: dict[str, Any]) -> None:
    missing = [field for field in contract.envelope_required if field not in payload]
    if missing:
        raise ContractError(f"нет обязательных полей: {', '.join(missing)}")
    target = payload.get("target")
    if not isinstance(target, dict) or not target.get("line_id"):
        raise ContractError("target.line_id обязателен")
    if not isinstance(payload.get("params"), dict):
        raise ContractError("params должен быть объектом")
    evidence = payload.get("evidence") or []
    if not isinstance(evidence, list) or len(evidence) > contract.max_evidence:
        raise ContractError(f"evidence: список не длиннее {contract.max_evidence}")
