"""OData-адаптер 1С (стандартный интерфейс, без правки конфигурации).

Публикация базы включает `standardOdata`, и документы становятся доступны по
`/odata/standard.odata/Document_<Имя>?$format=json` с правами пользователя 1С.

Для демо-базы DemoAgent документов заказов нет, есть `РеализацияТоваровУслуг`.
Маппинг продаж в «заказ» — решение демо-контура, а не свойство 1С: в ответе
всегда есть `document_type`, чтобы это было видно.
"""
from __future__ import annotations

from typing import Any

import httpx

from factoria.adapters.base import Order

DOCUMENT = "Document_РеализацияТоваровУслуг"


class OnesUnavailable(RuntimeError):
    """1С недоступна или вернула ошибку."""


def _sum_qty(row: dict[str, Any]) -> int:
    goods = row.get("Товары")
    if not isinstance(goods, list):
        return 0
    total = 0.0
    for item in goods:
        try:
            total += float(item.get("Количество") or 0)
        except (TypeError, ValueError):
            continue
    return int(round(total))


def _to_order(row: dict[str, Any]) -> Order:
    try:
        partner = row.get("Контрагент") or {}
        product = partner.get("Description") if isinstance(partner, dict) else None
        date = str(row.get("Date") or "")[:10]
        return Order(
            order_id=str(row["Number"]),
            product=str(product or row.get("Контрагент_Key") or "без контрагента"),
            qty=_sum_qty(row),
            priority=str(row.get("priority") or "normal"),
            due_date=date,
            spec_id=str(row.get("document_type") or "SALES"),
        )
    except (KeyError, TypeError) as exc:
        raise OnesUnavailable(f"неверный формат документа 1С: {exc}") from exc


class ODataOnesAdapter:
    def __init__(
        self,
        base_url: str,
        user: str | None = None,
        password: str | None = None,
        *,
        timeout: float = 8.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not base_url:
            raise OnesUnavailable("ONES_HTTP_URL не задан")
        self.base_url = base_url.rstrip("/") + "/"
        self.auth = (user, password) if user else None
        self.timeout = timeout
        self._transport = transport

    def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        try:
            with httpx.Client(
                base_url=self.base_url,
                auth=self.auth,
                timeout=self.timeout,
                transport=self._transport,
            ) as client:
                response = client.get(path, params=params)
        except httpx.HTTPError as exc:
            raise OnesUnavailable(f"1С недоступна: {exc}") from exc

        if response.status_code >= 400:
            raise OnesUnavailable(f"1С вернула HTTP {response.status_code}")
        try:
            return response.json()
        except ValueError as exc:
            raise OnesUnavailable("1С вернула не JSON (вероятно, HTML-страница ошибки)") from exc

    def list_open_orders(self) -> list[Order]:
        payload = self._get(
            DOCUMENT,
            {
                "$format": "json",
                "$top": "50",
                "$orderby": "Date desc",
                "$expand": "Контрагент",
            },
        )
        rows = payload.get("value")
        if not isinstance(rows, list):
            raise OnesUnavailable("в ответе OData нет массива value")
        return [_to_order(row) for row in rows]

    def get_order(self, order_id: str) -> Order | None:
        payload = self._get(
            DOCUMENT,
            {
                "$format": "json",
                "$top": "1",
                "$filter": f"Number eq '{order_id}'",
                "$expand": "Контрагент",
            },
        )
        rows = payload.get("value") or []
        return _to_order(rows[0]) if rows else None
