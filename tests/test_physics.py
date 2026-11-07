from __future__ import annotations

import pytest
from factoria.simulator.line_physics import (
    AMBIENT,
    BadInvalidState,
    BadOutOfRange,
    LineState,
)


def make_line(**kw) -> LineState:
    return LineState(line_id="L1", **kw)


def ramp(line: LineState, target: float, step: float = 700.0) -> None:
    """Поднимает уставку ступенями: |delta| > 800 запрещён interlock-ом §6.5."""
    while abs(line.sp - target) > 1e-9:
        line.set_speed(min(target, line.sp + step))


def test_initial_state():
    line = make_line()
    assert line.running is False
    assert line.temp == AMBIENT
    assert line.sp == 0.0
    assert line.alarm == 0


def test_speed_follows_setpoint_with_tau_2s():
    line = make_line()
    line.start()
    line.set_speed(600)
    line.advance(2.0)  # одна постоянная времени -> ~63%
    assert 340 < line.pv < 420
    line.advance(10.0)
    assert abs(line.pv - 600) < 5


def test_temperature_rises_with_speed_and_reaches_interlock():
    line = make_line()
    line.start()
    ramp(line, 1200)
    line.advance(40.0)
    assert line.temp > 80, line.temp
    assert line.temp <= 120


def test_set_speed_ok_below_threshold_at_any_temp():
    line = make_line()
    line.temp = 100.0
    line.set_speed(300)  # <= speed_threshold, перегрев не мешает
    assert line.sp == 300


def test_interlock_rejects_high_speed_when_hot():
    line = make_line()
    line.temp = 85.0
    with pytest.raises(BadInvalidState):
        line.set_speed(500)
    assert line.alarm == 101
    assert line.sp == 0.0


def test_delta_interlock_uses_absolute_delta():
    line = make_line()
    line.set_speed(0)
    with pytest.raises(BadInvalidState):
        line.set_speed(900)  # |900 - 0| > 800
    with pytest.raises(BadInvalidState):
        line.set_speed(850)
    line.set_speed(799)  # ровно под порогом — разрешено
    assert line.sp == 799


def test_speed_out_of_range():
    line = make_line()
    with pytest.raises(BadOutOfRange):
        line.set_speed(1201)
    with pytest.raises(BadOutOfRange):
        line.set_speed(-1)


def test_recipe_validation():
    line = make_line()
    line.set_recipe("R4")
    assert line.recipe == "R4"
    with pytest.raises(BadOutOfRange):
        line.set_recipe("R9")


def test_overload_autostop_after_60s():
    line = make_line()
    line.overload = True
    line.recipe = "R5"
    line.start()
    ramp(line, 1200)
    line.advance(30.0)
    assert line.load > 95
    line.advance(20.0)
    assert line.alarm == 0, "до 60 c автостопа быть не должно"
    line.advance(20.0)
    assert line.alarm == 102
    assert line.running is False
    assert line.sp == 0.0


def test_start_blocked_by_alarm():
    line = make_line()
    line.alarm = 102
    with pytest.raises(BadInvalidState):
        line.start()


def test_stop_resets_setpoint():
    line = make_line()
    line.start()
    line.set_speed(400)
    line.stop()
    assert line.running is False
    assert line.sp == 0.0


def test_reallocate_blocked_on_overload():
    line = make_line()
    line.load = 96.0
    with pytest.raises(BadInvalidState):
        line.reallocate_job("job-1")
    line.load = 50.0
    line.reallocate_job("job-1")
    assert line.jobs["job-1"] == "L1"
