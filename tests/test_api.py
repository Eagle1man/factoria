from __future__ import annotations

from fastapi.testclient import TestClient

from factoria.config import Settings
from factoria.main import create_app


def make_client() -> TestClient:
    settings = Settings(env="test", opcua_enabled=False)
    app = create_app(settings)
    app.state.cache.update("L1.Speed.PV", 700.0)
    app.state.cache.update("L1.Temp.PV", 62.0)
    return TestClient(app)


def login(client: TestClient, username: str = "operator") -> str:
    response = client.post(
        "/api/v1/auth/login", json={"username": username, "password": "dev-password"}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_health_open_and_counts_tags():
    with make_client() as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        body = response.json()
        assert body["tags"]["total"] == 21
        assert body["sources"]["opcua"]["state"] in {"unknown", "down", "connected"}


def test_login_and_me():
    with make_client() as client:
        token = login(client)
        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["role"] == "production_specialist"


def test_login_rejects_bad_password():
    with make_client() as client:
        response = client.post(
            "/api/v1/auth/login", json={"username": "operator", "password": "nope"}
        )
        assert response.status_code == 401


def test_equipment_requires_token():
    with make_client() as client:
        assert client.get("/api/v1/equipment").status_code == 401


def test_equipment_lists_three_lines():
    with make_client() as client:
        token = login(client)
        response = client.get("/api/v1/equipment", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        lines = response.json()["lines"]
        assert [line["line_id"] for line in lines] == ["L1", "L2", "L3"]
        assert lines[0]["speed_pv"] == 700.0
        assert lines[0]["quality"] == "GOOD"


def test_line_state_and_404():
    with make_client() as client:
        token = login(client)
        headers = {"Authorization": f"Bearer {token}"}
        ok = client.get("/api/v1/equipment/L1/state", headers=headers)
        assert ok.status_code == 200
        assert len(ok.json()["values"]) == 7
        assert client.get("/api/v1/equipment/L9/state", headers=headers).status_code == 404


def test_audit_rbac():
    with make_client() as client:
        operator = login(client, "operator")
        auditor = login(client, "auditor")
        assert client.get(
            "/api/v1/audit", headers={"Authorization": f"Bearer {operator}"}
        ).status_code == 403
        response = client.get(
            "/api/v1/audit", headers={"Authorization": f"Bearer {auditor}"}
        )
        assert response.status_code == 200
        kinds = {event["kind"] for event in response.json()["events"]}
        assert "auth" in kinds


def test_ws_snapshot_and_resume():
    with make_client() as client:
        token = login(client)
        with client.websocket_connect(f"/ws?token={token}") as ws:
            ws.send_json(
                {"type": "subscribe", "tags": ["L1.Speed.PV"], "delta_only": True,
                 "min_interval_ms": 0}
            )
            snapshot = ws.receive_json()
            assert snapshot["type"] == "snapshot"
            assert snapshot["values"]["L1.Speed.PV"]["v"] == 700.0

            ws.send_json({"type": "resume", "last_seq": 0})
            resumed = ws.receive_json()
            assert resumed["type"] in {"resumed", "snapshot"}


def test_ws_requires_valid_token():
    from starlette.websockets import WebSocketDisconnect

    with make_client() as client:
        try:
            with client.websocket_connect("/ws?token=garbage") as ws:
                ws.receive()
        except WebSocketDisconnect as exc:
            assert exc.code == 4401
        else:
            raise AssertionError("соединение без валидного токена не должно открываться")
