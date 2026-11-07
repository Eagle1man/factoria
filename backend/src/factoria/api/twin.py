"""API двойника: текущий срез, история и сравнение (ТЗ §18.5, ADR-119)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from factoria.audit.storage import audit
from factoria.auth.rbac import Principal, require
from factoria.model.history import compare, get_version, list_versions, save_snapshot
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


@router.get("/twin/compare")
async def twin_compare(
    a: int = Query(ge=1),
    b: int = Query(ge=1),
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(require("read")),
) -> dict:
    first = await get_version(session, a)
    second = await get_version(session, b)
    if first is None or second is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="срез не найден")
    # Порядок задаёт время, а не порядок кликов: «раньше → позже».
    from datetime import datetime

    if datetime.fromisoformat(first["built_at"]) > datetime.fromisoformat(second["built_at"]):
        first, second = second, first
    return compare(first, second)


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
