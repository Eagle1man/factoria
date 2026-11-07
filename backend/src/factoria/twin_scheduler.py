"""Фоновые снимки двойника по расписанию (ADR-119).

Интервал задаётся `TWIN_SNAPSHOT_MINUTES`; 0 выключает задачу.
Снимок — это факт на момент времени, поэтому сбой одного снимка не валит
backend: ошибка пишется в лог, следующая попытка — через интервал.
"""
from __future__ import annotations

import asyncio
import logging

from factoria.model.history import save_snapshot
from factoria.model.semantic import build_semantic
from factoria.model.twin import build_twin
from factoria.storage.db import session_factory

LOG = logging.getLogger("twin-snapshots")


class NoDataYet(RuntimeError):
    """Кэш ещё не получил ни одного значения: снимок был бы ложным нулём."""


async def take_snapshot(registry, cache, ones) -> dict:
    values = cache.snapshot()["values"]
    if not any(item.get("v") is not None for item in values.values()):
        raise NoDataYet("кэш пуст: OPC UA ещё не отдал значения")
    orders = ones.list_open_orders()
    model = build_semantic(registry, orders)
    twin = build_twin(registry, cache, model)
    async with session_factory() as session:
        return await save_snapshot(session, twin)


async def snapshot_loop(registry, cache, ones, interval_s: int) -> None:
    # Дать опросу OPC UA забрать первые значения, иначе первый снимок — 0%.
    await asyncio.sleep(min(interval_s, 10))
    while True:
        try:
            saved = await take_snapshot(registry, cache, ones)
            LOG.info(
                "снимок двойника %s: покрытие %.1f%%, сигналов %s/%s",
                saved["version"],
                saved["coverage_pct"],
                saved["tags_good"],
                saved["tags_total"],
            )
        except asyncio.CancelledError:
            raise
        except NoDataYet as exc:
            LOG.info("снимок пропущен: %s", exc)
        except Exception as exc:  # noqa: BLE001 - снимок не должен ронять backend
            LOG.warning("снимок двойника не удался: %s", exc)
        await asyncio.sleep(interval_s)
