"""Детерминированная физика линии (этап 1).

Никаких случайных чисел: одинаковые входы дают одинаковое состояние.
Модуль не знает про OPC UA — его тестируют напрямую, эмулятор лишь
публикует значения и транслирует отказы в StatusCode.

Пороги берутся из registry.yaml; значения по умолчанию совпадают с ТЗ §4.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

AMBIENT = 20.0          # degC, нижняя граница Temp.PV
TEMP_MAX = 120.0        # degC, верхняя граница Temp.PV
TAU_SPEED = 2.0         # c, инерция Speed.PV (ТЗ §4.2)
TAU_TEMP = 30.0         # c, инерция температуры
DEFAULT_MAX = 1200.0

RECIPE_LOAD = {"R1": 30.0, "R2": 45.0, "R3": 55.0, "R4": 65.0, "R5": 75.0}


class PlantError(Exception):
    """Отказ уровня оборудования; code соответствует OPC UA."""

    code = "BadUnexpectedError"

    def __init__(self, message: str = "") -> None:
        super().__init__(message or self.code)


class BadOutOfRange(PlantError):
    code = "BadOutOfRange"


class BadInvalidState(PlantError):
    code = "BadInvalidState"


class BadNotRunning(BadInvalidState):
    code = "BadInvalidState"


@dataclass
class LineState:
    line_id: str
    speed_threshold: float = 400.0
    speed_max: float = DEFAULT_MAX
    speed_delta_interlock: float = 800.0
    temp_alarm: float = 80.0
    load_alarm: float = 95.0
    load_alarm_hold_s: float = 60.0
    recipes: tuple[str, ...] = ("R1", "R2", "R3", "R4", "R5")

    running: bool = False
    sp: float = 0.0
    pv: float = 0.0
    temp: float = AMBIENT
    load: float = 0.0
    alarm: int = 0
    recipe: str = "R1"
    overload: bool = False
    jobs: dict[str, str] = field(default_factory=dict)

    _overload_timer: float = 0.0
    _last_refusal: str = ""

    # ---------- команды (то, что доступно через method-ноды) ----------

    def set_speed(self, value: float) -> None:
        value = float(value)
        if math.isnan(value) or value < 0 or value > self.speed_max:
            raise BadOutOfRange(f"value={value} вне 0..{self.speed_max}")

        if self.temp > self.temp_alarm and value > self.speed_threshold:
            self.alarm = 101
            self._last_refusal = "temp"
            raise BadInvalidState(
                f"перегрев: Temp={self.temp:.1f} > {self.temp_alarm}, запрос {value}"
            )

        if abs(value - self.sp) > self.speed_delta_interlock:
            self._last_refusal = "delta"
            raise BadInvalidState(
                f"скачок уставки: |{value} - {self.sp}| > {self.speed_delta_interlock}"
            )

        self.sp = value
        if self.alarm == 101:
            self.alarm = 0

    def set_recipe(self, recipe: str) -> None:
        if recipe not in self.recipes:
            raise BadOutOfRange(f"recipe={recipe!r} не из {self.recipes}")
        self.recipe = recipe

    def start(self) -> None:
        if self.alarm:
            raise BadInvalidState(f"пуск запрещён, Alarm.Code={self.alarm}")
        self.running = True

    def stop(self) -> None:
        self.running = False
        self.sp = 0.0

    def reallocate_job(self, job_id: str) -> None:
        if not job_id:
            raise BadOutOfRange("job_id пуст")
        if self.load > self.load_alarm:
            raise BadInvalidState(
                f"перегруз: Load={self.load:.1f} > {self.load_alarm}, перераспределение запрещено"
            )
        self.jobs[job_id] = self.line_id

    # ---------- физика ----------

    def step(self, dt: float) -> None:
        if dt <= 0:
            return

        target_speed = self.sp if self.running else 0.0
        self.pv += (target_speed - self.pv) * (1.0 - math.exp(-dt / TAU_SPEED))
        self.pv = min(max(self.pv, 0.0), self.speed_max)

        temp_eq = AMBIENT + (TEMP_MAX - AMBIENT) * (self.pv / self.speed_max) ** 2
        self.temp += (temp_eq - self.temp) * (1.0 - math.exp(-dt / TAU_TEMP))
        self.temp = min(max(self.temp, AMBIENT), TEMP_MAX)

        if self.running:
            base = RECIPE_LOAD.get(self.recipe, 50.0)
            load = base + 40.0 * (self.pv / self.speed_max)
            if self.overload:
                load += 25.0
            self.load = min(max(load, 0.0), 100.0)
        else:
            self.load = max(0.0, self.load - 20.0 * dt)

        if self.load > self.load_alarm:
            self._overload_timer += dt
            if self._overload_timer >= self.load_alarm_hold_s:
                self.alarm = 102
                self.running = False
                self.sp = 0.0
        else:
            self._overload_timer = 0.0

    def advance(self, seconds: float, dt: float = 0.5) -> None:
        steps = int(round(seconds / dt))
        for _ in range(steps):
            self.step(dt)

    # ---------- публикация ----------

    def snapshot(self) -> dict[str, float | int | str | bool]:
        return {
            "Running": self.running,
            "Speed.SP": round(self.sp, 3),
            "Speed.PV": round(self.pv, 3),
            "Temp.PV": round(self.temp, 3),
            "Load.Pct": round(self.load, 3),
            "Alarm.Code": int(self.alarm),
            "Recipe.ID": self.recipe,
        }


def build_lines(registry) -> dict[str, LineState]:
    th = registry.thresholds
    return {
        line: LineState(
            line_id=line,
            speed_threshold=th["speed_threshold"],
            speed_max=th["speed_max"],
            speed_delta_interlock=th["speed_delta_interlock"],
            temp_alarm=th["temp_alarm"],
            load_alarm=th["load_alarm"],
            load_alarm_hold_s=th["load_alarm_hold_s"],
            recipes=registry.recipes,
        )
        for line in registry.lines
    }
