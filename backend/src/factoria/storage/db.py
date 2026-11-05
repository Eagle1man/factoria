"""Подключение к БД (ADR-108: SQLite + SQLAlchemy async, PostgreSQL на пилоте)."""
from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from factoria.config import get_settings
from factoria.storage.models import Base


def _prepare_sqlite_dir(url: str) -> None:
    if not url.startswith("sqlite"):
        return
    path = url.split("///")[-1]
    if path and path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)


_settings = get_settings()
_prepare_sqlite_dir(_settings.database_url)

engine = create_async_engine(_settings.database_url, future=True)
session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


async def create_all() -> None:
    """Только для dev/тестов. В остальных средах — Alembic."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
