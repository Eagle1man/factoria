"""API экспериментов: запуск, список, сравнение, права."""
from __future__ import annotations

from fastapi.testclient import TestClient

from factoria.config import Settings
from factoria.main import create_app


def make_client() -> TestClient:
    return TestClient(create_app(Settings(env="test", opcua_enabled=False)))


def login(client: TestClient, username: str = "operator") -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login", json={"username": username, "password": "dev-password"}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_scenarios_listed():
    with make_client() as client:
        headers = login(client)
        body = client.get("/api/v1/sim/scenarios", headers=headers).json()
        names = {item["name"] for item in body["scenarios"]}
        assert {"nominal", "overload", "hot_start", "noisy"} <= names


def test_run_requires_operator_role():
    with make_client() as client:
        auditor = login(client, "auditor")
        response = client.post(
            "/api/v1/sim/runs",
            json={"scenario": "nominal", "seed": 1, "horizon_s": 60},
            headers=auditor,
        )
        assert response.status_code == 403


def test_run_and_reproducibility():
    with make_client() as client:
        headers = login(client)
        payload = {"scenario": "noisy", "seed": 7, "horizon_s": 60}
        first = client.post("/api/v1/sim/runs", json=payload, headers=headers)
        second = client.post("/api/v1/sim/runs", json=payload, headers=headers)
        assert first.status_code == 201, first.text
        assert second.status_code == 201
        assert first.json()["repro_hash"] == second.json()["repro_hash"]
        assert first.json()["metrics"]["output_index"] > 0


def test_compare_route_not_shadowed_by_id():
    with make_client() as client:
        headers = login(client)
        first = client.post(
            "/api/v1/sim/runs",
            json={"scenario": "nominal", "seed": 1, "horizon_s": 60},
            headers=headers,
        ).json()
        second = client.post(
            "/api/v1/sim/runs",
            json={"scenario": "overload", "seed": 1, "horizon_s": 180},
            headers=headers,
        ).json()

        response = client.get(
            f"/api/v1/sim/runs/compare?a={first['id']}&b={second['id']}", headers=headers
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert set(body["delta"]) == {"output_index", "max_temp", "avg_load", "uptime_pct", "alarms"}
        assert body["delta"]["max_temp"] > 0
        assert body["same_repro"] is False


def test_list_and_get_run():
    with make_client() as client:
        headers = login(client)
        created = client.post(
            "/api/v1/sim/runs",
            json={"scenario": "nominal", "seed": 3, "horizon_s": 30},
            headers=headers,
        ).json()
        listed = client.get("/api/v1/sim/runs?limit=5", headers=headers).json()
        assert listed["count"] >= 1
        assert listed["runs"][0]["id"] == created["id"]

        one = client.get(f"/api/v1/sim/runs/{created['id']}", headers=headers)
        assert one.status_code == 200
        assert client.get("/api/v1/sim/runs/999999", headers=headers).status_code == 404


def test_invalid_scenario_returns_422():
    with make_client() as client:
        headers = login(client)
        response = client.post(
            "/api/v1/sim/runs",
            json={"scenario": "nope", "seed": 1, "horizon_s": 60},
            headers=headers,
        )
        assert response.status_code == 422
