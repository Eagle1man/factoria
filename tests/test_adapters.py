"""Stub-1С: пять заказов, только чтение, добавление отдельным методом."""
from __future__ import annotations

from factoria.adapters.base import Order
from factoria.adapters.stub import StubAdapter


def test_stub_has_five_orders():
    adapter = StubAdapter()
    orders = adapter.list_open_orders()
    assert len(orders) == 5
    assert all(order.qty > 0 for order in orders)


def test_orders_sorted_by_due_date():
    adapter = StubAdapter()
    dates = [order.due_date for order in adapter.list_open_orders()]
    assert dates == sorted(dates)


def test_get_order_and_missing():
    adapter = StubAdapter()
    assert adapter.get_order("ORD-1001") is not None
    assert adapter.get_order("ORD-0000") is None


def test_add_order():
    adapter = StubAdapter()
    order = Order(
        order_id="ORD-2000",
        product="Тестовая деталь",
        qty=10,
        priority="high",
        due_date="2026-12-31",
        spec_id="SPEC-01",
    )
    adapter.add_order(order)
    assert adapter.get_order("ORD-2000") == order
    assert len(adapter.list_open_orders()) == 6
