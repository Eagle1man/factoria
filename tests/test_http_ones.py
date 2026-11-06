"""HTTP-адаптер 1С: контракт, ошибки и отсутствие подмены данных."""
from __future__ import annotations

import httpx
import pytest

from factoria.adapters.http_ones import HttpOnesAdapter, OnesUnavailable

ORDER = {
    "order_id": "ORD-1",
    "product": "Корпус редуктора",
    "qty": 10,
    "priority": "high",
    "due_date": "2026-11-08",
    "spec_id": "SPEC-01",
}


def make(handler) -> HttpOnesAdapter:
    return HttpOnesAdapter(
        "http://ones.local", "user", "pass", transport=httpx.MockTransport(handler)
    )


def test_list_open_orders():
    adapter = make(lambda request: httpx.Response(200, json={"orders": [ORDER]}))
    orders = adapter.list_open_orders()
    assert len(orders) == 1
    assert orders[0].order_id == "ORD-1"
    assert orders[0].priority == "high"


def test_get_order_not_found_returns_none():
    adapter = make(lambda request: httpx.Response(404, json={"error": "нет"}))
    assert adapter.get_order("ORD-404") is None


def test_server_error_is_not_empty_list():
    adapter = make(lambda request: httpx.Response(500, text="boom"))
    with pytest.raises(OnesUnavailable):
        adapter.list_open_orders()


def test_non_json_is_error():
    adapter = make(lambda request: httpx.Response(200, text="<html>1C</html>"))
    with pytest.raises(OnesUnavailable):
        adapter.list_open_orders()


def test_missing_orders_key_is_error():
    adapter = make(lambda request: httpx.Response(200, json={"items": []}))
    with pytest.raises(OnesUnavailable):
        adapter.list_open_orders()


def test_broken_order_payload_is_error():
    adapter = make(lambda request: httpx.Response(200, json={"orders": [{"order_id": "X"}]}))
    with pytest.raises(OnesUnavailable):
        adapter.list_open_orders()


def test_empty_list_is_valid():
    adapter = make(lambda request: httpx.Response(200, json={"orders": []}))
    assert adapter.list_open_orders() == []


def test_network_error_is_unavailable():
    def handler(request):
        raise httpx.ConnectError("нет соединения")

    adapter = make(handler)
    with pytest.raises(OnesUnavailable):
        adapter.list_open_orders()


def test_missing_url_rejected():
    with pytest.raises(OnesUnavailable):
        HttpOnesAdapter("")
