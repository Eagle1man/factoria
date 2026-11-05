"""Аудит: только добавление записей (ТЗ §5.5, R-015)."""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from factoria.storage.db import session_factory
from factoria.storage.models import AuditEvent


class AuditLog:
    def __init__(self, factory: async_sessionmaker[AsyncSession] | None = None) -> None:
        self._factory = factory or session_factory

    async def write(
        self,
        kind: str,
        action: str,
        *,
        actor: str = "system",
        subject: str | None = None,
        payload: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        async with self._factory() as session:
            session.add(
                AuditEvent(
                    kind=kind,
                    action=action,
                    actor=actor,
                    subject=subject,
                    payload=json.dumps(payload or {}, ensure_ascii=False, default=str),
                    correlation_id=correlation_id,
                )
            )
            await session.commit()

    async def recent(
        self,
        *,
        limit: int = 100,
        kind: str | None = None,
        actor: str | None = None,
    ) -> list[dict[str, Any]]:
        async with self._factory() as session:
            stmt = select(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit)
            if kind:
                stmt = stmt.where(AuditEvent.kind == kind)
            if actor:
                stmt = stmt.where(AuditEvent.actor == actor)
            rows = (await session.execute(stmt)).scalars().all()
            return [
                {
                    "id": r.id,
                    "ts": r.ts.isoformat(),
                    "kind": r.kind,
                    "actor": r.actor,
                    "action": r.action,
                    "subject": r.subject,
                    "payload": json.loads(r.payload),
                    "correlation_id": r.correlation_id,
                }
                for r in rows
            ]


audit = AuditLog()
