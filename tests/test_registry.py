from __future__ import annotations

import pytest

from factoria.tags import registry as reg_mod
from factoria.tags.registry import RegistryError, load_registry


def test_registry_has_21_tags_and_5_methods():
    reg = load_registry()
    assert len(reg.tags) == 21
    assert len(reg.lines) == 3
    assert len(reg.methods) == 5
    assert {m.name for m in reg.methods} == {
        "SetSpeed", "SetRecipe", "StartLine", "StopLine", "ReallocateJob"
    }


def test_every_tag_is_read_only():
    reg = load_registry()
    assert all(t.writable is False for t in reg.tags)


def test_line_has_seven_tags():
    reg = load_registry()
    names = {t.name for t in reg.line_tags("L1")}
    assert names == {
        "Running", "Speed.SP", "Speed.PV", "Temp.PV", "Load.Pct", "Alarm.Code", "Recipe.ID"
    }


def test_recipe_enum_matches_recipes():
    reg = load_registry()
    assert reg.tag("L2.Recipe.ID").enum == reg.recipes


def test_thresholds_present():
    reg = load_registry()
    th = reg.thresholds
    assert th["speed_threshold"] == 400
    assert th["speed_delta_interlock"] == 800
    assert th["temp_alarm"] == 80
    assert th["load_alarm"] == 95
    assert th["load_alarm_hold_s"] == 60


def test_writable_true_is_rejected():
    import yaml

    raw = yaml.safe_load(reg_mod.REGISTRY_PATH.read_text(encoding="utf-8"))
    raw["tags"][0]["writable"] = True
    built = reg_mod._build(raw)
    with pytest.raises(RegistryError):
        reg_mod.validate(built)


def test_wrong_tag_count_is_rejected():
    import yaml

    raw = yaml.safe_load(reg_mod.REGISTRY_PATH.read_text(encoding="utf-8"))
    raw["tags"] = raw["tags"][:-1]
    built = reg_mod._build(raw)
    with pytest.raises(RegistryError):
        reg_mod.validate(built)
