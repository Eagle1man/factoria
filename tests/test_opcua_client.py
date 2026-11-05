from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

import pytest

from factoria.opcua.client import OpcuaClient
from factoria.realtime.cache import GOOD, TagCache
from factoria.tags.registry import load_registry

ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.integration

URL = "opc.tcp://127.0.0.1:48415"


def _load_emulator():
    spec = importlib.util.spec_from_file_location(
        "factoria_emulator_s2", ROOT / "opcua-emulator" / "emulator.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DummyHistory:
    def __init__(self) -> None:
        self.items: list[tuple] = []

    def offer(self, tag, value, quality, ts) -> None:
        self.items.append((tag, value, quality, ts))


async def _wait_until(predicate, timeout: float) -> bool:
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        if predicate():
            return True
        await asyncio.sleep(0.05)
    return False


def test_client_reads_all_tags_and_goes_bad_on_disconnect():
    emulator = _load_emulator()
    registry = load_registry()
    cache = TagCache(registry)
    history = DummyHistory()

    async def scenario() -> dict:
        emu = emulator.Emulator(URL)
        await emu.setup()
        await emu.publish("L1")

        client = OpcuaClient(
            cache,
            history,
            endpoint=URL,
            namespace=registry.namespace,
            tags=tuple(t.id for t in registry.tags),
            interval_s=0.15,
        )
        task = asyncio.create_task(client.run(), name="opcua-client")
        result: dict = {}
        try:
            async with emu.server:
                await asyncio.sleep(0.3)
                for line in emu.lines:
                    await emu.publish(line)
                ok = await _wait_until(
                    lambda: all(cache.effective_quality(t.id) == GOOD for t in registry.tags),
                    timeout=5,
                )
                result["all_good"] = ok
                result["source_connected"] = cache.source
                snapshot = cache.snapshot()
                result["l1_speed"] = snapshot["values"]["L1.Speed.PV"]["v"]
                result["l1_recipe"] = snapshot["values"]["L1.Recipe.ID"]["v"]
                result["history_items"] = len(history.items)
                loop = asyncio.get_running_loop()
                result["shutdown_started"] = loop.time()
            # сервер выключен: клиент обязан пометить данные BAD не позже 3 c (DoD §5.7)
            loop = asyncio.get_running_loop()
            down = await _wait_until(lambda: cache.source == "down", timeout=6)
            result["down_seconds"] = round(loop.time() - result["shutdown_started"], 2)
            result["went_down"] = down
            result["quality_after_down"] = cache.effective_quality("L1.Speed.PV")
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        return result

    result = asyncio.run(scenario())
    print("opcua-client:", result)

    assert result["all_good"] is True, result
    assert result["source_connected"] == "connected"
    assert result["l1_speed"] == 0.0
    assert result["l1_recipe"] == "R1"
    assert result["history_items"] >= 21
    assert result["went_down"] is True, result
    assert result["down_seconds"] <= 3.0, result
    assert result["quality_after_down"] == "BAD"
