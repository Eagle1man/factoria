"""Безопасность: refresh, отзыв, лимит входа, WS-тикеты, экспорт аудита."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from factoria.auth.limiter import limiter
from factoria.auth.tickets import tickets
from factoria.config import Settings
from factoria.main import create_app


def make_client() -> TestClient:
    return TestClient(create_app(Settings(env="test", opcua_enabled=False)))


def login(client: TestClient, username: str = "operator", password: str = "dev-password") -> dict:
    response = client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_login_returns_refresh_token():
    with make_client() as client:
        body = login(client)
        assert body["access_token"]
        assert body["refresh_token"]
        assert body["expires_in"] > 0


def test_refresh_rotates_and_old_is_revoked():
    with make_client() as client:
        first = login(client)
        refreshed = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
        )
        assert refreshed.status_code == 200, refreshed.text
        second = refreshed.json()
        assert second["refresh_token"] != first["refresh_token"]

        reuse = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
        )
        assert reuse.status_code == 401


def test_logout_revokes_refresh():
    with make_client() as client:
        body = login(client)
        out = client.post("/api/v1/auth/logout", json={"refresh_token": body["refresh_token"]})
        assert out.status_code == 204
        again = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": body["refresh_token"]}
        )
        assert again.status_code == 401


def test_login_rate_limit():
    limiter.reset("operator")
    try:
        with make_client() as client:
            for _ in range(5):
                bad = client.post(
                    "/api/v1/auth/login",
                    json={"username": "operator", "password": "wrong"},
                )
                assert bad.status_code == 401
            locked = client.post(
                "/api/v1/auth/login",
                json={"username": "operator", "password": "dev-password"},
            )
            assert locked.status_code == 429
    finally:
        limiter.reset("operator")


def test_ws_ticket_is_single_use():
    ticket = tickets.issue("user-1", "auditor", 30)
    assert tickets.consume(ticket) is not None
    assert tickets.consume(ticket) is None


def test_ws_ticket_endpoint_requires_auth():
    with make_client() as client:
        assert client.post("/api/v1/auth/ws-ticket").status_code == 401


def test_audit_export_ndjson():
    with make_client() as client:
        auditor = login(client, "auditor")
        headers = {"Authorization": f"Bearer {auditor['access_token']}"}
        response = client.get("/api/v1/audit/export?limit=5", headers=headers)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/x-ndjson")
        lines = [line for line in response.text.splitlines() if line.strip()]
        assert lines
        import json

        assert "kind" in json.loads(lines[0])


def test_audit_export_forbidden_for_operator():
    with make_client() as client:
        operator = login(client)
        headers = {"Authorization": f"Bearer {operator['access_token']}"}
        assert client.get("/api/v1/audit/export", headers=headers).status_code == 403
