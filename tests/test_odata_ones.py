"""OData-адаптер 1С: стандартный интерфейс без правки конфигурации."""
from __future__ import annotations

import httpx
import pytest
from factoria.adapters.odata_ones import ODataOnesAdapter, OnesUnavailable

ROW = {
    "Number": "РТУ-000001",
    "Date": "2026-11-01T12:00:00",
    "Контрагент": {"Description": "ООО Ромашка"},
    "Товары": [{"Количество": 5}, {"Количество": 7}],
    "document_type": "РеализацияТоваровУслуг",
}


def make(handler) -> ODataOnesAdapter:
    return ODataOnesAdapter(
        "http://1c.local/mfg/odata/standard.odata",
        "user",
        "pass",
        transport=httpx.MockTransport(handler),
    )


def test_list_maps_sales_document():
    adapter = make(lambda request: httpx.Response(200, json={"value": [ROW]}))
    orders = adapter.list_open_orders()
    assert len(orders) == 1
    assert orders[0].order_id == "РТУ-000001"
    assert orders[0].product == "ООО Ромашка"
    assert orders[0].qty == 12
    assert orders[0].due_date == "2026-11-01"
    assert orders[0].spec_id == "РеализацияТоваровУслуг"


def test_get_order_uses_filter():
    captured: dict = {}

    def handler(request):
        captured["url"] = str(request.url)
        return httpx.Response(200, json={"value": [ROW]})

    adapter = make(handler)
    order = adapter.get_order("РТУ-000001")
    assert order is not None
    assert "%D0%A0" in captured["url"] or "РТУ" in captured["url"]


def test_get_order_missing_returns_none():
    adapter = make(lambda request: httpx.Response(200, json={"value": []}))
    assert adapter.get_order("NOPE") is None


def test_http_error_is_unavailable():
    adapter = make(lambda request: httpx.Response(401, text="denied"))
    with pytest.raises(OnesUnavailable):
        adapter.list_open_orders()


def test_html_instead_of_json_is_error():
    adapter = make(lambda request: httpx.Response(200, text="<html>login</html>"))
    with pytest.raises(OnesUnavailable):
        adapter.list_open_orders()


def test_missing_value_is_error():
    adapter = make(lambda request: httpx.Response(200, json={"odata.metadata": "x"}))
    with pytest.raises(OnesUnavailable):
        adapter.list_open_orders()


def test_empty_value_is_valid():
    adapter = make(lambda request: httpx.Response(200, json={"value": []}))
    assert adapter.list_open_orders() == []
