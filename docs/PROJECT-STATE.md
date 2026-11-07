# PROJECT-STATE.md — снимок состояния репозитория

Дата: 2026-11-07. Ветка: `master`. Коммит-снимок: см. `git log -1`.
Репозиторий: `D:\factoria` (рядом с рабочим демо-контуром `D:\agent-1c-demo`).

## 1. Что работает

| Блок | Состояние | Проверка |
|---|---|---|
| OPC UA-эмулятор: 3 линии, 21 тег, 5 метод-нод, interlocks | работает | `pytest`, `SPIKE_RESULT=PASS` |
| Backend: FastAPI, JWT, RBAC, кэш, WS, SQLite, Alembic, аудит | работает | 150 тестов |
| Команды: контракт, 5 стадий валидации, идемпотентность, TTL | работает | smoke + тесты |
| A1/A2: подтверждение человеком, автономия в коридоре | работает | smoke `command_status` |
| Согласования, документы (stub), двойник с историей, 3D-сцена | работает | скриншоты |
| Эксперименты: 5 сценариев, seed, история, сравнение прогонов | работает | `report-sim.md` |
| Безопасность: ws_ticket, refresh/отзыв, лимит входа, экспорт аудита | работает | `report-security.md` |
| Журнал аудита, настройки | работает | скриншоты |

Стек: Python 3.14.3, FastAPI, SQLAlchemy/aiosqlite, asyncua 2.1.0,
React 18 + TypeScript + Vite, three.js/R3F.

## 2. Что заблокировано

| Блок | Причина | Что нужно |
|---|---|---|
| Этап 5 — агенты DeepSeek | нет `DEEPSEEK_API_KEY` | ключ + разрешение на исходящий HTTPS (сеть проверена: 401 без ключа) |
| Этап 4b — реальная 1С | база `DemoAgent` учебной версии: лимит подключений, нет администратора, пустой состав OData | лицензионная база и доступ к конфигурации |
| 1С в UI | по решению ADR-118 — демо-режим `ONES_MODE=stub` | включается одной переменной, код готов |

## 3. Запуск

```powershell
# 1. эмулятор
python opcua-emulator/emulator.py

# 2. backend
$env:PYTHONPATH="D:\factoria\backend\src"
$env:DATABASE_URL="sqlite+aiosqlite:///D:/factoria/data/factoria.db"
$env:OPCUA_ENDPOINT="opc.tcp://127.0.0.1:48400"
python -m uvicorn factoria.main:app --port 8010

# 3. интерфейс
cd frontend; npm run dev
```

Вход: `operator` / `dev-password` (`auditor` — для журнала).

## 4. Проверки

```powershell
python -m pytest -q                 # 150 тестов
cd frontend; npm run build          # tsc + vite
python scripts/shots.py             # скриншоты 1920/1280/1024 + 390
python scripts/smoke_stage6.py      # A2 и WS-события
```

## 5. Особенности среды (чтобы не искать заново)

- **Порт 8000:** uvicorn на нём зависает без логов, при этом `asyncio.start_server`
  и `http.server` работают. Контур переведён на **8010**.
- **PowerShell 5.1 и UTF-8:** файлы без BOM читаются как ANSI. Скрипты `.ps1`
  должны быть с BOM, править текст — инструментом, не `Get-Content`/`Set-Content`.
- **BOM в конфигах:** `alembic.ini` с BOM ломает `configparser`; есть тест
  `test_no_bom_in_repository`.
- **1С:** установлена 8.3.27.1508 (x86). Публикация на IIS требует отдельного
  пула с `enable32BitAppOnWin64=true` — иначе `500.0 / 0x800700c1`.
- **Первый снимок двойника** не пишется, пока кэш пуст (`NoDataYet`), иначе
  в историю попадал ложный 0 %.

## 6. Карта документов

| Документ | О чём |
|---|---|
| `README.md` | запуск и границы проекта |
| `docs/specification.md` | ТЗ v2.1 + §18 (интерфейс, дизайн-система) |
| `docs/api.md` | контракт API и WS |
| `docs/data-model.md` | таблицы и состояния |
| `docs/decisions.md` | ADR-101…119 |
| `docs/security/ot-baseline.md` | чек-лист OT-безопасности |
| `docs/ones-http-contract.md` | контракт 1С (HTTP и OData) |
| `docs/assessment/` | обследование, отчёты по этапам |
| `DESIGN.md`, `DESIGN.operator.md`, `DESIGN.chat.md` | дизайн-система |
| `docs/assessment/checks/shots/` | скриншоты и замеры |

## 7. Следующие шаги

1. Ключ DeepSeek → этап 5 (агент `sequential`, 8 инструментов, evidence).
2. Лицензионная 1С → этап 4b (HTTP-сервис в расширении, публикация).
3. TLS для OPC UA и HTTPS для публикации — перед пилотом.
