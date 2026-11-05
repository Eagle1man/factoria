"""Health и журнал аудита."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from factoria.audit.storage import audit
from factoria.auth.rbac import Principal, require

router = APIRouter(prefix="/api/v1", tags=["system"])


@router.get("/health")
async def health(request: Request) -> dict:
    cache = request.app.state.cache
    registry = request.app.state.registry
    snapshot = cache.snapshot()
    bad = [t for t, v in snapshot["values"].items() if v["q"] != "GOOD"]
    return {
        "status": "ok",
        "env": request.app.state.settings.env,
        "sources": {
            "opcua": {
                "state": cache.source,
                "changed_at": cache.source_changed_at.isoformat() if cache.source_changed_at else None,
                "endpoint": request.app.state.settings.opcua_endpoint,
            },
            "database": "ok",
        },
        "tags": {"total": len(registry.tags), "not_good": len(bad)},
        "snapshot_ts": snapshot["snapshot_ts"],
    }


@router.get("/audit")
async def audit_events(
    limit: int = Query(default=100, ge=1, le=1000),
    kind: str | None = None,
    actor: str | None = None,
    principal: Principal = Depends(require("audit_read")),
) -> dict:
    events = await audit.recent(limit=limit, kind=kind, actor=actor)
    return {"events": events, "count": len(events)}
