# PROJECT-STATE.md — снимок состояния репозитория

Дата: 2026-11-08 (обновление: интеграция спеки Stitch). Ветка: `master`. Коммит-снимок: см. `git log -1`.
Репозиторий: `D:\factoria` (рядом с рабочим демо-контуром `D:\agent-1c-demo`).

## 1. Что работает

| Блок | Состояние | Проверка |
|---|---|---|
| OPC UA-эмулятор: 3 линии, 21 тег, 5 метод-нод, interlocks | работает | `pytest`, `SPIKE_RESULT=PASS` |
| Backend: FastAPI, JWT, RBAC, кэш, WS, SQLite, Alembic, аудит, LLM health | работает | 185 тестов (pytest `tests/`), ruff clean |
| Команды: контракт, 5 стадий валидации, идемпотентность, TTL | работает | smoke + тесты |
| A1/A2: подтверждение человеком, автономия в коридоре | работает | smoke `command_status` |
| Согласования, документы (stub), двойник с историей, 3D-сцена | работает | скриншоты |
| Эксперименты: 5 сценариев, seed, история, сравнение прогонов | работает | `report-sim.md` |
| Безопасность: ws_ticket, refresh/отзыв, лимит входа, экспорт аудита | работает | `report-security.md` |
| Поток цеха: 4 шаблона (Stitch), 2.5D-схема, Co-Pilot (детерминированный, A1), экспорт XML, запуск sim-сценария | работает | `report-stitch-merge.md` |
| LLM-провайдер: `none/deepseek/ollama`, статус в `/health` без секретов (ADR-121) | конфиг готов | env/ключ/VM — решение владельца |
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
$env:PYTHONPATH="D:\factoria\backend\src"
python -m pytest tests -q           # 185 тестов (каталог tests/)
cd frontend; npm run build          # tsc + vite
python scripts/shots.py             # скриншоты 1920/1280/1024 + 390
python scripts/smoke_stage6.py      # A2 и WS-события
```

## 4.1. CI и качество кода

- `.github/workflows/ci.yml`: ruff, pytest с покрытием, миграции на чистой базе,
  сборка фронтенда, тест дизайн-системы.
- Локальный аналог: `powershell -ExecutionPolicy Bypass -File scripts/ci.ps1`.
- Job `visual`: поднимает контур, снимает скриншоты, падает при переполнении,
  выгружает артефакт.
- HTTPS для API: `scripts/gen_certs.py` + `scripts/run_backend_https.ps1`.
- OPC UA TLS: `Basic256Sha256_SignAndEncrypt`, проверен интеграционным тестом
  (`tests/test_opcua_tls.py`).
- Покрытие backend: ранее **91 %** (`docs/assessment/checks/coverage.txt`); после интеграции Stitch покрытие не пересчитывалось в этом прогоне.
- Линтер: `ruff check backend tests scripts` — без замечаний.

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
| `docs/decisions.md` | ADR-101…121 |
| `docs/security/ot-baseline.md` | чек-лист OT-безопасности |
| `docs/ones-http-contract.md` | контракт 1С (HTTP и OData) |
| `docs/assessment/` | обследование, отчёты по этапам |
| `docs/assessment/report-stitch-merge.md` | интеграция спеки Stitch/Three.js |
| `docs/spec/stitch-threejs/` | исходная спека, прототип, решения |
| `DESIGN.md`, `DESIGN.operator.md`, `DESIGN.chat.md` | дизайн-система |
| `docs/assessment/checks/shots/` | скриншоты и замеры |

## 7. Следующие шаги

1. Ключ DeepSeek / Ollama VM (URL, модель, auth) → этап 5; слой `LLM_PROVIDER` готов (`.env.example`), агентный tool-calling — при подключении (thinking off).
2. Лицензионная 1С → этап 4b (HTTP-сервис в расширении, публикация).
3. Скриншоты `/flow` после перегенерации `scripts/shots.py`; покрытие пересчитать при необходимости.
