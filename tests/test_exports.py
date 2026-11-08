"""Экспорт 1C/OPC UA из реального реестра (read-only)."""
from __future__ import annotations

from xml.etree.ElementTree import fromstring

from factoria.config import Settings
from factoria.main import create_app
from fastapi.testclient import TestClient


def make_client() -> TestClient:
    return TestClient(create_app(Settings(env="test", opcua_enabled=False)))


def login(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login", json={"username": "operator", "password": "dev-password"}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_export_1c_enterprise():
    with make_client() as client:
        headers = login(client)
        res = client.get("/api/v1/exports/1c-enterprise.xml?template_id=cnc_metal", headers=headers)
        assert res.status_code == 200
        assert "application/xml" in res.headers["content-type"]
        root = fromstring(res.content)
        ns = {"e": "http://v8.1c.ru/edi/edi_stnd/EnterpriseData/1.14"}
        assert root.findtext("e:Header/e:FormatVersion", namespaces=ns) == "1.14"
        assert "ВТУЛКА" in (root.findtext(".//e:Номенклатура", namespaces=ns) or "")
        body = res.text
        assert "ТолькоЧтение" in body or "read-only" in body


def test_export_nodeset2_from_registry():
    with make_client() as client:
        headers = login(client)
        res = client.get("/api/v1/exports/opcua-nodeset2.xml", headers=headers)
        assert res.status_code == 200
        root = fromstring(res.content)
        ns = {"u": "http://opcfoundation.org/UA/2011/03/UANodeSet.xsd"}
        uri = root.findtext("u:NamespaceUris/u:Uri", namespaces=ns)
        assert uri == "urn:mfg:emulator"
        vars_ = root.findall(".//u:UAVariable", namespaces=ns)
        assert len(vars_) == 21  # 3 lines * 7 tags
        methods = root.findall(".//u:UAMethod", namespaces=ns)
        assert len(methods) == 15  # 5 methods * 3 lines


def test_exports_require_auth():
    with make_client() as client:
        assert client.get("/api/v1/exports/1c-enterprise.xml").status_code in {401, 403}
