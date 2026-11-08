"""LLM-провайдер: статус без утечки секретов, моки сети."""
from __future__ import annotations

import json

import httpx
import pytest
from factoria.config import Settings
from factoria.llm.provider import llm_status
from factoria.main import create_app
from fastapi.testclient import TestClient


@pytest.mark.anyio
async def test_llm_none():
    status = await llm_status(Settings(llm_provider="none"))
    assert status["provider"] == "none"
    assert status["reachable"] is False


@pytest.mark.anyio
async def test_deepseek_disabled_without_external_or_key():
    status = await llm_status(
        Settings(llm_provider="deepseek", allow_external_api=False, deepseek_api_key="secret")
    )
    assert status["provider"] == "deepseek"
    assert status["reachable"] is False
    assert "secret" not in json.dumps(status, ensure_ascii=False)
    status = await llm_status(Settings(llm_provider="deepseek", allow_external_api=True, deepseek_api_key=""))
    assert status["detail"] == "missing_api_key"


@pytest.mark.anyio
async def test_ollama_reachable_and_model_present(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/tags"
        return httpx.Response(200, json={"models": [{"name": "qwen3.5:35b"}]})

    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient

    def make_client(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr("factoria.llm.provider.httpx.AsyncClient", make_client)
    status = await llm_status(Settings(llm_provider="ollama", ollama_model="qwen3.5:35b"))
    assert status["reachable"] is True
    assert status.get("model_present") is True


@pytest.mark.anyio
async def test_ollama_unreachable(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient

    def make_client(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr("factoria.llm.provider.httpx.AsyncClient", make_client)
    status = await llm_status(Settings(llm_provider="ollama"))
    assert status["reachable"] is False
    assert status["detail"] == "unreachable"


def test_health_contains_llm_without_secrets():
    client = TestClient(
        create_app(
            Settings(
                env="test",
                opcua_enabled=False,
                llm_provider="deepseek",
                deepseek_api_key="TOPSECRET",
                allow_external_api=False,
            )
        )
    )
    body = client.get("/api/v1/health").json()
    assert "llm" in body
    assert body["llm"]["provider"] == "deepseek"
    dumped = json.dumps(body, ensure_ascii=False)
    assert "TOPSECRET" not in dumped
    assert "deepseek_api_key" not in dumped
