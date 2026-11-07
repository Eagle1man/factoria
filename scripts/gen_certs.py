"""Самоподписанные сертификаты для локального HTTPS и OPC UA TLS.

Файлы пишутся в `certs/` (каталог в .gitignore) и не коммитятся.
Запуск: python scripts/gen_certs.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend" / "src"))

from factoria.security.certs import generate_https_pair, generate_opcua_pair  # noqa: E402

OUT = ROOT / "certs"


def main() -> int:
    https_cert, https_key = generate_https_pair(OUT)
    server_cert, server_key = generate_opcua_pair(
        OUT, "opcua-server", "urn:factoria:server", server=True
    )
    client_cert, client_key = generate_opcua_pair(
        OUT, "opcua-client", "urn:factoria:client", server=False
    )

    print(f"HTTPS:  {https_cert.name}, {https_key.name}")
    print(f"OPC UA сервер: {server_cert.name}, {server_key.name}")
    print(f"OPC UA клиент: {client_cert.name}, {client_key.name}")
    print("срок: 365 дней; каталог certs/ не коммитится")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
