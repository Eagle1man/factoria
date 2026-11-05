"""Конфигурация сервиса (ТЗ §3.2)."""
from __future__ import annotations

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET = "dev-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    env: str = "dev"

    jwt_secret: str = DEFAULT_SECRET
    jwt_ttl_min: int = 60

    opcua_endpoint: str = "opc.tcp://localhost:48400"
    opcua_enabled: bool = True
    opcua_fallback_port: int = 48400

    database_url: str = "sqlite+aiosqlite:///./data/factoria.db"
    tag_history_retention_h: int = 72

    autonomy_max: str = "A1"
    allow_external_api: bool = False
    ones_mode: str = "stub"

    @model_validator(mode="after")
    def _guard(self) -> "Settings":
        if self.env != "dev" and self.jwt_secret == DEFAULT_SECRET:
            raise ValueError("JWT_SECRET=dev-secret-change-me запрещён при ENV != dev")
        if self.autonomy_max not in {"A1", "A2"}:
            raise ValueError("AUTONOMY_MAX должен быть A1 или A2")
        if self.tag_history_retention_h <= 0:
            raise ValueError("TAG_HISTORY_RETENTION_H должен быть > 0")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
