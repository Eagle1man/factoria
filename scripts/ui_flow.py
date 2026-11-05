"""E2E-проверка пульта: вход, выбор карточки, комментарий, согласование.

Требует запущенных сервисов (эмулятор :48400, backend :8000, vite :5173).
Запуск: python scripts/ui_flow.py
"""
from __future__ import annotations

import sys
from uuid import uuid4

import httpx
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5173"
API = "http://127.0.0.1:8000"


def ensure_pending() -> str:
    token = httpx.post(
        f"{API}/api/v1/auth/login",
        json={"username": "operator", "password": "dev-password"},
        timeout=10,
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    existing = httpx.get(
        f"{API}/api/v1/commands?status=AWAITING_APPROVAL", headers=headers, timeout=10
    ).json()
    if existing["count"]:
        return headers["Authorization"]
    httpx.post(
        f"{API}/api/v1/commands",
        headers=headers,
        timeout=10,
        json={
            "command_id": str(uuid4()),
            "type": "set_setpoint",
            "target": {"line_id": "L3"},
            "params": {"setpoint_value": 250},
            "requested_by": {"kind": "agent", "id": "production#e2e"},
            "correlation_id": str(uuid4()),
        },
    )
    return headers["Authorization"]


def main() -> int:
    auth = ensure_pending()
    token = auth.split(" ", 1)[1]

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_context(viewport={"width": 1440, "height": 900}).new_page()
        page.add_init_script(f"sessionStorage.setItem('factoria.token', '{token}')")

        page.goto(f"{BASE}/approvals", wait_until="networkidle")
        page.wait_for_selector(".queue-item", timeout=10_000)
        page.click(".queue-item")
        page.wait_for_selector("#comment", timeout=5_000)

        approve = page.get_by_role("button", name="Согласовать")
        print("disabled before comment:", approve.is_disabled())

        page.fill("#comment", "проверил температуру и загрузку линии")
        print("disabled before checkbox:", approve.is_disabled())

        page.check(".checkbox-row input")
        print("disabled after checkbox:", approve.is_disabled())

        approve.click()
        page.wait_for_timeout(1500)

        status = httpx.get(f"{API}/api/v1/commands?limit=5", headers={"Authorization": auth}, timeout=10).json()
        latest = status["commands"][0] if status["commands"] else {}
        print("latest command status:", latest.get("status"))

        page.screenshot(path="docs/assessment/checks/shots/approvals-after-action.png", full_page=True)
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
