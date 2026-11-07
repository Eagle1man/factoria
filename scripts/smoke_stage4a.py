"""Дымовой тест этапа 4a: команда → подтверждение → исполнение → аудит."""
import sys
from uuid import uuid4

import httpx

BASE = "http://127.0.0.1:8010"


def main() -> int:
    with httpx.Client(base_url=BASE, timeout=15) as client:
        login = client.post(
            "/api/v1/auth/login", json={"username": "operator", "password": "dev-password"}
        )
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("login:", login.status_code, login.json()["role"])

        print("orders:", client.get("/api/v1/orders", headers=headers).json()["source"],
              len(client.get("/api/v1/orders", headers=headers).json()["orders"]))

        command_id = str(uuid4())
        body = {
            "command_id": command_id,
            "type": "set_setpoint",
            "target": {"line_id": "L1"},
            "params": {"setpoint_value": 300},
            "requested_by": {"kind": "agent", "id": "prod#sess-1"},
            "correlation_id": str(uuid4()),
            "evidence": ["call-1"],
        }
        created = client.post("/api/v1/commands", json=body, headers=headers)
        print("submit:", created.status_code, created.json())

        duplicate = client.post("/api/v1/commands", json=body, headers=headers)
        print("duplicate:", duplicate.status_code, duplicate.json())

        bad = dict(body, command_id=str(uuid4()), params={"setpoint_value": 900})
        bad["correlation_id"] = str(uuid4())
        refused = client.post("/api/v1/commands", json=bad, headers=headers)
        print("interlock:", refused.status_code, refused.json())

        approved = client.post(
            f"/api/v1/commands/{command_id}/approve",
            json={"version": 1, "comment": "проверено"},
            headers=headers,
        )
        print("approve:", approved.status_code, approved.json())

        final = client.get(f"/api/v1/commands/{command_id}", headers=headers)
        print("state:", final.status_code, final.json()["status"])

        import time

        time.sleep(1.2)  # дать опросу тегов забрать новое значение
        line = client.get("/api/v1/equipment/L1/state", headers=headers).json()
        print("L1.Speed.SP:", line["values"]["L1.Speed.SP"]["v"], "q:", line["values"]["L1.Speed.SP"]["q"])

        auditor = client.post(
            "/api/v1/auth/login", json={"username": "auditor", "password": "dev-password"}
        ).json()["access_token"]
        events = client.get(
            "/api/v1/audit?limit=5", headers={"Authorization": f"Bearer {auditor}"}
        ).json()["events"]
        print("audit:", [(event["kind"], event["action"]) for event in events[:4]])

    return 0


if __name__ == "__main__":
    sys.exit(main())
