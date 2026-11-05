"""Stub-1С для этапа 4a (ТЗ §9.2): 5 заказов в памяти, только чтение."""
from __future__ import annotations

from datetime import date, timedelta

from factoria.adapters.base import Order


def _seed() -> dict[str, Order]:
    today = date.today()
    rows = [
        ("ORD-1001", "Корпус редуктора", 120, "high", 1, "SPEC-01"),
        ("ORD-1002", "Вал привода", 300, "normal", 3, "SPEC-02"),
        ("ORD-1003", "Фланец", 800, "normal", 5, "SPEC-01"),
        ("ORD-1004", "Крышка подшипника", 450, "low", 7, "SPEC-03"),
        ("ORD-1005", "Шестерня", 200, "high", 2, "SPEC-02"),
    ]
    return {
        order_id: Order(
            order_id=order_id,
            product=product,
            qty=qty,
            priority=priority,
            due_date=(today + timedelta(days=days)).isoformat(),
            spec_id=spec,
        )
        for order_id, product, qty, priority, days, spec in rows
    }


class StubAdapter:
    def __init__(self) -> None:
        self._orders = _seed()

    def get_order(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    def list_open_orders(self) -> list[Order]:
        return sorted(self._orders.values(), key=lambda order: order.due_date)

    def add_order(self, order: Order) -> Order:
        self._orders[order.order_id] = order
        return order
