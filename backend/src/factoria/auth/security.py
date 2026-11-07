"""Пароли и JWT (ТЗ §5.6)."""
from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt

from factoria.config import get_settings

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
DKLEN = 32


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(
        password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=DKLEN
    )
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    digest = hashlib.scrypt(
        password.encode(),
        salt=bytes.fromhex(salt_hex),
        n=int(n),
        r=int(r),
        p=int(p),
        dklen=len(bytes.fromhex(digest_hex)),
    )
    return hmac.compare_digest(digest.hex(), digest_hex)


def create_token(user_id: str, role: str, ttl_min: int | None = None) -> tuple[str, int]:
    settings = get_settings()
    ttl = ttl_min if ttl_min is not None else settings.jwt_ttl_min
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ttl)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token, ttl * 60


def create_access(user_id: str, role: str) -> tuple[str, int]:
    settings = get_settings()
    return create_token(user_id, role, ttl_min=settings.access_ttl_min)


def create_refresh(user_id: str, ttl_days: int | None = None) -> tuple[str, str, datetime]:
    settings = get_settings()
    days = ttl_days if ttl_days is not None else settings.refresh_ttl_days
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=days)
    jti = str(uuid4())
    payload: dict[str, Any] = {
        "sub": user_id,
        "type": "refresh",
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token, jti, expires


def decode_token(token: str, expected_type: str | None = "access") -> dict[str, Any]:
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    token_type = payload.get("type")
    if expected_type is not None and token_type != expected_type:
        raise jwt.InvalidTokenError(f"ожидался токен {expected_type}, получен {token_type}")
    return payload
