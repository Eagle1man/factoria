"""Команды: идемпотентность, валидация, подтверждение, исполнение (ТЗ §5.1–§5.5)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from factoria.audit.storage import audit
from factoria.auth.rbac import Principal, require
from factoria.contract.loader import ContractError, get_contract, validate_envelope
from factoria.opcua.commands import dispatch_command
from factoria.storage.db import get_session
from factoria.storage.models import Approval, Command
from factoria.validation.pipeline import Stage, ValidationResult, load_interlocks, validate_command

router = APIRouter(prefix="/api/v1", tags=["commands"])

TTL_MINUTES = 5


class Target(BaseModel):
    line_id: str = Field(min_length=1, max_length=8)


class RequestedBy(BaseModel):
    kind: str = Field(pattern="^(agent|human)$")
    id: str = Field(min_length=1, max_length=64)


class CommandRequest(BaseModel):
    command_id: str = Field(min_length=8, max_length=40)
    type: str
    target: Target
    params: dict
    requested_by: RequestedBy
    agent_session_id: str | None = None
    correlation_id: str = Field(min_length=8, max_length=40)
    evidence: list[str] = Field(default_factory=list)


class ApproveRequest(BaseModel):
    version: int = Field(ge=1)
    comment: str | None = Field(default=None, max_length=500)


class RejectRequest(BaseModel):
    version: int = Field(ge=1)
    reason: str = Field(min_length=3, max_length=500)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


async def _expire_if_needed(command: Command, session: AsyncSession) -> None:
    if command.status != "AWAITING_APPROVAL":
        return
    expires = _aware(command.expires_at)
    if expires is not None and expires < _now():
        command.status = "EXPIRED"
        await session.commit()


def _trace_json(result: ValidationResult) -> str:
    return json.dumps([stage.__dict__ for stage in result.trace], ensure_ascii=False)


def _command_dict(command: Command) -> dict:
    return {
        "command_id": command.command_id,
        "type": command.type,
        "line_id": command.target_line,
        "status": command.status,
        "autonomy_level": command.autonomy_level,
        "version": command.version,
        "params": json.loads(command.params),
        "validation_trace": json.loads(command.validation_trace),
        "expires_at": _aware(command.expires_at).isoformat() if command.expires_at else None,
        "created_at": _aware(command.created_at).isoformat() if command.created_at else None,
    }


@router.post("/commands", status_code=202)
async def submit_command(
    body: CommandRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(require("read")),
):
    existing = await session.get(Command, body.command_id)
    if existing is not None:
        await _expire_if_needed(existing, session)
        return {
            "command_id": existing.command_id,
            "status": existing.status,
            "duplicate": True,
        }

    contract = get_contract()
    payload = body.model_dump()
    try:
        validate_envelope(contract, payload)
        result = validate_command(
            payload,
            contract=contract,
            registry=request.app.state.registry,
            values=request.app.state.cache.snapshot()["values"],
            max_autonomy=request.app.state.settings.autonomy_max,
            allowed_targets=request.app.state.settings.allowed_targets,
            interlocks=load_interlocks(),
        )
    except ContractError as exc:
        result = ValidationResult(
            ok=False,
            status="REJECTED",
            autonomy="A1",
            trace=[Stage("schema_check", False, "SCHEMA_001", str(exc))],
            code="SCHEMA_001",
            detail=str(exc),
        )

    command = Command(
        command_id=body.command_id,
        type=body.type,
        target_line=body.target.line_id,
        params=json.dumps(body.params, ensure_ascii=False),
        requested_by_kind=body.requested_by.kind,
        requested_by_id=body.requested_by.id,
        agent_session_id=body.agent_session_id,
        correlation_id=body.correlation_id,
        status=result.status,
        autonomy_level=result.autonomy,
        validation_trace=_trace_json(result),
        expires_at=_now() + timedelta(minutes=TTL_MINUTES) if result.ok else None,
    )
    session.add(command)
    await session.commit()

    await audit.write(
        "command",
        "accepted" if result.ok else "rejected",
        actor=body.requested_by.id,
        subject=body.command_id,
        payload={
            "type": body.type,
            "line_id": body.target.line_id,
            "status": result.status,
            "code": result.code,
            "autonomy": result.autonomy,
        },
        correlation_id=body.correlation_id,
    )

    if not result.ok:
        last = result.trace[-1]
        return JSONResponse(
            status_code=422,
            content={"stage": last.stage, "code": result.code, "detail": result.detail},
        )

    return {
        "command_id": body.command_id,
        "status": result.status,
        "autonomy_level": result.autonomy,
        "expires_in": TTL_MINUTES * 60,
        "duplicate": False,
    }


@router.get("/commands")
async def list_commands(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(require("read")),
) -> dict:
    stmt = select(Command).order_by(Command.created_at.desc()).limit(limit)
    if status_filter:
        stmt = stmt.where(Command.status == status_filter)
    rows = (await session.execute(stmt)).scalars().all()

    # TTL: истёкшие карточки не должны висеть в очереди (ТЗ §5.1, §6.6).
    now = _now()
    changed = False
    for row in rows:
        expires = _aware(row.expires_at)
        if row.status == "AWAITING_APPROVAL" and expires is not None and expires < now:
            row.status = "EXPIRED"
            changed = True
    if changed:
        await session.commit()
        rows = [row for row in rows if not (status_filter and row.status != status_filter)]

    return {"commands": [_command_dict(row) for row in rows], "count": len(rows)}


@router.get("/commands/{command_id}")
async def get_command(
    command_id: str,
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(require("read")),
) -> dict:
    command = await session.get(Command, command_id)
    if command is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="команда не найдена")
    await _expire_if_needed(command, session)
    return _command_dict(command)


@router.post("/commands/{command_id}/approve")
async def approve_command(
    command_id: str,
    body: ApproveRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(require("operator")),
) -> dict:
    command = await session.get(Command, command_id)
    if command is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="команда не найдена")
    await _expire_if_needed(command, session)

    if command.status != "AWAITING_APPROVAL":
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail=f"статус {command.status}, подтверждение невозможно"
        )
    if body.version != command.version:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="версия устарела, обновите карточку")

    settings = request.app.state.settings
    command.status = "DISPATCHING"
    command.version += 1
    await session.commit()

    ok, detail = await dispatch_command(
        endpoint=settings.opcua_endpoint,
        namespace=request.app.state.registry.namespace,
        line_id=command.target_line,
        command_type=command.type,
        params=json.loads(command.params),
    )

    command.status = "EXECUTED" if ok else "FAILED"
    session.add(
        Approval(
            id=str(uuid4()),
            command_id=command_id,
            operator_id=principal.user_id,
            decision="approve",
            comment=body.comment,
        )
    )
    await session.commit()

    await audit.write(
        "execution",
        "executed" if ok else "failed",
        actor=principal.user_id,
        subject=command_id,
        payload={"detail": detail},
        correlation_id=command.correlation_id,
    )
    return {"command_id": command_id, "status": command.status, "detail": detail}


@router.post("/commands/{command_id}/reject")
async def reject_command(
    command_id: str,
    body: RejectRequest,
    session: AsyncSession = Depends(get_session),
    principal: Principal = Depends(require("operator")),
) -> dict:
    command = await session.get(Command, command_id)
    if command is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="команда не найдена")
    if command.status != "AWAITING_APPROVAL":
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail=f"статус {command.status}, отклонение невозможно"
        )
    if body.version != command.version:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="версия устарела")

    command.status = "REJECTED"
    command.version += 1
    session.add(
        Approval(
            id=str(uuid4()),
            command_id=command_id,
            operator_id=principal.user_id,
            decision="reject",
            comment=body.reason,
        )
    )
    await session.commit()

    await audit.write(
        "approval",
        "rejected",
        actor=principal.user_id,
        subject=command_id,
        payload={"reason": body.reason},
        correlation_id=command.correlation_id,
    )
    return {"command_id": command_id, "status": command.status}
