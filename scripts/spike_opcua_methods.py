"""Спайк этапа 0: доказывает, что паттерн ТЗ §4.3 исполним на asyncua 2.1.0 / Python 3.14.

Проверяет три утверждения:
  1) переменная с writable=False недоступна клиенту на запись;
  2) method-нода пишет в неё на стороне сервера;
  3) method возвращает BadInvalidState по interlock (Temp > 80 и value > 400).

Побочные находки, заложенные в код (иначе спайк падал):
  * get_child("2:Name") трактует часть пути как строковый NodeId (ns=2;s=Name)
    и даёт BadNoMatch, потому что add_variable создаёт числовые NodeId —
    узел ищется по BrowseName;
  * callback метода получает ua.Variant, а не float — нужен .Value.

Запуск: python scripts/spike_opcua_methods.py
Порт 48403, время работы ~2 с. В репозиторий ничего не пишет.
"""
from __future__ import annotations

import asyncio
import sys

from asyncua import Client, Server, ua

PORT = 48403
URL = f"opc.tcp://127.0.0.1:{PORT}"


def code_name(exc: ua.UaStatusCodeError) -> str:
    try:
        return ua.StatusCodes.get_name(exc.code)
    except Exception:  # noqa: BLE001 - диагностика важнее строгости
        return hex(exc.code)


async def child_by_name(node, name: str):
    for child in await node.get_children():
        if (await child.read_browse_name()).Name == name:
            return child
    raise LookupError(f"child {name!r} not found")


def unwrap(value):
    return value.Value if isinstance(value, ua.Variant) else value


async def main() -> int:
    srv = Server()
    await srv.init()
    srv.set_endpoint(URL)
    idx = await srv.register_namespace("urn:mfg:emulator")

    line = await srv.nodes.objects.add_object(idx, "L1")
    speed = await line.add_variable(idx, "Speed.SP", 0.0)
    temp = await line.add_variable(idx, "Temp.PV", 20.0)
    await speed.set_writable(False)
    await temp.set_writable(False)

    async def set_speed(parent, value):
        value = float(unwrap(value))
        if float(unwrap(await temp.read_value())) > 80.0 and value > 400.0:
            return ua.StatusCode(ua.StatusCodes.BadInvalidState)
        await speed.write_value(value)
        return ua.StatusCode(ua.StatusCodes.Good)

    await line.add_method(
        idx, "SetSpeed", set_speed, [ua.VariantType.Double], [ua.VariantType.StatusCode]
    )

    result: dict[str, object] = {}
    async with srv, Client(URL) as client:
        l1 = await client.nodes.root.get_child(["0:Objects", f"{idx}:L1"])
        sp = await child_by_name(l1, "Speed.SP")
        tp = await child_by_name(l1, "Temp.PV")
        setter = await child_by_name(l1, "SetSpeed")

        try:
            await sp.write_value(500.0)
            result["direct_write_blocked"] = False
        except ua.UaStatusCodeError as exc:
            result["direct_write_blocked"] = True
            result["direct_write_error"] = code_name(exc)

        await l1.call_method(setter.nodeid, 500.0)
        result["method_write_ok"] = abs(float(await sp.read_value()) - 500.0) < 1e-6

        await temp.write_value(90.0)
        try:
            await l1.call_method(setter.nodeid, 600.0)
            result["interlock_blocks"] = False
        except ua.UaStatusCodeError as exc:
            result["interlock_blocks"] = True
            result["interlock_error"] = code_name(exc)
        result["value_after_interlock"] = float(await sp.read_value())

    for key, value in result.items():
        print(f"{key} = {value}")
    ok = all(
        result.get(k) for k in ("direct_write_blocked", "method_write_ok", "interlock_blocks")
    )
    print("SPIKE_RESULT =", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
