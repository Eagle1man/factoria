"""История срезов цифрового двойника (ADR-119)."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from factoria.storage.models import TwinVersion


def _as_dict(row: TwinVersion) -> dict[str, Any]:
    return {
        "id": row.id,
        "version": row.version,
        "built_at": row.built_at.isoformat() if row.built_at else None,
        "status": row.status,
        "coverage_pct": row.coverage_pct,
        "tags_good": row.tags_good,
        "tags_total": row.tags_total,
        "freshness_sec": row.freshness_sec,
        "snapshot_seq": row.snapshot_seq,
        "warnings": json.loads(row.warnings or "[]"),
    }


def _delta(previous: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
    if previous is None:
        return {"coverage_pct": None, "tags_good": None}
    return {
        "coverage_pct": round(current["coverage_pct"] - previous["coverage_pct"], 2),
        "tags_good": current["tags_good"] - previous["tags_good"],
    }


async def save_snapshot(session: AsyncSession, twin: dict[str, Any]) -> dict[str, Any]:
    row = TwinVersion(
        version=twin["version"],
        status=twin["status"],
        coverage_pct=float(twin["metrics"]["coverage_pct"]),
        tags_good=int(twin["metrics"]["tags_good"]),
        tags_total=int(twin["metrics"]["tags_total"]),
        freshness_sec=twin["metrics"]["freshness_sec"],
        snapshot_seq=int(twin["basis"]["snapshot_seq"]),
        warnings=json.dumps(twin.get("warnings", []), ensure_ascii=False),
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _as_dict(row)


async def list_versions(session: AsyncSession, limit: int = 20) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            select(TwinVersion).order_by(TwinVersion.id.desc()).limit(limit)
        )
    ).scalars().all()
    ordered = [_as_dict(row) for row in reversed(rows)]
    result: list[dict[str, Any]] = []
    previous: dict[str, Any] | None = None
    for item in ordered:
        item = dict(item)
        item["delta"] = _delta(previous, item)
        result.append(item)
        previous = item
    return list(reversed(result))


async def latest(session: AsyncSession) -> dict[str, Any] | None:
    row = (
        await session.execute(select(TwinVersion).order_by(TwinVersion.id.desc()).limit(1))
    ).scalar_one_or_none()
    return _as_dict(row) if row else None


def compare(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    """Сравнение двух срезов по метрикам."""
    return {
        "from": {"id": first["id"], "built_at": first["built_at"]},
        "to": {"id": second["id"], "built_at": second["built_at"]},
        "coverage_pct": round(second["coverage_pct"] - first["coverage_pct"], 2),
        "tags_good": second["tags_good"] - first["tags_good"],
        "freshness_sec": (
            round((second["freshness_sec"] or 0) - (first["freshness_sec"] or 0), 2)
            if first["freshness_sec"] is not None and second["freshness_sec"] is not None
            else None
        ),
        "version_changed": first["version"] != second["version"],
    }


def since(iso: str) -> datetime:
    return datetime.fromisoformat(iso)
