"""Исполнение команды через реальный OPC UA (эмулятор в процессе)."""
from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

import pytest

from factoria.opcua.commands import dispatch_command
from factoria.tags.registry import load_registry

ROOT = Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.integration

URL = "opc.tcp://127.0.0.1:48416"


def _load_emulator():
    spec = importlib.util.spec_from_file_location(
        "factoria_emulator_s4", ROOT / "opcua-emulator" / "emulator.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dispatch_reaches_method_nodes():
    emulator = _load_emulator()
    registry = load_registry()

    async def scenario():
        emu = emulator.Emulator(URL)
        await emu.setup()
        async with emu.server:
            await asyncio.sleep(0.3)
            started = await dispatch_command(
                endpoint=URL,
                namespace=registry.namespace,
                line_id="L1",
                command_type="line_start",
                params={},
            )
            speed = await dispatch_command(
                endpoint=URL,
                namespace=registry.namespace,
                line_id="L1",
                command_type="set_setpoint",
                params={"setpoint_value": 300.0},
            )
            recipe = await dispatch_command(
                endpoint=URL,
                namespace=registry.namespace,
                line_id="L1",
                command_type="switch_recipe",
                params={"recipe_id": "R4"},
            )
            bad = await dispatch_command(
                endpoint=URL,
                namespace=registry.namespace,
                line_id="L1",
                command_type="switch_recipe",
                params={"recipe_id": "R9"},
            )
            return started, speed, recipe, bad, emu.lines["L1"].sp, emu.lines["L1"].recipe

    started, speed, recipe, bad, sp, recipe_id = asyncio.run(scenario())

    assert started == (True, "EXECUTED")
    assert speed == (True, "EXECUTED")
    assert recipe == (True, "EXECUTED")
    assert sp == 300.0
    assert recipe_id == "R4"
    assert bad[0] is False
    assert "BadOutOfRange" in bad[1]
