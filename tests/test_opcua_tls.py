"""Интеграция по OPC UA TLS: Basic256Sha256, сертификаты и ключ сервера."""
from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

import pytest
from factoria.opcua.client import OpcuaClient
from factoria.realtime.cache import GOOD, TagCache
from factoria.security.certs import generate_opcua_pair
from factoria.tags.registry import load_registry

ROOT = Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.integration

URL = "opc.tcp://127.0.0.1:48420"


def _load_emulator():
    spec = importlib.util.spec_from_file_location(
        "factoria_emulator_tls", ROOT / "opcua-emulator" / "emulator.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DummyHistory:
    def offer(self, *args) -> None:
        return None


def test_tls_connection(tmp_path: Path):
    emulator = _load_emulator()
    registry = load_registry()
    server_cert, server_key = generate_opcua_pair(
        tmp_path, "server", "urn:factoria:server", server=True
    )
    client_cert, client_key = generate_opcua_pair(
        tmp_path, "client", "urn:factoria:client", server=False
    )

    async def scenario() -> dict:
        emu = emulator.Emulator(
            URL,
            security="Basic256Sha256_SignAndEncrypt",
            cert=str(server_cert),
            key=str(server_key),
        )
        await emu.setup()
        cache = TagCache(registry)
        client = OpcuaClient(
            cache,
            DummyHistory(),
            endpoint=URL,
            namespace=registry.namespace,
            tags=tuple(t.id for t in registry.tags),
            interval_s=0.15,
            security="Basic256Sha256_SignAndEncrypt",
            client_cert=str(client_cert),
            client_key=str(client_key),
            server_cert=str(server_cert),
        )
        task = asyncio.create_task(client.run(), name="tls-client")
        try:
            async with emu.server:
                await asyncio.sleep(0.4)
                for line in emu.lines:
                    await emu.publish(line)
                deadline = asyncio.get_running_loop().time() + 8
                while asyncio.get_running_loop().time() < deadline:
                    if all(cache.effective_quality(tag.id) == GOOD for tag in registry.tags):
                        break
                    await asyncio.sleep(0.1)
                return {
                    "source": cache.source,
                    "good": sum(
                        1 for tag in registry.tags if cache.effective_quality(tag.id) == GOOD
                    ),
                    "total": len(registry.tags),
                }
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    result = asyncio.run(scenario())
    assert result["source"] == "connected", result
    assert result["good"] == result["total"], result
