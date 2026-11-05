"""Скриншоты и замеры интерфейса (Playwright + системный Chrome).

Запуск при поднятых сервисах (эмулятор :48400, backend :8000, vite :5173):
    python scripts/shots.py
Результат: docs/assessment/checks/shots/*.png и measurements.json
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import asyncio

import httpx
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5173"
API = "http://127.0.0.1:8010"
OPCUA = "opc.tcp://127.0.0.1:48400"


def warm_up() -> None:
    """Разгоняет L1, чтобы на сцене были обороты и нагрев, а не нули."""
    from asyncua import Client as UaClient

    async def go() -> None:
        async with UaClient(OPCUA) as client:
            index = await client.get_namespace_index("urn:mfg:emulator")
            line = client.get_node(f"ns={index};s=L1")
            await line.call_method(client.get_node(f"ns={index};s=L1.StartLine").nodeid)
            await line.call_method(client.get_node(f"ns={index};s=L1.SetSpeed").nodeid, 700.0)
            await asyncio.sleep(0.2)
            await line.call_method(client.get_node(f"ns={index};s=L1.SetSpeed").nodeid, 900.0)

    try:
        asyncio.run(go())
    except Exception as exc:  # noqa: BLE001 - сцена всё равно снимется
        print("warm_up skipped:", exc)
OUT = Path(__file__).resolve().parent.parent / "docs" / "assessment" / "checks" / "shots"
SIZES = [(1920, 1080), (1280, 800), (1024, 768)]
PAGES = [
    ("overview", "/"),
    ("production", "/production"),
    ("documents", "/documents"),
    ("approvals", "/approvals"),
    ("audit", "/audit"),
    ("settings", "/settings"),
    ("scene", "/scene"),
]

MEASURE = """
() => {
  const cs = (sel) => {
    const el = document.querySelector(sel);
    return el ? getComputedStyle(el) : null;
  };
  const row = document.querySelector('table.data tbody tr');
  const muted = document.querySelector('td.muted') || document.querySelector('.muted');
  const panel = document.querySelector('.panel');
  const body = getComputedStyle(document.body);
  const parse = (value) => {
    const m = value.match(/\\d+(\\.\\d+)?/g);
    return m ? m.map(Number) : [0, 0, 0];
  };
  const lum = ([r, g, b]) => {
    const c = [r, g, b].map((v) => {
      const s = v / 255;
      return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  };
  const contrast = (fg, bg) => {
    const a = lum(parse(fg)) + 0.05;
    const b = lum(parse(bg)) + 0.05;
    return Math.round((Math.max(a, b) / Math.min(a, b)) * 100) / 100;
  };
  const mutedColor = muted ? getComputedStyle(muted).color : 'rgb(0,0,0)';
  const panelBg = panel ? getComputedStyle(panel).backgroundColor : 'rgb(0,0,0)';
  const inkColor = cs('td') ? getComputedStyle(document.querySelector('td')).color : 'rgb(0,0,0)';
  return {
    font_ui: body.fontFamily,
    font_size: body.fontSize,
    row_height: row ? Math.round(row.getBoundingClientRect().height) : null,
    muted_contrast: contrast(mutedColor, panelBg),
    ink_contrast: contrast(inkColor, panelBg),
    doc_width: document.documentElement.scrollWidth,
    viewport_width: window.innerWidth,
    overflow: document.documentElement.scrollWidth > window.innerWidth,
    banner_present: Boolean(document.querySelector('.banner')),
    banner_text: (document.querySelector('.banner') || {}).textContent || null,
    nav_items: document.querySelectorAll('.nav-item').length,
    buttons_disabled: document.querySelectorAll('button:disabled').length,
  };
}
"""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    token = httpx.post(
        f"{API}/api/v1/auth/login", json={"username": "operator", "password": "dev-password"}, timeout=10
    ).json()["access_token"]
    auditor = httpx.post(
        f"{API}/api/v1/auth/login", json={"username": "auditor", "password": "dev-password"}, timeout=10
    ).json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    pending = httpx.get(f"{API}/api/v1/commands?status=AWAITING_APPROVAL", headers=headers, timeout=10)
    if pending.json().get("count", 0) == 0:
        httpx.post(
            f"{API}/api/v1/commands",
            headers=headers,
            timeout=10,
            json={
                "command_id": str(__import__("uuid").uuid4()),
                "type": "set_setpoint",
                "target": {"line_id": "L2"},
                "params": {"setpoint_value": 300},
                "requested_by": {"kind": "agent", "id": "production#sess-4a"},
                "correlation_id": str(__import__("uuid").uuid4()),
                "evidence": ["tool-call-17"],
            },
        )

    results: dict = {}
    only = os.environ.get("SHOTS_ONLY")
    pages = [item for item in PAGES if not only or item[0] == only]
    warm_up()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        for width, height in SIZES:
            context = browser.new_context(
                viewport={"width": width, "height": height}, device_scale_factor=1
            )
            page = context.new_page()
            page.add_init_script(f"sessionStorage.setItem('factoria.token', {json.dumps(token)})")
            for name, path in pages:
                wait = "domcontentloaded" if name == "scene" else "networkidle"
                page.goto(f"{BASE}{path}", wait_until=wait, timeout=45000)
                page.evaluate("document.fonts.ready")
                page.wait_for_timeout(1200)
                if name == "scene":
                    page.wait_for_selector("canvas", timeout=20000)
                    page.wait_for_timeout(2000)
                if name == "approvals":
                    item = page.query_selector(".queue-item")
                    if item:
                        item.click()
                        page.wait_for_timeout(700)
                if name == "documents":
                    row = page.query_selector("table.data tbody tr")
                    if row:
                        row.click()
                        page.wait_for_timeout(500)
                        page.screenshot(path=str(OUT / f"documents-drawer_{width}.png"), full_page=True)
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(300)
                key = f"{name}_{width}"
                page.screenshot(path=str(OUT / f"{key}.png"), full_page=True)
                results[key] = page.evaluate(MEASURE)
            # журнал отдельно: нужен токен аудитора
            page2 = context.new_page()
            page2.add_init_script(f"sessionStorage.setItem('factoria.token', {json.dumps(auditor)})")
            page2.goto(f"{BASE}/audit", wait_until="networkidle")
            page2.wait_for_timeout(800)
            page2.screenshot(path=str(OUT / f"audit-ok_{width}.png"), full_page=True)
            results[f"audit-ok_{width}"] = page2.evaluate(MEASURE)
            # вход без токена
            page3 = context.new_page()
            page3.goto(f"{BASE}/login", wait_until="networkidle")
            page3.wait_for_timeout(400)
            page3.screenshot(path=str(OUT / f"login_{width}.png"))
            context.close()

        narrow = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1)
        page = narrow.new_page()
        page.add_init_script(f"sessionStorage.setItem('factoria.token', {json.dumps(token)})")
        page.goto(f"{BASE}/production", wait_until="networkidle")
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT / "production_390.png"), full_page=True)
        results["production_390"] = page.evaluate(MEASURE)
        narrow.close()
        browser.close()

    (OUT / "measurements.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({k: results[k] for k in list(results)[:3]}, ensure_ascii=False, indent=2))
    print("screenshots:", len(list(OUT.glob('*.png'))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
