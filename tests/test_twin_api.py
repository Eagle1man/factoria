"""API истории двойника: доступ, срез, дельта."""
from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient
from sqlalchemy import delete

from factoria.config import Settings
from factoria.main import create_app
from factoria.storage.db import create_all, session_factory
from factoria.storage.models import TwinVersion


def reset_history() -> None:
    async def clear() -> None:
        await create_all()
        async with session_factory() as session:
            await session.execute(delete(TwinVersion))
            await session.commit()

    asyncio.run(clear())


def make_client() -> TestClient:
    settings = Settings(env="test", opcua_enabled=False)
    app = create_app(settings)
    app.state.cache.update("L1.Speed.SP", 100.0)
    app.state.cache.update("L1.Temp.PV", 40.0)
    return TestClient(app)


def login(client: TestClient, username: str = "operator") -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login", json={"username": username, "password": "dev-password"}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_history_requires_token():
    with make_client() as client:
        assert client.get("/api/v1/twin/history").status_code == 401


def test_snapshot_and_history():
    with make_client() as client:
        headers = login(client)
        created = client.post("/api/v1/twin/snapshot", headers=headers)
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["coverage_pct"] <= 100
        assert body["tags_total"] == 21
        assert body["warnings"]

        history = client.get("/api/v1/twin/history", headers=headers).json()
        assert history["count"] >= 1
        assert history["versions"][0]["id"] == body["id"]


def test_snapshot_requires_operator_role():
    with make_client() as client:
        auditor = login(client, "auditor")
        response = client.post("/api/v1/twin/snapshot", headers=auditor)
        assert response.status_code == 403


def test_history_empty_delta_first_time():
    reset_history()
    with make_client() as client:
        headers = login(client)
        client.post("/api/v1/twin/snapshot", headers=headers)
        first = client.get("/api/v1/twin/history?limit=1", headers=headers).json()["versions"][0]
        assert first["delta"]["coverage_pct"] is None
