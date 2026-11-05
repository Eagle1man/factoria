"""Аутентификация (ТЗ §5.6): operator_id всегда из токена."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from factoria.audit.storage import audit
from factoria.auth.rbac import Principal, get_principal
from factoria.auth.security import create_token, verify_password
from factoria.storage.db import get_session
from factoria.storage.models import User

router = APIRouter(prefix="/api/v1", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    expires_in: int


@router.post("/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_session)) -> TokenResponse:
    user = await session.scalar(select(User).where(User.username == body.username))
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        await audit.write(
            "auth", "login_failed", actor=body.username, payload={"reason": "bad_credentials"}
        )
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="неверные учётные данные")

    token, expires_in = create_token(user.id, user.role)
    await audit.write("auth", "login", actor=user.id, payload={"role": user.role})
    return TokenResponse(access_token=token, role=user.role, expires_in=expires_in)


@router.get("/auth/me")
async def me(principal: Principal = Depends(get_principal)) -> dict[str, str]:
    return {"user_id": principal.user_id, "role": principal.role}
