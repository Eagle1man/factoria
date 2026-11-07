"""Эксперименты на симуляторе (ТЗ §10, экран «Эксперименты»)."""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from factoria.audit.storage import audit
from factoria.auth.rbac import Principal, require
from factoria.sim.runner import MAX_HORIZON_S, run_scenario
from factoria.sim.scenarios import SCENARIOS
from factoria.storage.db import get_session
from factoria.storage.models import SimRun

router = APIRouter(prefix="/api/v1", tags=["sim"])


class RunRequest(BaseModel):
    scenario: str = Field(min_length=1, max_length=32)
    seed: int = Field(ge=0, le=2_147_483_647)
    horizon_s: int = Field(ge=10, le=MAX_HORIZON_S)


def _as_dict(row: SimRun) -> dict[str, Any]:
    return {
        "id": row.id,
        "scenario": row.scenario,
        "seed": row.seed,
        "horizon_s": row.horizon_s,
        "status": row.status,
        "metrics": json.loads(row.metrics or "{}"),
        "events": json.loads(row.events or "[]"),
        "repro_hash": row.repro_hash,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "created_by": row.created_by,
    }


@router.get("/sim/scenarios")
async def list_scenarios(principal: Principal = Depends(require("read"))) -> dict:
    return {
        "scenarios": [
            {"name": item.name, "title": item.title, "description": item.description}
            for item in SCENARIOS.values()
        ]
    }


@router.post("/sim/runs", status_code=201)
async def create_run(
    body: RunRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(require("operator")),
) -> dict:
    try:
        result = run_scenario(body.scenario, body.seed, body.horizon_s)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

    row = SimRun(
        scenario=result["scenario"],
        seed=result["seed"],
        horizon_s=result["horizon_s"],
        metrics=json.dumps(result["metrics"], ensure_ascii=False),
        events=json.dumps(result["events"], ensure_ascii=False),
        repro_hash=result["repro_hash"],
        created_by=principal.user_id,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    await audit.write(
        "system",
        "sim_run",
        actor=principal.user_id,
        subject=str(row.id),
        payload={"scenario": row.scenario, "seed": row.seed, "hash": row.repro_hash},
    )
    return _as_dict(row)


@router.get("/sim/runs")
async def list_runs(
    limit: int = Query(default=20, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(require("read")),
) -> dict:
    rows = (
        await session.execute(select(SimRun).order_by(SimRun.id.desc()).limit(limit))
    ).scalars().all()
    return {"runs": [_as_dict(row) for row in rows], "count": len(rows)}


@router.get("/sim/runs/{run_id:int}")
async def get_run(
    run_id: int,
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(require("read")),
) -> dict:
    row = await session.get(SimRun, run_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="прогон не найден")
    return _as_dict(row)


@router.get("/sim/runs/compare")
async def compare_runs(
    a: int = Query(ge=1),
    b: int = Query(ge=1),
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(require("read")),
) -> dict:
    first = await session.get(SimRun, a)
    second = await session.get(SimRun, b)
    if first is None or second is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="прогон не найден")

    left, right = _as_dict(first), _as_dict(second)
    if (left["created_at"] or "") > (right["created_at"] or ""):
        left, right = right, left

    keys = ("output_index", "max_temp", "avg_load", "uptime_pct", "alarms")
    delta = {
        key: round(float(right["metrics"].get(key, 0)) - float(left["metrics"].get(key, 0)), 2)
        for key in keys
    }
    return {
        "from": {"id": left["id"], "scenario": left["scenario"], "seed": left["seed"]},
        "to": {"id": right["id"], "scenario": right["scenario"], "seed": right["seed"]},
        "metrics": {"from": left["metrics"], "to": right["metrics"]},
        "delta": delta,
        "same_repro": left["repro_hash"] == right["repro_hash"],
    }
