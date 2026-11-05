"""Смоук этапа 6: A2 исполняется сам, WS присылает command_status."""
import asyncio
import json
from uuid import uuid4

import httpx
import websockets

BASE = "http://127.0.0.1:8010"
WS = "ws://127.0.0.1:8010/ws"


def submit(client: httpx.Client, headers: dict, line: str, setpoint: int) -> dict:
    body = {
        "command_id": str(uuid4()),
        "type": "set_setpoint",
        "target": {"line_id": line},
        "params": {"setpoint_value": setpoint},
        "requested_by": {"kind": "agent", "id": "production#stage6"},
        "correlation_id": str(uuid4()),
        "evidence": ["tool-call-1"],
    }
    response = client.post("/api/v1/commands", json=body, headers=headers)
    print(f"submit {line} -> {setpoint}: {response.status_code} {response.json()}")
    return response.json()


async def main() -> None:
    with httpx.Client(base_url=BASE, timeout=15) as client:
        login = client.post(
            "/api/v1/auth/login", json={"username": "operator", "password": "dev-password"}
        )
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # ждём, пока опрос заберёт нулевую уставку линии L2
        await asyncio.sleep(1.0)

        async with websockets.connect(f"{WS}?token={token}") as ws:
            await ws.send(
                json.dumps(
                    {
                        "type": "subscribe",
                        "tags": ["L2.Speed.SP"],
                        "delta_only": True,
                        "min_interval_ms": 100,
                    }
                )
            )
            snapshot = json.loads(await ws.recv())
            print("ws snapshot seq:", snapshot.get("seq"))

            safe = submit(client, headers, "L2", 50)  # delta 50 <= 60, target <= 400
            print("A2 status:", safe["status"], "autonomy:", safe["autonomy_level"])

            message = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            print("ws event:", message["type"], message.get("status"), message.get("autonomy_level"))

            risky = submit(client, headers, "L2", 500)  # target > 400 -> A1
            print("A1 status:", risky["status"], "autonomy:", risky["autonomy_level"])


asyncio.run(main())
