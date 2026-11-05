# REPOSITORY-AUDIT.md — что переиспользуем из `agent-1c-demo`

Дата: 2026-11-05. Метод: чтение кода и запуск проверок, без правок старого репозитория.
Источники: `D:\agent-1c-demo\{PROJECT_AUDIT.md, ARCHITECTURE.md, DECISIONS.md, RISKS.md}`, сам код.

## 1. Сводка

| Компонент | Факт | Строк/объём | Решение для `factoria/` |
|---|---|---|---|
| Файловый мост 1С (`agent/bridge.py`, `1c/АгентМост.bsl`) | работает, протокол v1.0, атомарная запись | — | **оставить в старом контуре**, не переносить (ADR-107) |
| Панель (`agent/panel_server.py`) | 12 эндпоинтов, реальные SQL к 1С через мост | 874 | **ADAPT**: контракт и UX — да, код — нет |
| SCADA-клиент (`agent/scada_client.py`) | реальный HTTP к RapidSCADA, cookie-login, каналы 101–108 | 246+ | **REUSE как источник телеметрии** на этапе 2/3, альтернатива OPC UA |
| Чат-сервис (`agent/chat_service.py`) | диалог 1С↔Ollama через `exchange/chat/` | 457 | **не переносить** в v1 |
| LLM-инструменты (`agent/llm.py`) | только Ollama HTTP | 163 | **заменить** клиентом DeepSeek (§7.1) |
| База агентов (`agent/base_agent.py`) | `use_mock=True` принудительно (ADR-003) | — | **не переносить**, дефект зафиксирован |
| 7 спецагентов | PARTIAL/MOCK/BROKEN (см. PROJECT_AUDIT §1) | — | **DROP** |
| Координатор, конфликт-резолвер | MOCK, никем не инстанцируется | — | **DROP** |
| `agent/plant_sim.py` | модель в памяти, `rng` не используется | — | **ADAPT**: идея, не код |
| `agent/simulator.py` | константы + `random.random()` | — | **DROP**: не симуляция |
| RAG (`rag/`, `chroma_db` 952 МБ) | dense-only, dim=384 | — | **не переносить** в v1 |
| `agent/event_logger.py` | JSONL, анонимизация | — | **ADAPT** идею в `audit_events` |
| `platform/{core,llm,agents}` | Stage 1 каркас | 16 файлов | **ADAPT**: решения, не импорт (другой стек) |
| `platform/{data,model,sim,expert,improve,safety,obs,ui}` | **пусто** (0 файлов) | — | новые модули в `factoria/` |
| `tests/test_readonly_policy.py` | запрет записи в 1С | 2111 байт | **REUSE идею** в `tests/safety/` |
| `verify_1c.py` | приёмка read-only («ПРИЁМКА ПРОЙДЕНА») | 14 КБ | **REUSE как чек-лист** для 4b |

## 2. Что нельзя тащить в новый репозиторий

| Артефакт | Объём | Почему нет |
|---|---|---|
| `.git` | 132 МБ | история старого контура не относится к новому |
| `build/`, `dist/` | 135 МБ | собранные артефакты, не исходники |
| `exchange/` | 8,7 МБ / ~19,7 тыс. файлов | пользовательские данные 1С, не код |
| `*.pptx` (9 файлов) | ~2,9 МБ | презентации, версионируются вручную |
| `*.png` (10 скриншотов) | ~0,4 МБ | содержат реальные данные, не для репозитория |
| `chat_*_out.txt`, `out*.txt`, `*_log.txt` | — | отладочный мусор в корне |
| `dump_tree.txt`, `state_report.txt` | — | снимки состояния, устаревают |
| Три копии ТЗ (MD5 совпадает) | 230 КБ | дубликат; в `factoria/docs/specification.md` одна копия |

## 3. Переиспользуемые контракты старого проекта

1. **Read-only политика** (ADR-002): запись заблокирована на четырёх уровнях —
   `tools.py:19` (`ONEC_WRITE_ENABLED=False`), BSL, `mock_bridge.py`, `chat_service.py`.
   В `factoria/` повторяем принцип: адаптер 1С не имеет методов записи вообще (не флаг, а отсутствие кода).
2. **ADR-005** (внешние API только после разрешения) → ADR-102: `ALLOW_EXTERNAL_API=false`.
3. **ADR-006** (SimulationAdapter) → `backend/src/factoria/simulator/adapter.py`.
4. **Приёмка read-only**: `verify_1c.py` даёт готовый сценарий проверки для 4b.

## 4. Расхождения между документами старого репозитория

| Факт | Где расходится | Влияние на `factoria/` |
|---|---|---|
| SCADA установлена или нет | `docs/audit_report.md` vs `docs/RAPIDSCADA.md` | источник телеметрии v1 — OPC UA-эмулятор; SCADA опциональна |
| Протокол v1.0 / v1.1 / v2.0 | `PROTOCOL.md`, `spec/03_protocol_multiagent.md`, `AGENT_PROJECT_SUMMARY.md` | не наследуем: новый контракт в `docs/api.md` |
| Метрики «−66,7% / −60%» | `AGENT_PROJECT_SUMMARY.md` | не переносить как факт: не подтверждены кодом |
| Число проверок панели 13/26/37 | README/docs | факт — 37 вызовов в `tools/check_panel.py` |

## 5. Что это значит для этапа 0

Старого кода, который можно импортировать, почти нет: рабочий контур — это
мост + панель + чат под Ollama, а новый стек (FastAPI, pydantic v2, asyncua,
LangGraph) другой. Переиспользуем **решения и контракты**, а не модули.
Единственное исключение по коду — `scada_client.py` как справочник по
RapidSCADA HTTP API, если понадобится реальная SCADA вместо эмулятора.
