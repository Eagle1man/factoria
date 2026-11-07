"""Аутентификация: вход, refresh, отзыв, тикет для WS (ТЗ §5.6)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from factoria.audit.storage import audit
from factoria.auth.limiter import limiter
from factoria.auth.rbac import Principal, get_principal
from factoria.auth.security import (
    create_access,
    create_refresh,
    decode_token,
    verify_password,
)
from factoria.auth.tickets import tickets
from factoria.config import get_settings
from factoria.storage.db import get_session
from factoria.storage.models import RefreshToken, User

router = APIRouter(prefix="/api/v1", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    expires_in: int


class WsTicketResponse(BaseModel):
    ticket: str
    expires_in: int


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


async def _issue_tokens(session: AsyncSession, user: User) -> TokenResponse:
    access, expires_in = create_access(user.id, user.role)
    refresh_token, jti, expires = create_refresh(user.id)
    session.add(RefreshToken(jti=jti, user_id=user.id, expires_at=expires))
    await session.commit()
    return TokenResponse(
        access_token=access,
        refresh_token=refresh_token,
        role=user.role,
        expires_in=expires_in,
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_session)) -> TokenResponse:
    locked = limiter.locked_for(body.username)
    if locked:
        await audit.write(
            "auth", "login_locked", actor=body.username, payload={"seconds_left": locked}
        )
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, detail=f"вход заблокирован ещё {locked} c"
        )

    user = await session.scalar(select(User).where(User.username == body.username))
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        limiter.fail(body.username)
        await audit.write(
            "auth", "login_failed", actor=body.username, payload={"reason": "bad_credentials"}
        )
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="неверные учётные данные")

    limiter.reset(body.username)
    await audit.write("auth", "login", actor=user.id, payload={"role": user.role})
    return await _issue_tokens(session, user)


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, session: AsyncSession = Depends(get_session)) -> TokenResponse:
    try:
        payload = decode_token(body.refresh_token, "refresh")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="refresh не принят") from exc

    row = await session.get(RefreshToken, payload["jti"])
    if row is None or row.revoked:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="refresh отозван")
    if _aware(row.expires_at) and _aware(row.expires_at) < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="refresh истёк")

    user = await session.get(User, payload["sub"])
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="пользователь недоступен")

    row.revoked = True
    await session.commit()
    await audit.write("auth", "refresh", actor=user.id)
    return await _issue_tokens(session, user)


@router.post("/auth/logout", status_code=204)
async def logout(body: RefreshRequest, session: AsyncSession = Depends(get_session)) -> None:
    try:
        payload = decode_token(body.refresh_token, "refresh")
    except Exception:  # noqa: BLE001
        return
    row = await session.get(RefreshToken, payload["jti"])
    if row is not None and not row.revoked:
        row.revoked = True
        await session.commit()
        await audit.write("auth", "logout", actor=row.user_id)


@router.post("/auth/ws-ticket", response_model=WsTicketResponse)
async def ws_ticket(principal: Principal = Depends(get_principal)) -> WsTicketResponse:
    settings = get_settings()
    ticket = tickets.issue(principal.user_id, principal.role, settings.ws_ticket_ttl_s)
    return WsTicketResponse(ticket=ticket, expires_in=settings.ws_ticket_ttl_s)


@router.get("/auth/me")
async def me(principal: Principal = Depends(get_principal)) -> dict[str, str]:
    return {"user_id": principal.user_id, "role": principal.role}
