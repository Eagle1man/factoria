"""Смоук безопасности: тикет WS, refresh, экспорт аудита."""
import asyncio
import json

import httpx
import websockets

BASE = "http://127.0.0.1:8010"
WS = "ws://127.0.0.1:8010/ws"


async def main() -> None:
    with httpx.Client(base_url=BASE, timeout=15) as client:
        login = client.post(
            "/api/v1/auth/login", json={"username": "operator", "password": "dev-password"}
        ).json()
        access = login["access_token"]
        refresh = login["refresh_token"]
        print("login: access+refresh ok")

        headers = {"Authorization": f"Bearer {access}"}
        ticket = client.post("/api/v1/auth/ws-ticket", headers=headers).json()["ticket"]
        print("ws ticket issued")

        async with websockets.connect(f"{WS}?ticket={ticket}") as ws:
            await ws.send(json.dumps({"type": "subscribe", "tags": ["L1.Speed.PV"]}))
            snapshot = json.loads(await ws.recv())
            print("ws with ticket:", snapshot["type"])

        try:
            async with websockets.connect(f"{WS}?ticket={ticket}"):
                print("reuse: ОШИБКА, тикет принят повторно")
        except Exception as exc:
            print("ticket reuse rejected:", type(exc).__name__)

        rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
        print("refresh:", rotated.status_code, "new token:", rotated.json()["refresh_token"][:12] + "…")
        reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
        print("old refresh reuse:", reuse.status_code)

        auditor = client.post(
            "/api/v1/auth/login", json={"username": "auditor", "password": "dev-password"}
        ).json()["access_token"]
        export = client.get(
            "/api/v1/audit/export?limit=5", headers={"Authorization": f"Bearer {auditor}"}
        )
        lines = [line for line in export.text.splitlines() if line.strip()]
        print("audit export:", export.status_code, export.headers["content-type"], "lines:", len(lines))


asyncio.run(main())
