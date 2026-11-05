"""Проверки конфигурации: защита от небезопасного старта (OT-baseline §1.1, §2.3)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from factoria.config import Settings


def test_local_endpoint_allowed_by_default():
    settings = Settings(env="test", opcua_endpoint="opc.tcp://127.0.0.1:48400")
    assert settings.opcua_allow_remote is False


def test_remote_endpoint_rejected_without_flag():
    with pytest.raises(ValidationError) as error:
        Settings(env="test", opcua_endpoint="opc.tcp://10.20.30.40:4840")
    assert "OPCUA_ALLOW_REMOTE" in str(error.value)


def test_remote_endpoint_allowed_with_flag():
    settings = Settings(
        env="test",
        opcua_endpoint="opc.tcp://10.20.30.40:4840",
        opcua_allow_remote=True,
    )
    assert settings.opcua_allow_remote is True


def test_dev_secret_rejected_outside_dev():
    with pytest.raises(ValidationError) as error:
        Settings(env="pilot", jwt_secret="dev-secret-change-me")
    assert "JWT_SECRET" in str(error.value)


def test_production_secret_accepted():
    settings = Settings(env="pilot", jwt_secret="a" * 40)
    assert settings.env == "pilot"


def test_bad_autonomy_rejected():
    with pytest.raises(ValidationError):
        Settings(env="dev", autonomy_max="A3")


def test_retention_must_be_positive():
    with pytest.raises(ValidationError):
        Settings(env="dev", tag_history_retention_h=0)
