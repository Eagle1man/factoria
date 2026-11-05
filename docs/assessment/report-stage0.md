# REPORT — ЭТАП 0: обследование

Дата: 2026-11-05. Шаблон: ТЗ §15. Исполнитель: opencode (DeepSeek V4.1 Flash).

---

## 1. ЦЕЛЬ

Провести обследование по §14: изучить `agent-1c-demo` и ТЗ v2.1, выявить
переиспользуемое, противоречия и пробелы, проверить совместимость стека на
реальной машине, предложить план и пилотные сценарии. **Код этапов 1+ не писать.**

Цель достигнута: 9 документов assessment + репозиторий-скелет `factoria/`.
Спайк DeepSeek (§3.4) не выполнен — нет ключа (BLOCKED, см. §7).

## 2. ИЗУЧЕНО

| Источник | Объём / факт |
|---|---|
| `docs/specification.md` (ТЗ v2.1) | 811 строк, прочитано целиком |
| `D:\agent-1c-demo\PROJECT_AUDIT.md` | 51 строка, факты по 15 компонентам |
| `D:\agent-1c-demo\ARCHITECTURE.md` | 58 строк, текущий и целевой контур |
| `D:\agent-1c-demo\DECISIONS.md` | ADR-001…006 |
| `D:\agent-1c-demo\RISKS.md` | 5 критических рисков + 6 вопросов владельцу |
| `agent/panel_server.py` | 874 строки, 12 эндпоинтов `/api/*` |
| `agent/scada_client.py` | RapidSCADA HTTP, cookie-login, каналы 101–108 |
| `agent/tools.py` | `ONEC_WRITE_ENABLED=False` (строка 19) — read-only |
| `platform/` | `core` 7 файлов, `llm` 4, `agents` 5; `data/model/sim/expert/improve/safety/obs/ui` — **пусто** |
| `tests/` | 5 файлов, включая `test_readonly_policy.py` |
| Машина | Python, Docker, Node, установленные пакеты — фактическими командами |

## 3. РЕАЛИЗОВАНО

Создан репозиторий `D:\factoria` (только скелет и документы, код этапов 1+ отсутствует):

| Файл | Что это |
|---|---|
| `README.md` | назначение, этап, план B, границы безопасности |
| `.env.example` | флаги ТЗ + `AUTONOMY_MAX`, `TAG_HISTORY_RETENTION_H`, `OPCUA_ENDPOINT=localhost` |
| `.gitignore`, `opencode.jsonc`, `pyproject.toml` | конфигурация проекта |
| `docs/specification.md` | копия ТЗ v2.1 (источник истины) |
| `docs/decisions.md` | ADR-101…110 |
| `docs/tag-registry.md` | схема `registry.yaml`, которой нет в ТЗ |
| `docs/autonomy-matrix.md` | матрица A0–A3 как data-driven dict + снятие противоречия |
| `docs/data-model.md` | 7 таблиц, включая недостающие `users`, `tag_history` |
| `docs/api.md` | контракт `/api/v1` + 7 PLANNED путей под 2D-панель |
| `docs/risks.md` | короткая сводка |
| `docs/assessment/repository-audit.md` | что переиспользуем из `agent-1c-demo` |
| `docs/assessment/architecture-assessment.md` | контуры, границы доверия, карта зависимостей |
| `docs/assessment/technology-stack.md` | проверка стека на машине |
| `docs/assessment/requirements-traceability.md` | 63 требования со статусами |
| `docs/assessment/risks.md` | R-001…R-022 |
| `docs/assessment/open-decisions.md` | OD-01…OD-16 |
| `docs/assessment/implementation-roadmap.md` | пересчёт оценок и ворота |
| `docs/assessment/pilot-scenario-proposals.md` | 5 сценариев с оценкой |
| `docs/assessment/deepseek-spike.md` | чек-лист, статус **НЕ ВЫПОЛНЕН** |
| `docs/assessment/checks/stage0-*.txt` | фактический вывод проверок |
| `scripts/spike_opcua_methods.py` | спайк паттерна method-нод (доказательство §4.3) |

