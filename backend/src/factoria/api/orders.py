"""Заказы 1С (v1 — только чтение, ТЗ §9.1–§9.2)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from factoria.adapters.base import Order
from factoria.auth.rbac import Principal, require

router = APIRouter(prefix="/api/v1", tags=["orders"])


class OrderIn(BaseModel):
    order_id: str = Field(min_length=1, max_length=32)
    product: str = Field(min_length=1, max_length=120)
    qty: int = Field(ge=1, le=1_000_000)
    priority: str = Field(pattern="^(low|normal|high)$")
    due_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    spec_id: str = Field(min_length=1, max_length=32)


@router.get("/orders")
async def list_orders(request: Request, principal: Principal = Depends(require("read"))) -> dict:
    adapter = request.app.state.ones
    return {
        "source": request.app.state.settings.ones_mode,
        "orders": [order.as_dict() for order in adapter.list_open_orders()],
    }


@router.get("/orders/{order_id}")
async def get_order(
    order_id: str, request: Request, principal: Principal = Depends(require("read"))
) -> dict:
    order = request.app.state.ones.get_order(order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="заказ не найден")
    return order.as_dict()


@router.post("/debug/orders", status_code=201)
async def add_debug_order(
    body: OrderIn, request: Request, principal: Principal = Depends(require("operator"))
) -> dict:
    """Только ENV=dev (ТЗ §9.2). В остальных средах маршрут отсутствует."""
    if request.app.state.settings.env != "dev":
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="not found")
    return request.app.state.ones.add_order(Order(**body.model_dump())).as_dict()
