"""Dev-пользователи (только ENV=dev). Пароль не хардкодится в коде репозитория."""
from __future__ import annotations

import logging
import os
from uuid import uuid4

from sqlalchemy import select

from factoria.auth.security import hash_password
from factoria.config import get_settings
from factoria.storage.db import session_factory
from factoria.storage.models import User

LOG = logging.getLogger("seed")

DEV_USERS = (
    ("operator", "production_specialist"),
    ("technologist", "technologist"),
    ("auditor", "auditor"),
    ("lead", "project_lead"),
)


async def ensure_dev_users() -> int:
    settings = get_settings()
    if settings.env not in {"dev", "test"}:
        return 0
    password = os.environ.get("DEV_DEFAULT_PASSWORD", "dev-password")
    created = 0
    async with session_factory() as session:
        for username, role in DEV_USERS:
            if await session.scalar(select(User).where(User.username == username)):
                continue
            session.add(
                User(
                    id=str(uuid4()),
                    username=username,
                    password_hash=hash_password(password),
                    role=role,
                )
            )
            created += 1
        await session.commit()
    if created:
        LOG.warning(
            "созданы dev-пользователи: %s (пароль из DEV_DEFAULT_PASSWORD, по умолчанию dev-*)",
            ", ".join(u for u, _ in DEV_USERS),
        )
    return created
