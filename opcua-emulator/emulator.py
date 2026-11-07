"""Эмулятор ПЛК на OPC UA (этап 1 ТЗ).

3 линии L1..L3, 7 тегов на линию (21), 5 method-нод.
Запись возможна только через методы: все переменные создаются с writable=False
(ADR-105). Физика — в `factoria.simulator.line_physics`, здесь только транспорт.

Запуск:
    python opcua-emulator/emulator.py                # до Ctrl+C
    python opcua-emulator/emulator.py --seconds 10   # для проверок

Адрес: OPCUA_ENDPOINT. Порт 4840 на машине разработки занят OPC UA Local
Discovery Server (процесс opcualds), поэтому локально по умолчанию 48400.
В docker/prod используется 4840 (ТЗ §4.1).
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend" / "src"))

from asyncua import Server, ua  # noqa: E402

from factoria.simulator.line_physics import PlantError, build_lines  # noqa: E402
from factoria.tags.registry import load_registry  # noqa: E402

LOG = logging.getLogger("emulator")
ENDPOINT = os.environ.get("OPCUA_ENDPOINT", "opc.tcp://0.0.0.0:48400")
STEP_S = 0.5

VARIANT_TYPES = {
    "bool": ua.VariantType.Boolean,
    "float": ua.VariantType.Double,
    "uint16": ua.VariantType.UInt16,
    "string": ua.VariantType.String,
}

INITIAL = {
    "Running": False,
    "Speed.SP": 0.0,
    "Speed.PV": 0.0,
    "Temp.PV": 20.0,
    "Load.Pct": 0.0,
    "Alarm.Code": 0,
    "Recipe.ID": "R1",
}


def _status(code: str) -> ua.StatusCode:
    return ua.StatusCode(getattr(ua.StatusCodes, code))


def _unwrap(value):
    return value.Value if isinstance(value, ua.Variant) else value


class Emulator:
    def __init__(
        self,
        endpoint: str = ENDPOINT,
        *,
        security: str | None = None,
        cert: str | None = None,
        key: str | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.security = security
        self.cert = cert
        self.key = key
        self.registry = load_registry()
        self.lines = build_lines(self.registry)
        self.server = Server()
        self.nodes: dict[str, dict[str, object]] = {}
        self.namespace = 0

    # ---------- сборка адресного пространства ----------

    async def setup(self) -> None:
        await self.server.init()
        if self.security:
            await self.server.set_application_uri("urn:factoria:server")
        self.server.set_endpoint(self.endpoint)
        self.server.set_server_name("FACTORIA OPC UA emulator")
        if self.security:
            if not self.cert or not self.key:
                raise RuntimeError("OPCUA_SECURITY задан, но нет OPCUA_CERT/OPCUA_KEY")
            # ВАЖНО: load_certificate грузит только сертификат, ключ — отдельно.
            await self.server.load_certificate(self.cert)
            await self.server.load_private_key(self.key)
            self.server.set_security_policy([getattr(ua.SecurityPolicyType, self.security)])
        self.namespace = await self.server.register_namespace(self.registry.namespace)

        for line_id, state in self.lines.items():
            obj = await self.server.nodes.objects.add_object(
                ua.NodeId(line_id, self.namespace),
                ua.QualifiedName(line_id, self.namespace),
            )
            self.nodes[line_id] = {}

            for spec in self.registry.line_tags(line_id):
                # Строковый NodeId = полный id тега (L1.Speed.SP): адресация
                # "ns=2;s=L1.Speed.SP" стабильна и не зависит от порядка узлов.
                node = await obj.add_variable(
                    ua.NodeId(spec.id, self.namespace),
                    ua.QualifiedName(spec.name, self.namespace),
                    INITIAL[spec.name],
                    VARIANT_TYPES[spec.type],
                )
                await node.set_writable(False)  # ADR-105: только через методы
                self.nodes[line_id][spec.name] = node

            await self._add_methods(obj, state)

    async def _add_methods(self, obj, state) -> None:
        def mid(name: str) -> ua.NodeId:
            return ua.NodeId(f"{state.line_id}.{name}", self.namespace)

        await obj.add_method(
            mid("SetSpeed"), "SetSpeed", self._make_handler(state, "set_speed"),
            [ua.VariantType.Double], [ua.VariantType.StatusCode],
        )
        await obj.add_method(
            mid("SetRecipe"), "SetRecipe", self._make_handler(state, "set_recipe"),
            [ua.VariantType.String], [ua.VariantType.StatusCode],
        )
        await obj.add_method(
            mid("StartLine"), "StartLine", self._make_handler(state, "start"),
            [], [ua.VariantType.StatusCode],
        )
        await obj.add_method(
            mid("StopLine"), "StopLine", self._make_handler(state, "stop"),
            [], [ua.VariantType.StatusCode],
        )
        await obj.add_method(
            mid("ReallocateJob"), "ReallocateJob", self._make_handler(state, "reallocate_job"),
            [ua.VariantType.String], [ua.VariantType.StatusCode],
        )

    def _make_handler(self, state, method: str):
        async def handler(parent, *args):
            try:
                if method == "reallocate_job":
                    state.reallocate_job(str(_unwrap(args[0])))
                elif method == "set_recipe":
                    state.set_recipe(str(_unwrap(args[0])))
                elif method == "set_speed":
                    state.set_speed(float(_unwrap(args[0])))
                else:
                    getattr(state, method)()
            except PlantError as exc:
                LOG.info("%s %s -> %s", state.line_id, method, exc.code)
                await self.publish(state.line_id)
                return _status(exc.code)
            await self.publish(state.line_id)
            return _status("Good")

        return handler

    # ---------- публикация значений ----------

    async def publish(self, line_id: str) -> None:
        state = self.lines[line_id]
        now = datetime.now(timezone.utc)
        for name, value in state.snapshot().items():
            node = self.nodes[line_id][name]
            spec = self.registry.tag(f"{line_id}.{name}")
            variant = ua.Variant(value, VARIANT_TYPES[spec.type])
            await node.write_value(
                ua.DataValue(variant, SourceTimestamp=now, ServerTimestamp=now)
            )

    async def simulate(self, seconds: float | None = None) -> None:
        elapsed = 0.0
        while seconds is None or elapsed < seconds:
            await asyncio.sleep(STEP_S)
            elapsed += STEP_S
            for line_id, state in self.lines.items():
                state.step(STEP_S)
                await self.publish(line_id)

    async def run(self, seconds: float | None = None) -> None:
        await self.setup()
        async with self.server:
            await asyncio.sleep(0.3)  # дать серверу подняться
            for line_id in self.lines:
                await self.publish(line_id)
            LOG.info("эмулятор слушает %s, тегов: %d", self.endpoint, len(self.registry.tags))
            await self.simulate(seconds)


def main() -> int:
    parser = argparse.ArgumentParser(description="FACTORIA OPC UA emulator")
    parser.add_argument("--seconds", type=float, default=None, help="остановиться через N секунд")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    security = os.environ.get("OPCUA_SECURITY", "None")
    security = None if security in {"", "None", "none"} else security
    emulator = Emulator(
        security=security,
        cert=os.environ.get("OPCUA_CERT"),
        key=os.environ.get("OPCUA_KEY"),
    )
    try:
        asyncio.run(emulator.run(args.seconds))
    except KeyboardInterrupt:
        LOG.info("остановлен пользователем")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
