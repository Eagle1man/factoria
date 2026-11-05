"""Загрузка и валидация реестра тегов (ADR-104: единственный источник правды)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REGISTRY_PATH = Path(__file__).with_name("registry.yaml")


class RegistryError(ValueError):
    """Реестр невалиден — сервис не должен стартовать."""


@dataclass(frozen=True)
class TagSpec:
    id: str
    line: str
    name: str
    type: str
    unit: str | None
    min: float | None
    max: float | None
    writable: bool
    max_age_seconds: float
    deadband: float
    enum: tuple[str, ...] = ()
    command: tuple[str, ...] = ()

    @property
    def node_name(self) -> str:
        return self.name


@dataclass(frozen=True)
class MethodSpec:
    name: str
    args: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class Registry:
    namespace: str
    thresholds: dict[str, float]
    lines: tuple[str, ...]
    recipes: tuple[str, ...]
    tags: tuple[TagSpec, ...]
    methods: tuple[MethodSpec, ...]

    def tag(self, tag_id: str) -> TagSpec:
        for t in self.tags:
            if t.id == tag_id:
                return t
        raise KeyError(tag_id)

    def line_tags(self, line: str) -> tuple[TagSpec, ...]:
        return tuple(t for t in self.tags if t.line == line)


def load_registry(path: Path | str | None = None) -> Registry:
    path = Path(path) if path else REGISTRY_PATH
    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    reg = _build(raw)
    validate(reg)
    return reg


def _build(raw: dict[str, Any]) -> Registry:
    defaults = raw.get("defaults", {})
    lines = tuple(raw["lines"])
    recipes = tuple(raw["recipes"])
    max_age = float(defaults.get("max_age_seconds", 3))
    deadband = float(defaults.get("deadband", 0.5))

    tags: list[TagSpec] = []
    for line in lines:
        for tpl in raw["tags"]:
            name = tpl["name"]
            tags.append(
                TagSpec(
                    id=f"{line}.{name}",
                    line=line,
                    name=name,
                    type=tpl["type"],
                    unit=tpl.get("unit"),
                    min=None if tpl.get("min") is None else float(tpl["min"]),
                    max=None if tpl.get("max") is None else float(tpl["max"]),
                    writable=bool(tpl.get("writable", False)),
                    max_age_seconds=float(tpl.get("max_age_seconds", max_age)),
                    deadband=float(tpl.get("deadband", deadband)),
                    enum=tuple(tpl.get("enum", ())),
                    command=tuple(tpl.get("command", ())),
                )
            )

    methods = tuple(
        MethodSpec(
            name=m["name"],
            args=tuple((a["name"], a["type"]) for a in m.get("args", [])),
        )
        for m in raw["methods"]
    )
    return Registry(
        namespace=raw["namespace"],
        thresholds={k: float(v) for k, v in raw["thresholds"].items()},
        lines=lines,
        recipes=recipes,
        tags=tuple(tags),
        methods=methods,
    )


def validate(reg: Registry) -> None:
    expected = len(reg.lines) * 7
    if len(reg.tags) != expected:
        raise RegistryError(f"ожидалось {expected} тегов, получено {len(reg.tags)}")

    ids = [t.id for t in reg.tags]
    if len(set(ids)) != len(ids):
        raise RegistryError("дубликаты id тегов")

    for t in reg.tags:
        if t.writable:
            raise RegistryError(f"{t.id}: writable=true запрещён (ADR-105)")
        if t.min is not None and t.max is not None and t.min >= t.max:
            raise RegistryError(f"{t.id}: min >= max")
        if t.type == "string" and not t.enum:
            raise RegistryError(f"{t.id}: строковый тег без enum")
        if t.max_age_seconds <= 0:
            raise RegistryError(f"{t.id}: max_age_seconds <= 0")

    recipe_tag = next((t for t in reg.tags if t.name == "Recipe.ID"), None)
    if recipe_tag is None or set(recipe_tag.enum) != set(reg.recipes):
        raise RegistryError("Recipe.ID enum не совпадает с recipes")

    required = {"speed_threshold", "speed_max", "speed_delta_interlock",
                "temp_alarm", "load_alarm", "load_alarm_hold_s"}
    missing = required - set(reg.thresholds)
    if missing:
        raise RegistryError(f"нет порогов: {sorted(missing)}")

    if len({m.name for m in reg.methods}) != 5:
        raise RegistryError("ожидалось ровно 5 методов")
