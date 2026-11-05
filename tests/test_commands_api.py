"""Команды: идемпотентность, отказы с кодами, подтверждение и исполнение."""
from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from factoria.api import commands as commands_api
from factoria.config import Settings
from factoria.main import create_app


def make_client(*, autonomy: str = "A1", with_values: bool = True) -> TestClient:
    settings = Settings(env="test", opcua_enabled=False, autonomy_max=autonomy)
    app = create_app(settings)
    if with_values:
        app.state.cache.update("L1.Speed.SP", 0.0)
        app.state.cache.update("L1.Temp.PV", 40.0)
        app.state.cache.update("L1.Load.Pct", 30.0)
    return TestClient(app)


def login(client: TestClient, username: str = "operator") -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login", json={"username": username, "password": "dev-password"}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def payload(**overrides) -> dict:
    base = {
        "command_id": str(uuid4()),
        "type": "set_setpoint",
        "target": {"line_id": "L1"},
        "params": {"setpoint_value": 300},
        "requested_by": {"kind": "agent", "id": "prod#sess-1"},
        "correlation_id": str(uuid4()),
    }
    base.update(overrides)
    return base


def test_submit_creates_awaiting_approval():
    with make_client() as client:
        headers = login(client)
        response = client.post("/api/v1/commands", json=payload(), headers=headers)
        assert response.status_code == 202, response.text
        body = response.json()
        assert body["status"] == "AWAITING_APPROVAL"
        assert body["autonomy_level"] == "A1"
        assert body["duplicate"] is False


def test_duplicate_command_is_idempotent():
    with make_client() as client:
        headers = login(client)
        body = payload()
        first = client.post("/api/v1/commands", json=body, headers=headers)
        second = client.post("/api/v1/commands", json=body, headers=headers)
        assert first.status_code == 202
        assert second.status_code == 202
        assert second.json()["duplicate"] is True
        assert second.json()["status"] == first.json()["status"]


def test_schema_error_returns_code():
    with make_client() as client:
        headers = login(client)
        response = client.post(
            "/api/v1/commands", json=payload(params={}), headers=headers
        )
        assert response.status_code == 422
        assert response.json()["code"] == "SCHEMA_001"
        assert response.json()["stage"] == "schema_check"


def test_unknown_line_returns_range_code():
    with make_client() as client:
        headers = login(client)
        response = client.post(
            "/api/v1/commands", json=payload(target={"line_id": "L9"}), headers=headers
        )
        assert response.status_code == 422
        assert response.json()["code"] == "RANGE_001"


def test_delta_interlock_returns_code():
    with make_client() as client:
        headers = login(client)
        response = client.post(
            "/api/v1/commands",
            json=payload(params={"setpoint_value": 900}),
            headers=headers,
        )
        assert response.status_code == 422
        assert response.json()["code"] == "INTERLOCK_001"


def test_missing_data_blocks_command():
    with make_client(with_values=False) as client:
        headers = login(client)
        response = client.post("/api/v1/commands", json=payload(), headers=headers)
        assert response.status_code == 422
        assert response.json()["code"] == "DATA_STALE"


def test_approve_executes(monkeypatch):
    async def fake_dispatch(**kwargs):
        return True, "EXECUTED"

    monkeypatch.setattr(commands_api, "dispatch_command", fake_dispatch)

    with make_client() as client:
        headers = login(client)
        created = client.post("/api/v1/commands", json=payload(), headers=headers).json()
        command_id = created["command_id"]

        response = client.post(
            f"/api/v1/commands/{command_id}/approve",
            json={"version": 1, "comment": "проверено"},
            headers=headers,
        )
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "EXECUTED"

        repeat = client.post("/api/v1/commands", json=payload(command_id=command_id), headers=headers)
        assert repeat.json()["status"] == "EXECUTED"
        assert repeat.json()["duplicate"] is True


def test_approve_requires_operator_role():
    with make_client() as client:
        operator = login(client)
        auditor = login(client, "auditor")
        command_id = client.post(
            "/api/v1/commands", json=payload(), headers=operator
        ).json()["command_id"]
        response = client.post(
            f"/api/v1/commands/{command_id}/approve",
            json={"version": 1},
            headers=auditor,
        )
        assert response.status_code == 403


