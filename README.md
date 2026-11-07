# FACTORIA & AI

Мультиагентная система управления производственными процессами предприятия:
1С ↔ backend ↔ OPC UA/SCADA, цифровой двойник, симулятор, пульт оператора.

Репозиторий `D:\factoria` работает рядом с демо-контуром `D:\agent-1c-demo`
и не изменяет его (ADR-101). Полный снимок состояния — `docs/PROJECT-STATE.md`.

## Что уже работает

| Блок | Состояние |
|---|---|
| OPC UA-эмулятор: 3 линии, 21 тег, 5 метод-нод, interlocks | работает |
| Backend: FastAPI, JWT/RBAC, кэш тегов, WebSocket, SQLite, Alembic, аудит | работает |
| Команды: контракт, 5 стадий валидации, идемпотентность, TTL | работает |
| A1/A2: подтверждение человеком и автономия в безопасном коридоре | работает |
| Интерфейс: обзор, производство, согласования, документы, двойник, журнал, настройки, 3D | работает |
| Двойник: структура, покрытие, история срезов, сравнение | работает |
| Эксперименты: 5 сценариев, seed, история и сравнение прогонов | работает |
| 1С: HTTP/OData-адаптеры и BSL-шаблон | код готов, подключение в демо-режиме (`ONES_MODE=stub`) |
| Агенты DeepSeek (этап 5) | ждут ключ |

## Запуск

```powershell
# 1. эмулятор
python opcua-emulator/emulator.py

# 2. backend (:8010)
$env:PYTHONPATH="D:\factoria\backend\src"
$env:DATABASE_URL="sqlite+aiosqlite:///D:/factoria/data/factoria.db"
$env:OPCUA_ENDPOINT="opc.tcp://127.0.0.1:48400"
python -m uvicorn factoria.main:app --port 8010

# 3. интерфейс (:5173)
cd frontend
npm run dev
```

Вход: `operator` / `dev-password`; для журнала — `auditor` / `dev-password`.

Backend слушает **8010**, не 8000: в этой среде uvicorn на 8000 зависает без
логов (asyncio и `http.server` на том же порту работают). Прокси Vite настроен
на 8010.

## HTTPS (локально)

```powershell
python scripts/gen_certs.py
powershell -ExecutionPolicy Bypass -File scripts/run_backend_https.ps1
# https://127.0.0.1:8443/api/v1/health (сертификат самоподписанный)
```

Сертификаты лежат в `certs/` и не коммитятся.

OPC UA TLS включается переменными окружения (сертификаты создаёт тот же скрипт):

```powershell
$env:OPCUA_SECURITY="Basic256Sha256_SignAndEncrypt"
$env:OPCUA_CERT="D:\factoria\certs\opcua-server.cert.der"
$env:OPCUA_KEY="D:\factoria\certs\opcua-server.key.der"
# backend: OPCUA_CLIENT_CERT, OPCUA_CLIENT_KEY, OPCUA_SERVER_CERT
```

## Проверки

```powershell
python -m pytest -q            # 172 теста
cd frontend; npm run build     # TypeScript + Vite
python scripts/shots.py        # скриншоты 1920/1280/1024/390 и замеры
python -m ruff check backend tests scripts   # линтер
powershell -ExecutionPolicy Bypass -File scripts/ci.ps1   # всё сразу
```

## Структура

| Путь | Содержание |
|---|---|
| `backend/src/factoria/` | FastAPI: api, auth, contract, validation, opcua, model, realtime, storage |
| `opcua-emulator/` | эмулятор ПЛК: физика линий и method-ноды |
| `frontend/src/` | React 18 + TS: экраны, компоненты, 3D-сцена |
| `1c-extension/` | BSL-шаблон HTTP-сервиса и инструкция публикации |
| `docs/` | ТЗ, API, модель данных, ADR, безопасность, отчёты по этапам |
| `DESIGN.md`, `DESIGN.operator.md`, `DESIGN.chat.md` | дизайн-система и варианты |
| `scripts/` | скриншоты, смоуки, публикация и выгрузка 1С |
| `tests/` | pytest: контракт, валидация, API, OPC UA, двойник |

## Границы безопасности

- LLM не имеет транспорта к ПЛК/OPC UA — только инструменты backend.
- Валидация и исполнение — на backend, не на модели.
- 1С в v1 — только чтение; запись исключена.
- `AUTONOMY_MAX=A1` по умолчанию: любое действие подтверждает человек.
- `ALLOW_EXTERNAL_API=false` по умолчанию.
- `emergency_stop` модели недоступен.

Подробнее: `docs/decisions.md` (ADR-101…119), `docs/security/ot-baseline.md`.

## Документы

- `docs/PROJECT-STATE.md` — что сделано, что заблокировано, как проверять.
- `docs/specification.md` — ТЗ v2.1 и §18 (интерфейс, дизайн-система).
- `docs/api.md` — контракт API и WebSocket.
- `docs/assessment/` — обследование и отчёты по этапам.
