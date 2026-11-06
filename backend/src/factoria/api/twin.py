"""API двойника (ТЗ §18.5, маршрут /twin)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from factoria.auth.rbac import Principal, require
from factoria.model.semantic import build_semantic
from factoria.model.twin import build_twin

router = APIRouter(prefix="/api/v1", tags=["twin"])


@router.get("/twin")
async def twin(request: Request, principal: Principal = Depends(require("read"))) -> dict:
    registry = request.app.state.registry
    orders = request.app.state.ones.list_open_orders()
    model = build_semantic(registry, orders)
    return build_twin(registry, request.app.state.cache, model)
