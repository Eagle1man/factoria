# Backend по HTTPS с самоподписанным сертификатом (локальная проверка TLS).
# Требуется: python scripts/gen_certs.py
# Запуск: powershell -ExecutionPolicy Bypass -File scripts/run_backend_https.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$cert = Join-Path $root "certs\localhost.crt"
$key = Join-Path $root "certs\localhost.key"
if (-not (Test-Path $cert) -or -not (Test-Path $key)) {
    Write-Host "Нет сертификатов. Сначала: python scripts/gen_certs.py" -ForegroundColor Red
    exit 2
}

$env:PYTHONPATH = Join-Path $root "backend\src"
$env:DATABASE_URL = "sqlite+aiosqlite:///D:/factoria/data/factoria.db"
$env:OPCUA_ENDPOINT = "opc.tcp://127.0.0.1:48400"
$env:ENV = "dev"

Write-Host "HTTPS на https://127.0.0.1:8443 (сертификат самоподписанный)" -ForegroundColor Cyan
python -m uvicorn factoria.main:app --host 127.0.0.1 --port 8443 --ssl-certfile $cert --ssl-keyfile $key
