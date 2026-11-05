"""Роли и права (ТЗ §5.6, §6.4).

Полная матрица автономности — `docs/autonomy-matrix.md` и этап 6.
Здесь только доступ к API на этапе 2.
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from factoria.auth.security import decode_token

ROLES = (
    "project_lead",
    "employee",
    "enterprise_head",
    "technologist",
    "production_specialist",
    "it_admin",
    "auditor",
)

PERMISSIONS: dict[str, set[str]] = {
    "read": set(ROLES),
    "audit_read": {"project_lead", "enterprise_head", "it_admin", "auditor"},
    "operator": {"production_specialist", "technologist"},
}

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    user_id: str
    role: str

    def can(self, permission: str) -> bool:
        return self.role in PERMISSIONS.get(permission, set())


def get_principal(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> Principal:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="требуется токен")
    try:
        payload = decode_token(creds.credentials)
    except Exception as exc:  # noqa: BLE001 - любая ошибка JWT = 401
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=f"токен не принят: {exc}")
    return Principal(user_id=payload["sub"], role=payload["role"])


def require(permission: str):
    def dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if not principal.can(permission):
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="роль не имеет права")
        return principal

    return dependency
