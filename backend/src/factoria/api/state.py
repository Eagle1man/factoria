"""Состояние оборудования и история тегов (ТЗ §5.2)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from factoria.auth.rbac import Principal, require
from factoria.realtime.cache import TagCache
from factoria.storage.db import get_session
from factoria.storage.models import TagHistory

router = APIRouter(prefix="/api/v1", tags=["equipment"])


def _cache(request: Request) -> TagCache:
    return request.app.state.cache


@router.get("/equipment")
async def equipment(
    request: Request, principal: Principal = Depends(require("read"))
) -> dict:
    cache = _cache(request)
    registry = request.app.state.registry
    snapshot = cache.snapshot()
    lines = []
    for line in registry.lines:
        def val(name: str):
            return snapshot["values"].get(f"{line}.{name}", {"v": None, "q": "BAD"})

        lines.append(
            {
                "line_id": line,
                "running": val("Running")["v"],
                "speed_sp": val("Speed.SP")["v"],
                "speed_pv": val("Speed.PV")["v"],
                "temp": val("Temp.PV")["v"],
                "load": val("Load.Pct")["v"],
                "alarm": val("Alarm.Code")["v"],
                "recipe": val("Recipe.ID")["v"],
                "quality": val("Speed.PV")["q"],
            }
        )
    return {"lines": lines, "snapshot_ts": snapshot["snapshot_ts"], "seq": snapshot["seq"]}


@router.get("/equipment/{line_id}/state")
async def line_state(
    line_id: str, request: Request, principal: Principal = Depends(require("read"))
) -> dict:
    cache = _cache(request)
    registry = request.app.state.registry
    if line_id not in registry.lines:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="линия не найдена")
    tags = [t.id for t in registry.line_tags(line_id)]
    snapshot = cache.snapshot(tags)
    return {"line_id": line_id, **snapshot}


@router.get("/tags/history")
async def tag_history(
    tag: str,
    request: Request,
    from_ts: datetime | None = Query(default=None, alias="from"),
    to_ts: datetime | None = Query(default=None, alias="to"),
    max_points: int = Query(default=500, ge=1, le=5000),
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(require("read")),
) -> dict:
    registry = request.app.state.registry
    if tag not in {t.id for t in registry.tags}:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="тег не найден")

    now = datetime.now(timezone.utc)
    stmt = select(TagHistory).where(TagHistory.tag == tag)
    if from_ts:
        stmt = stmt.where(TagHistory.ts >= from_ts)
    if to_ts:
        stmt = stmt.where(TagHistory.ts <= to_ts)
    stmt = stmt.order_by(TagHistory.ts.asc()).limit(max_points * 10)
    rows = (await session.execute(stmt)).scalars().all()
    step = max(1, len(rows) // max_points) if rows else 1
    points = [
        [r.ts.isoformat(), r.value, r.quality]
        for r in rows[::step][:max_points]
    ]
    return {"tag": tag, "points": points, "from": from_ts.isoformat() if from_ts else None,
            "to": to_ts.isoformat() if to_ts else None, "now": now.isoformat()}