def test_reject_requires_reason():
    with make_client() as client:
        headers = login(client)
        command_id = client.post(
            "/api/v1/commands", json=payload(), headers=headers
        ).json()["command_id"]
        short = client.post(
            f"/api/v1/commands/{command_id}/reject", json={"version": 1, "reason": "x"}, headers=headers
        )
        assert short.status_code == 422
        ok = client.post(
            f"/api/v1/commands/{command_id}/reject",
            json={"version": 1, "reason": "неверная смена"},
            headers=headers,
        )
        assert ok.status_code == 200
        assert ok.json()["status"] == "REJECTED"


def test_stale_version_rejected():
    with make_client() as client:
        headers = login(client)
        command_id = client.post(
            "/api/v1/commands", json=payload(), headers=headers
        ).json()["command_id"]
        response = client.post(
            f"/api/v1/commands/{command_id}/reject",
            json={"version": 99, "reason": "устаревшая карточка"},
            headers=headers,
        )
        assert response.status_code == 409


def test_orders_are_read_only_stub():
    with make_client() as client:
        headers = login(client)
        response = client.get("/api/v1/orders", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "stub"
        assert len(body["orders"]) == 5
        first = body["orders"][0]["order_id"]
        one = client.get(f"/api/v1/orders/{first}", headers=headers)
        assert one.status_code == 200
        assert one.json()["order_id"] == first
        missing = client.get("/api/v1/orders/NOPE", headers=headers)
        assert missing.status_code == 404


def test_debug_orders_disabled_outside_dev():
    with make_client() as client:
        headers = login(client)
        response = client.post(
            "/api/v1/debug/orders",
            json={
                "order_id": "ORD-9001",
                "product": "Тест",
                "qty": 1,
                "priority": "normal",
                "due_date": "2026-12-01",
                "spec_id": "SPEC-01",
            },
            headers=headers,
        )
        assert response.status_code == 404

def test_expired_command_leaves_queue():
    import asyncio
    from datetime import datetime, timedelta, timezone

    from factoria.storage.db import session_factory
    from factoria.storage.models import Command

    with make_client() as client:
        headers = login(client)
        command_id = client.post(
            "/api/v1/commands", json=payload(), headers=headers
        ).json()["command_id"]

        async def expire() -> None:
            async with session_factory() as session:
                command = await session.get(Command, command_id)
                command.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
                await session.commit()

        asyncio.run(expire())

        listed = client.get(
            "/api/v1/commands?status=AWAITING_APPROVAL", headers=headers
        ).json()
        assert command_id not in [item["command_id"] for item in listed["commands"]]

        detail = client.get(f"/api/v1/commands/{command_id}", headers=headers).json()
        assert detail["status"] == "EXPIRED"

        approve = client.post(
            f"/api/v1/commands/{command_id}/approve", json={"version": 1}, headers=headers
        )
        assert approve.status_code == 409

def test_a2_executes_without_approval(monkeypatch):
    async def fake_dispatch(**kwargs):
        return True, "EXECUTED"

    monkeypatch.setattr(commands_api, "dispatch_command", fake_dispatch)
    settings = Settings(env="test", opcua_enabled=False, autonomy_max="A2")
    app = create_app(settings)
    app.state.cache.update("L1.Speed.SP", 340.0)
    app.state.cache.update("L1.Temp.PV", 40.0)
    app.state.cache.update("L1.Load.Pct", 30.0)

    with TestClient(app) as client:
        headers = login(client)
        response = client.post(
            "/api/v1/commands",
            json=payload(params={"setpoint_value": 380}),
            headers=headers,
        )
        assert response.status_code == 202, response.text
        body = response.json()
        assert body["status"] == "EXECUTED"
        assert body["autonomy_level"] == "A2"

        detail = client.get(f"/api/v1/commands/{body['command_id']}", headers=headers).json()
        assert detail["status"] == "EXECUTED"


def test_a2_corridor_keeps_approval_for_large_step(monkeypatch):
    async def fake_dispatch(**kwargs):
        return True, "EXECUTED"

    monkeypatch.setattr(commands_api, "dispatch_command", fake_dispatch)
    settings = Settings(env="test", opcua_enabled=False, autonomy_max="A2")
    app = create_app(settings)
    app.state.cache.update("L1.Speed.SP", 340.0)
    app.state.cache.update("L1.Temp.PV", 40.0)
    app.state.cache.update("L1.Load.Pct", 30.0)

    with TestClient(app) as client:
        headers = login(client)
        response = client.post(
            "/api/v1/commands",
            json=payload(params={"setpoint_value": 500}),
            headers=headers,
        )
        assert response.status_code == 202
        assert response.json()["status"] == "AWAITING_APPROVAL"
        assert response.json()["autonomy_level"] == "A1"