## 4. АРХИТЕКТУРНЫЕ РЕШЕНИЯ

| Решение | Почему |
|---|---|
| Старый контур не трогаем, новый репозиторий рядом | ADR-101; big-bang ломает работающее демо |
| `AUTONOMY_MAX=A1` по умолчанию, A2 за флагом | ADR-103: A2 меняет политику «человек подтверждает всё» |
| `registry.yaml` — единственный источник правды | ADR-104: три потребителя (эмулятор, backend, bindings) без него разъедутся |
| Только method-ноды, `writable` всегда `false` | ADR-105 + спайк: отказ по физике возможен только на сервере |
| UI приводим к `/api/v1`, совместимость не делаем | ADR-106: два контракта — двойная поддержка |
| SQLite + Alembic с первого дня | ADR-108: идемпотентность и аудит требуют транзакций |
| Python 3.14.3 как фактическая цель | ADR-109: 3.11/3.13 на машине не существуют |
| FUXA/InfluxDB отложены | ADR-110: Docker-демона нет |

## 5. ТЕСТИРОВАНИЕ (команды и фактический вывод)

**5.1. Версии Python — реестр `py` врёт:**

```
py -0p  → 3.14 (default), 3.13, 3.11 (D:\1\python.exe)
Test-Path D:\1\python.exe → False
py -3.11 → [ERROR] Failed to launch 'D:\1\python.exe' (0x80070003)
py -3.13 → [ERROR] Failed to launch ... (0x80070780)
python --version → Python 3.14.3
```

**5.2. Docker:**

```
docker --version → Docker version 19.03.1, build 74b1e89e8a
docker info      → нет ответа за 25 с (команда прервана по таймауту)
```

**5.3. Установка стека в чистый venv (Python 3.14.3):**

```
alembic 1.20.1
langgraph 1.2.19
StateGraph ok
langgraph.checkpoint.sqlite → ModuleNotFoundError
после pip install langgraph-checkpoint-sqlite → SqliteSaver ok
```

**5.4. Спайк OPC UA (`scripts/spike_opcua_methods.py`):**

```
direct_write_blocked = True
direct_write_error   = 0x801f0000     (BadUserAccessDenied)
method_write_ok      = True
interlock_blocks     = True
interlock_error      = 0x80af0000     (BadInvalidState)
value_after_interlock = 500.0
SPIKE_RESULT = PASS
```

Полные логи: `docs/assessment/checks/stage0-spike.txt`, `stage0-stack.txt`.

**5.5. Что проверено импортом:** `asyncua 2.1.0`, `fastapi 0.136.1`,
`pydantic 2.13.4`, `SQLAlchemy 2.0.49`, `aiosqlite 0.22.1`, `uvicorn 0.49.0`,
`pytest 9.0.3` — работают на 3.14.3.

## 6. РЕЗУЛЬТАТЫ

| Проверка | Итог |
|---|---|
| Assessment из 9 документов | **ПРОШЛО** |
| Скелет `factoria/` по §2 | **ПРОШЛО** (добавлены `tests/`, `scripts/`, отсутствовавшие в ТЗ) |
| Стек собирается на машине | **ПРОШЛО** (с оговоркой: Python 3.14, не 3.11) |
| Паттерн method-нод и interlock | **ПРОШЛО** (SPIKE_RESULT = PASS) |
| План B без Docker | **ПРОШЛО** (демона нет — факт) |
| Спайк DeepSeek §3.4 | **НЕ ПРОШЛО / НЕ ВЫПОЛНЕНО** — нет ключа и сети |

## 7. ПРОБЛЕМЫ

1. **Спайк DeepSeek не выполнен.** Без него нельзя утверждать, что strict
   mode, отключение thinking и лимиты из §7.1 реальны. Этап 5 не начинать.
2. **Python 3.11 недоступен физически.** ТЗ §3.1 закрепляет «3.11+», а на машине
   работает только 3.14.3. Либо ADR-109, либо переустановка.
3. **Противоречие §6.2/§6.5** не снято в самом ТЗ — предложено решение,
   но нужно утверждение (OD-02), иначе тесты матрицы будут проверять не то.
