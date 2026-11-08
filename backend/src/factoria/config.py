"""Конфигурация сервиса (ТЗ §3.2)."""
from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlparse

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
    access_ttl_min: int = 15
    refresh_ttl_days: int = 7
    ws_ticket_ttl_s: int = 30
    login_max_failures: int = 5
    login_lock_min: int = 5
    twin_history_keep: int = 500

    opcua_endpoint: str = "opc.tcp://localhost:48400"
    opcua_enabled: bool = True
    opcua_security: str = "None"
    opcua_client_cert: str = ""
    opcua_client_key: str = ""
    opcua_server_cert: str = ""
    opcua_allow_remote: bool = False
    opcua_fallback_port: int = 48400

    database_url: str = "sqlite+aiosqlite:///./data/factoria.db"
    tag_history_retention_h: int = 72
    twin_snapshot_minutes: int = 15

    autonomy_max: str = "A1"
    allowed_write_targets: str = "L1,L2,L3"
    allow_external_api: bool = False
    ones_mode: str = "stub"
    ones_http_url: str = ""
    ones_http_user: str = ""
    ones_http_password: str = ""

    llm_provider: str = "none"  # none | deepseek | ollama
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3.5:35b"
    llm_timeout_s: float = 3.0

    @model_validator(mode="after")
    def _guard(self) -> "Settings":
        if self.env != "dev" and self.jwt_secret == DEFAULT_SECRET:
            raise ValueError("JWT_SECRET=dev-secret-change-me запрещён при ENV != dev")
        if self.autonomy_max not in {"A1", "A2"}:
            raise ValueError("AUTONOMY_MAX должен быть A1 или A2")
        if self.ones_mode not in {"stub", "http", "odata"}:
            raise ValueError("ONES_MODE должен быть stub, http или odata")
        if self.ones_mode in {"http", "odata"} and not self.ones_http_url:
            raise ValueError("ONES_MODE=http|odata требует ONES_HTTP_URL")
        if self.llm_provider not in {"none", "deepseek", "ollama"}:
            raise ValueError("LLM_PROVIDER должен быть none, deepseek или ollama")
        if self.llm_timeout_s <= 0:
            raise ValueError("LLM_TIMEOUT_S должен быть > 0")
        if self.tag_history_retention_h <= 0:
            raise ValueError("TAG_HISTORY_RETENTION_H должен быть > 0")
        if self.twin_snapshot_minutes < 0:
            raise ValueError("TWIN_SNAPSHOT_MINUTES не может быть отрицательным")
        if self.opcua_security not in {"None", "Basic256Sha256_Sign", "Basic256Sha256_SignAndEncrypt"}:
            raise ValueError("OPCUA_SECURITY: None или Basic256Sha256_Sign[_AndEncrypt]")
        if self.opcua_security != "None" and not (
            self.opcua_client_cert and self.opcua_client_key and self.opcua_server_cert
        ):
            raise ValueError(
                "OPCUA_SECURITY требует OPCUA_CLIENT_CERT, OPCUA_CLIENT_KEY и OPCUA_SERVER_CERT"
            )

        host = (urlparse(self.opcua_endpoint).hostname or "").lower()
        if host not in {"localhost", "127.0.0.1", "::1"} and not self.opcua_allow_remote:
            raise ValueError(
                "OPCUA_ENDPOINT указывает на удалённый хост: "
                "включите OPCUA_ALLOW_REMOTE=true осознанно (docs/security/ot-baseline.md)"
            )
        return self

    @property
    def allowed_targets(self) -> list[str]:
        return [item.strip() for item in self.allowed_write_targets.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
