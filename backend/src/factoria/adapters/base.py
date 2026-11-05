"""Адаптер 1С (v1 — только чтение, ТЗ §9.1)."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Protocol


@dataclass(frozen=True)
class Order:
    order_id: str
    product: str
    qty: int
    priority: str
    due_date: str
    spec_id: str

    def as_dict(self) -> dict:
        return asdict(self)


class OnesAdapter(Protocol):
    def get_order(self, order_id: str) -> Order | None: ...

    def list_open_orders(self) -> list[Order]: ...
