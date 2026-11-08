"""API каталога шаблонов (интеграция спеки Stitch, read-only)."""
from __future__ import annotations

from factoria.config import Settings
from factoria.main import create_app
from factoria.templates.catalog import TEMPLATES, get_template
from fastapi.testclient import TestClient


def make_client() -> TestClient:
    return TestClient(create_app(Settings(env="test", opcua_enabled=False)))


def login(client: TestClient, username: str = "operator") -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login", json={"username": username, "password": "dev-password"}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_catalog_has_required_templates():
    assert {"cnc_metal", "drone_assembly", "cubesat_satellite", "battery_gigafactory"} <= set(
        TEMPLATES
    )
    cnc = get_template("cnc_metal")
    assert cnc is not None
    assert cnc.bottleneck_line_id == "L1"
    assert cnc.stations


def test_list_templates():
    with make_client() as client:
        headers = login(client)
        body = client.get("/api/v1/templates", headers=headers).json()
        ids = {item["id"] for item in body["templates"]}
        assert "cnc_metal" in ids
        assert body["count"] >= 4


def test_get_template_detail_and_404():
    with make_client() as client:
        headers = login(client)
        body = client.get("/api/v1/templates/drone_assembly", headers=headers).json()
        assert body["bottleneck_node_id"] == "ST-04"
        assert any(s["status"] == "BOTTLENECK" for s in body["stations"])
        assert client.get("/api/v1/templates/nope", headers=headers).status_code == 404


def test_templates_require_auth():
    with make_client() as client:
        assert client.get("/api/v1/templates").status_code in {401, 403}
