"""Исполнение команды: вызов method-ноды на OPC UA (ТЗ §5.1 DISPATCHING → EXECUTED)."""
from __future__ import annotations

import logging
from typing import Any

from asyncua import Client, ua

LOG = logging.getLogger("dispatch")

METHODS: dict[str, tuple[str, str]] = {
    # команда -> (метод, аргумент)
    "set_setpoint": ("SetSpeed", "setpoint_value"),
    "switch_recipe": ("SetRecipe", "recipe_id"),
    "line_start": ("StartLine", ""),
    "line_stop": ("StopLine", ""),
    "reallocate_job": ("ReallocateJob", "job_id"),
}


def _code_name(exc: ua.UaStatusCodeError) -> str:
    codes = {
        value: name
        for name in dir(ua.StatusCodes)
        if not name.startswith("_")
        for value in (getattr(ua.StatusCodes, name),)
        if isinstance(value, int)
    }
    return codes.get(exc.code, hex(exc.code))


async def dispatch_command(
    *,
    endpoint: str,
    namespace: str,
    line_id: str,
    command_type: str,
    params: dict[str, Any],
) -> tuple[bool, str]:
    """Вызывает метод линии. Возвращает (успех, код или пояснение)."""
    if command_type not in METHODS:
        return False, "UNKNOWN_METHOD"
    method_name, arg_name = METHODS[command_type]
    args: list[Any] = []
    if arg_name:
        if arg_name not in params:
            return False, f"нет параметра {arg_name}"
        args.append(params[arg_name])

    try:
        async with Client(endpoint) as client:
            index = await client.get_namespace_index(namespace)
            line = client.get_node(f"ns={index};s={line_id}")
            method = client.get_node(f"ns={index};s={line_id}.{method_name}")
            await line.call_method(method.nodeid, *args)
        return True, "EXECUTED"
    except ua.UaStatusCodeError as exc:
        name = _code_name(exc)
        LOG.warning("%s %s отклонён: %s", line_id, command_type, name)
        return False, name
    except Exception as exc:  # noqa: BLE001 - сеть, таймаут, неизвестная ошибка
        LOG.warning("%s %s не исполнен: %s", line_id, command_type, exc)
        return False, f"TRANSPORT: {exc}"