4. **API §5.2 не покрывает 9 экранов панели** — 7 путей помечены PLANNED,
   их нужно утвердить (OD-05).
5. **`py -0p` показывает несуществующие установки** — любые проверки версий
   делать запуском, а не реестром.

## 8. РИСКИ (новые, относительно ТЗ)

| ID | Риск |
|---|---|
| R-009 | `SqliteSaver` требует пакет `langgraph-checkpoint-sqlite`, не указанный в ТЗ |
| R-010 | LangGraph 1.x: API менялся, `interrupt()` + рестарт не проверены |
| R-015 | Аудит append-only не гарантирован SQLite без запрета на уровне репозитория |
| R-016 | `registry.yaml` разъедется между тремя потребителями без генерации |
| R-012 | Жюри debate из 2 голосов даёт ничью ~50% |

Полный список — `docs/assessment/risks.md`.

## 9. ОСТАТОЧНЫЕ ВОПРОСЫ (требуют человека)

| ID | Вопрос | Блокирует |
|---|---|---|
| OD-01 | Python: 3.14 как есть или переустановить 3.11 | этап 1 |
| OD-02 | Порог 800: дельта или «SP<400 и new>800» | этап 4a |
| OD-07 | Ключ DeepSeek + бюджет + разрешение на сеть | этап 5 |
| OD-03/04/05 | 9 или 6 экранов; `/api/v1`; 7 эндпоинтов | этап 3 |
| OD-09/10/11 | Конфигурация 1С, кто публикует `.cfe`, тестовая база | этап 4b |
| OD-08 | Размер жюри debate (2 или 3) | этап 7 |

## 10. СООТВЕТСТВИЕ ТЗ (REQ → статус)

| Группа | Кол-во | Статус |
|---|---|---|
| Границы и контуры | 9 | 7 CONTRACT, 1 DONE, 1 PROSE |
| OPC UA (§4) | 8 | 5 CONTRACT, 1 DONE, 1 PROSE, 1 N/A |
| Backend (§5) | 10 | 8 CONTRACT, 2 MISSING |
| Валидатор (§6) | 10 | 8 CONTRACT, 1 CONTRADICTION, 1 PROSE |
| Агенты (§7) | 11 | 8 CONTRACT, 1 PROSE, 2 BLOCKED |
| Frontend (§8) | 6 | 3 CONTRACT, 3 PROSE |
| 1С (§9) | 5 | 4 CONTRACT, 1 PROSE |
| Песочница (§10) | 3 | 2 CONTRACT, 1 PROSE |
| Тесты (§11) | 5 | 1 DONE, 3 PROSE, 1 VERIFY |
| Эксплуатация | 7 | 7 MISSING (закрыты документами `factoria/docs`) |

Детали и проверки — `docs/assessment/requirements-traceability.md`.

## 11. СЛЕДУЮЩИЙ ЭТАП (предложение)

**Этап 1 — OPC UA-эмулятор**, после ответов на OD-01 и OD-02:

1. `backend/src/factoria/tags/registry.yaml` — 21 тег + 5 методов (схема готова).
2. `opcua-emulator/emulator.py` — 3 линии, τ=2 c для Speed.PV, нагрев ∝ (SP/1200)²,
   interlock `Temp>80 → BadInvalidState`, автостоп при `Load>95` 60 c.
3. `scripts/gen-tag-registry.py` и `scripts/gen-bindings.py`.
4. `tests/test_emulator.py` — спайк превращается в pytest (маркер `integration`).

DoD: `SPIKE_RESULT=PASS` в CI, 21 тег виден клиенту, `SetSpeed(500)` при
`Temp>80` отклонён, `docs/tag-registry.md` воспроизводим из YAML.

Спайк DeepSeek делать параллельно, как только появится ключ, — он не блокирует этап 1.

---

**Запрет §15 соблюдён:** неудачная проверка (§6, спайк DeepSeek) не скрыта,
частичное не выдано за завершённое, работоспособность не заявлена без запуска.
