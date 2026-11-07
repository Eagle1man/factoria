"""HTTP-адаптер 1С (этап 4b, ТЗ §9.3). Только чтение.

Контракт: `docs/ones-http-contract.md`.
Любая ошибка источника — исключение, а не «пустой список»: пустой ответ и
недоступность не должны выглядеть одинаково.
"""
from __future__ import annotations

from typing import Any

import httpx

from factoria.adapters.base import Order


class OnesUnavailable(RuntimeError):
    """1С недоступна или вернула ошибку. Данные не подменяются."""


def _to_order(payload: dict[str, Any]) -> Order:
    try:
        return Order(
            order_id=str(payload["order_id"]),
            product=str(payload["product"]),
            qty=int(payload["qty"]),
            priority=str(payload["priority"]),
            due_date=str(payload["due_date"]),
            spec_id=str(payload["spec_id"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise OnesUnavailable(f"неверный формат заказа: {exc}") from exc


class HttpOnesAdapter:
    def __init__(
        self,
        base_url: str,
        user: str | None = None,
        password: str | None = None,
        *,
        timeout: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not base_url:
            raise OnesUnavailable("ONES_HTTP_URL не задан")
        self.base_url = base_url.rstrip("/") + "/"
        self.auth = (user, password) if user else None
        self.timeout = timeout
        self._transport = transport

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.base_url,
            auth=self.auth,
            timeout=self.timeout,
            transport=self._transport,
        )

    def _get(self, path: str) -> dict[str, Any] | None:
        try:
            with self._client() as client:
                response = client.get(path)
        except httpx.HTTPError as exc:
            raise OnesUnavailable(f"1С недоступна: {exc}") from exc

        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise OnesUnavailable(f"1С вернула HTTP {response.status_code}")
        try:
            return response.json()
        except ValueError as exc:
            raise OnesUnavailable("1С вернула не JSON") from exc

    def get_order(self, order_id: str) -> Order | None:
        payload = self._get(f"mfg/orders/{order_id}")
        return _to_order(payload) if payload else None

    def list_open_orders(self) -> list[Order]:
        payload = self._get("mfg/orders/open")
        if payload is None:
            raise OnesUnavailable("эндпоинт /mfg/orders/open вернул 404")
        rows = payload.get("orders")
        if not isinstance(rows, list):
            raise OnesUnavailable("в ответе нет списка orders")
        return [_to_order(row) for row in rows]
