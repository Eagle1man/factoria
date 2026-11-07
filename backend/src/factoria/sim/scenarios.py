"""Детерминированные сценарии симуляции (этап «Эксперименты»).

Сценарий — это подготовка линии и расписание управляющих воздействий.
Случайность допустима только через `random.Random(seed)`, чтобы один seed
давал один результат.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

from factoria.simulator.line_physics import LineState, PlantError

Event = dict[str, object]


@dataclass(frozen=True)
class Scenario:
    name: str
    title: str
    description: str
    noise: float
    prepare: Callable[[LineState, random.Random], None]
    control: Callable[[float, float, LineState, list[Event]], None]


def _safe(line: LineState, events: list[Event], action: str, t: float, fn, *args) -> None:
    try:
        fn(*args)
    except PlantError as exc:
        events.append({"t": round(t, 2), "kind": "refused", "action": action, "detail": exc.code})


def _nominal_prepare(line: LineState, rng: random.Random) -> None:
    line.start()


def _nominal_control(t: float, horizon: float, line: LineState, events: list[Event]) -> None:
    if t == 0:
        _safe(line, events, "set_speed", t, line.set_speed, 700.0)
    if abs(t - horizon / 2) < 1e-9:
        _safe(line, events, "set_speed", t, line.set_speed, 800.0)


def _overload_prepare(line: LineState, rng: random.Random) -> None:
    line.recipe = "R5"
    line.overload = True
    line.start()


def _overload_control(t: float, horizon: float, line: LineState, events: list[Event]) -> None:
    if t == 0:
        _safe(line, events, "set_speed", t, line.set_speed, 700.0)
    if abs(t - 1.0) < 1e-9:
        _safe(line, events, "set_speed", t, line.set_speed, 900.0)


def _recipe_prepare(line: LineState, rng: random.Random) -> None:
    line.start()


def _recipe_control(t: float, horizon: float, line: LineState, events: list[Event]) -> None:
    if t == 0:
        _safe(line, events, "set_speed", t, line.set_speed, 600.0)
    if abs(t - horizon / 2) < 1e-9:
        _safe(line, events, "set_recipe", t, line.set_recipe, "R4")


def _hot_prepare(line: LineState, rng: random.Random) -> None:
    line.temp = 85.0
    line.start()


def _hot_control(t: float, horizon: float, line: LineState, events: list[Event]) -> None:
    if t == 0:
        _safe(line, events, "set_speed", t, line.set_speed, 900.0)
    if abs(t - 2.0) < 1e-9:
        _safe(line, events, "set_speed", t, line.set_speed, 300.0)


SCENARIOS: dict[str, Scenario] = {
    "nominal": Scenario(
        name="nominal",
        title="Номинальный режим",
        description="Пуск, разгон до 700 rpm, через половину горизонта — 800 rpm.",
        noise=0.0,
        prepare=_nominal_prepare,
        control=_nominal_control,
    ),
    "overload": Scenario(
        name="overload",
        title="Перегруз линии",
        description="Рецепт R5 и перегруз: загрузка выше 95 % дольше 60 c, автостоп 102.",
        noise=0.0,
        prepare=_overload_prepare,
        control=_overload_control,
    ),
    "recipe_change": Scenario(
        name="recipe_change",
        title="Смена рецепта",
        description="Работа на R1, на половине горизонта — переход на R4.",
        noise=0.0,
        prepare=_recipe_prepare,
        control=_recipe_control,
    ),
    "hot_start": Scenario(
        name="hot_start",
        title="Горячий старт",
        description="Температура 85 °C: уставка 900 отклоняется, 300 — разрешается.",
        noise=0.0,
        prepare=_hot_prepare,
        control=_hot_control,
    ),
    "noisy": Scenario(
        name="noisy",
        title="Номинал с возмущениями",
        description="То же, что номинал, но загрузка колеблется по seed — проверка воспроизводимости.",
        noise=4.0,
        prepare=_nominal_prepare,
        control=_nominal_control,
    ),
}
