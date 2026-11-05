"""Дымовой тест этапа 2: backend + эмулятор + WS. Запускается вручную, не pytest."""
import asyncio
import json

import httpx
import websockets
from asyncua import Client

BASE = "http://127.0.0.1:8010"
WS = "ws://127.0.0.1:8010/ws"
OPCUA = "opc.tcp://127.0.0.1:48400"


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE, timeout=10) as c:
        health = (await c.get("/api/v1/health")).json()
        print("health:", health["status"], "| tags:", health["tags"], "| opcua:", health["sources"]["opcua"]["state"])

        login = await c.post("/api/v1/auth/login", json={"username": "operator", "password": "dev-password"})
        body = login.json()
        token = body["access_token"]
        print("login:", login.status_code, "| role:", body["role"])
        headers = {"Authorization": f"Bearer {token}"}

        equipment = (await c.get("/api/v1/equipment", headers=headers)).json()
        print("lines:", [(line["line_id"], line["speed_pv"], line["quality"]) for line in equipment["lines"]])

        state = (await c.get("/api/v1/equipment/L1/state", headers=headers)).json()
        print("L1 tags:", len(state["values"]), "| snapshot_ts:", state["snapshot_ts"])

        unauth = await c.get("/api/v1/equipment")
        print("no token ->", unauth.status_code)
        forbidden = await c.get("/api/v1/audit", headers=headers)
        print("audit as operator ->", forbidden.status_code)

    async with websockets.connect(f"{WS}?token={token}") as ws:
        await ws.send(json.dumps({
            "type": "subscribe",
            "tags": ["L1.Speed.PV", "L1.Temp.PV", "L1.Running"],
            "delta_only": True,
            "min_interval_ms": 100,
        }))
        snapshot = json.loads(await ws.recv())
        print("ws snapshot:", snapshot["type"], "| seq:", snapshot["seq"],
              "| q:", snapshot["values"]["L1.Speed.PV"]["q"])

        # меняем состояние через сам эмулятор (method-ноды), чтобы пошли дельты
        async with Client(OPCUA) as client:
            index = await client.get_namespace_index("urn:mfg:emulator")
            l1 = client.get_node(f"ns={index};s=L1")
            await l1.call_method(client.get_node(f"ns={index};s=L1.StartLine").nodeid)
            await l1.call_method(client.get_node(f"ns={index};s=L1.SetSpeed").nodeid, 300.0)

        for _ in range(3):
            message = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            print("ws next:", message["type"], "| seq:", message.get("seq"),
                  "| values:", list(message.get("values", {}))[:2])


asyncio.run(main())
