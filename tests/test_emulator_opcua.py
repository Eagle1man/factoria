from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

import pytest
from asyncua import Client, ua

ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.integration

URL = "opc.tcp://127.0.0.1:48413"


def _load_emulator():
    spec = importlib.util.spec_from_file_location(
        "factoria_emulator", ROOT / "opcua-emulator" / "emulator.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_CODES = {
    value: name
    for name in dir(ua.StatusCodes)
    if not name.startswith("_")
    for value in (getattr(ua.StatusCodes, name),)
    if isinstance(value, int)
}


def code_name(code: int) -> str:
    return _CODES.get(code, hex(code))


async def call(owner, method_node, *args) -> str:
    """Возвращает 'Good' или имя кода отказа (эмулятор отдаёт StatusCode)."""
    try:
        await owner.call_method(method_node.nodeid, *args)
        return "Good"
    except ua.UaStatusCodeError as exc:
        return code_name(exc.code)


async def _client_checks(emu) -> dict:
    out: dict = {}
    ns = emu.namespace
    async with Client(URL) as client:
        l1 = client.get_node(f"ns={ns};s=L1")
        variables, methods = [], []
        for child in await l1.get_children():
            klass = await child.read_node_class()
            if klass == ua.NodeClass.Variable:
                variables.append(child)
            elif klass == ua.NodeClass.Method:
                methods.append(child)
        out["variables"] = len(variables)
        out["methods"] = len(methods)

        blocked = 0
        for node in variables:
            try:
                await node.write_value(123)
            except ua.UaStatusCodeError:
                blocked += 1
        out["blocked"] = blocked

        sp = client.get_node(f"ns={ns};s=L1.Speed.SP")
        setter = client.get_node(f"ns={ns};s=L1.SetSpeed")
        recipe = client.get_node(f"ns={ns};s=L1.SetRecipe")
        alarm = client.get_node(f"ns={ns};s=L1.Alarm.Code")

        out["initial_sp"] = float(await sp.read_value())

        out["set_speed_code"] = await call(l1, setter, 500.0)
        out["sp_after"] = float(await sp.read_value())

        out["bad_recipe_code"] = await call(l1, recipe, "R9")
        out["good_recipe_code"] = await call(l1, recipe, "R4")

        emu.lines["L1"].temp = 90.0
        out["hot_speed_code"] = await call(l1, setter, 900.0)
        out["alarm"] = int(await alarm.read_value())
        out["sp_after_refusal"] = float(await sp.read_value())
    return out


def test_emulator_contract():
    emulator = _load_emulator()

    async def scenario():
        emu = emulator.Emulator(URL)
        await emu.setup()
        async with emu.server:
            await asyncio.sleep(0.4)
            for line in emu.lines:
                await emu.publish(line)
            return await _client_checks(emu)

    result = asyncio.run(scenario())

    assert result["variables"] == 7, result
    assert result["methods"] == 5, result
    assert result["blocked"] == 7, "все переменные линии должны отвергать прямую запись"
    assert result["initial_sp"] == 0.0
    assert result["set_speed_code"] == "Good"
    assert result["sp_after"] == 500.0
    assert result["bad_recipe_code"] == "BadOutOfRange"
    assert result["good_recipe_code"] == "Good"
    assert result["hot_speed_code"] == "BadInvalidState"
    assert result["alarm"] == 101
    assert result["sp_after_refusal"] == 500.0, "отказ не должен менять уставку"
