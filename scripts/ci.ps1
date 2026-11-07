# Локальный аналог CI: линтер, тесты, сборка.
# Запуск: powershell -ExecutionPolicy Bypass -File scripts/ci.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "1/4 ruff" -ForegroundColor Cyan
python -m ruff check backend tests scripts

Write-Host "2/4 pytest с покрытием" -ForegroundColor Cyan
$env:PYTHONPATH = Join-Path $root "backend\src"
$env:ENV = "test"
$env:DATABASE_URL = "sqlite+aiosqlite:///./data/ci.db"
$env:OPCUA_ENABLED = "false"
$env:JWT_SECRET = "ci-secret-at-least-32-bytes-long!!"
python -m pytest -q --cov=factoria --cov-report=term

Write-Host "3/4 миграции на чистой базе" -ForegroundColor Cyan
$migrationDb = Join-Path $root "data\ci-migrations.db"
if (Test-Path $migrationDb) { Remove-Item $migrationDb -Force }
$env:DATABASE_URL = "sqlite+aiosqlite:///$($migrationDb -replace '\\','/')"
Push-Location (Join-Path $root "backend")
try {
    alembic upgrade head
    alembic current
} finally {
    Pop-Location
}

Write-Host "4/4 сборка фронтенда" -ForegroundColor Cyan
Push-Location (Join-Path $root "frontend")
try {
    npm run build
} finally {
    Pop-Location
}

Write-Host "CI локально: всё прошло" -ForegroundColor Green
