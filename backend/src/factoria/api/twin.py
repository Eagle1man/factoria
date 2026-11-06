"""API двойника: текущий срез и история версий (ТЗ §18.5, ADR-119)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from factoria.audit.storage import audit
from factoria.auth.rbac import Principal, require
from factoria.model.history import list_versions, save_snapshot
from factoria.model.semantic import build_semantic
from factoria.model.twin import build_twin
from factoria.storage.db import get_session

router = APIRouter(prefix="/api/v1", tags=["twin"])


def _current(request: Request) -> dict:
    registry = request.app.state.registry
    orders = request.app.state.ones.list_open_orders()
    model = build_semantic(registry, orders)
    return build_twin(registry, request.app.state.cache, model)


@router.get("/twin")
async def twin(request: Request, principal: Principal = Depends(require("read"))) -> dict:
    return _current(request)


@router.get("/twin/history")
async def twin_history(
    limit: int = Query(default=20, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(require("read")),
) -> dict:
    versions = await list_versions(session, limit)
    return {"versions": versions, "count": len(versions)}


@router.post("/twin/snapshot", status_code=201)
async def twin_snapshot(
    request: Request,
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(require("operator")),
) -> dict:
    current = _current(request)
    saved = await save_snapshot(session, current)
    await audit.write(
        "system",
        "twin_snapshot",
        actor=principal.user_id,
        subject=saved["version"],
        payload={
            "coverage_pct": saved["coverage_pct"],
            "tags_good": saved["tags_good"],
            "tags_total": saved["tags_total"],
        },
    )
    return saved
