# REQUIREMENTS-TRACEABILITY.md — реестр требований

Дата: 2026-11-05. Источник: ТЗ v2.1 (`docs/specification.md`).
Статусы: **CONTRACT** — есть схема/контракт, можно кодировать; **PROSE** — описано
словами, схемы нет; **MISSING** — в ТЗ отсутствует, но нужно; **CONTRADICTION** —
внутреннее противоречие; **DONE** — закрыто на этапе 0; **BLOCKED** — внешняя зависимость.

## 1. Границы проекта (§0–§1)

| REQ | Требование | Статус | Проверка |
|---|---|---|---|
| REQ-001 | Новый репозиторий `factoria/`, `agent-1c-demo` не трогаем | **DONE** | дерево `D:\factoria` |
| REQ-002 | `ALLOW_EXTERNAL_API=false` по умолчанию | **CONTRACT** | `.env.example` |
| REQ-003 | A2 в границах §6.4, остальное A1 | **CONTRACT** | `docs/autonomy-matrix.md` |
| REQ-004 | Lovable-UI = 2D-панель нового backend, 3D — отдельный экран | **PROSE** | нет API под 9 экранов, см. REQ-095 |
| REQ-005 | Этапы 9–10 — только заглушка `ImprovementCandidate` | **PROSE** | нет dataclass-контракта |
| REQ-006 | План B без Docker | **DONE** | демон отсутствует, см. `technology-stack.md` |
| REQ-007 | 1С: stub → HTTP-сервисы | **CONTRACT** | `ONES_MODE` |
| REQ-008 | LLM не имеет транспорта к ПЛК | **CONTRACT** | 8 инструментов §7.2 |
| REQ-009 | Валидация не на LLM | **CONTRACT** | §6.1 |

## 2. OPC UA-эмулятор (§4)

| REQ | Требование | Статус | Проверка |
|---|---|---|---|
| REQ-010 | 21 тег (7 × 3 линии) | **CONTRACT** | `docs/tag-registry.md` |
| REQ-011 | Все изменения через method-ноды | **DONE (спайк)** | `scripts/spike_opcua_methods.py`, PASS |
| REQ-012 | Interlocks в сервере: Temp>80, Load>95 | **CONTRACT** | один interlock проверен спайком |
| REQ-013 | `SetRecipe` вне R1..R5 → BadOutOfRange | **CONTRACT** | — |
| REQ-014 | Автостоп при Load>95 дольше 60 c | **CONTRACT** | таймер в эмуляторе |
| REQ-015 | FUXA — read-only витрина | **N/A v1** | FUXA отложена (ADR-110) |
| REQ-016 | `docs/tag-registry.md` генерируется | **PROSE** | скрипт-генератор в ТЗ не указан |
| REQ-017 | 5 методов обязательны | **CONTRACT** | §4.4 |

## 3. Backend (§5)

| REQ | Требование | Статус | Проверка |
|---|---|---|---|
| REQ-020 | State machine 12 состояний | **CONTRACT** | `docs/api.md` §3 |
| REQ-021 | `APPROVED → REVALIDATING` перед исполнением | **CONTRACT** | §5.1, §6.6 |
| REQ-022 | Идемпотентность по `command_id` (UUIDv7) | **CONTRACT** | `docs/data-model.md` |
| REQ-023 | REST §5.2 (9 путей) | **CONTRACT** | `docs/api.md` |
| REQ-024 | WS: delta, resume, stale, seq | **CONTRACT** | `docs/api.md` §6 |
| REQ-025 | JWT, `operator_id` из токена, 7 ролей | **CONTRACT** | `docs/data-model.md` |
| REQ-026 | WS-подписка по ролям | **CONTRACT** | — |
| REQ-027 | Ошибки `{stage, code, detail}` | **CONTRACT** | коды — `docs/api.md` §7 |
| REQ-028 | Хранилище пользователей, хеш пароля | **MISSING** | в ТЗ нет; добавлено в data-model |
| REQ-029 | Refresh/revocation, лимит попыток входа | **MISSING** | в ТЗ нет |

## 4. Валидатор (§6)

| REQ | Требование | Статус | Проверка |
|---|---|---|---|
| REQ-030 | 5 стадий, порядок фиксирован | **CONTRACT** | §6.1 |
| REQ-031 | Порог 400 rpm, Δ≤5% (≤60 rpm) | **CONTRACT** | `registry.yaml` |
| REQ-032 | `|Δ| > 800` → interlock | **CONTRADICTION** | §6.2 даёт другой предикат, см. `autonomy-matrix.md` §4 |
| REQ-033 | `new > 400` → A1 (не запрет) | **CONTRACT** | `docs/autonomy-matrix.md` |
| REQ-034 | Матрица 7×4 = 28 ячеек, data-driven | **CONTRACT** | `docs/autonomy-matrix.md` |
| REQ-035 | A2 только при 6 условиях одновременно | **CONTRACT** | — |
| REQ-036 | stale/bad → отказ, не A1 | **CONTRACT** | — |
| REQ-037 | TTL 5 мин → EXPIRED | **CONTRACT** | — |
| REQ-038 | Revalidate отклоняет при изменении условий | **CONTRACT** | — |
| REQ-039 | Уведомление при A2 | **PROSE** | канал уведомления не определён |

## 5. Агенты (§7)

| REQ | Требование | Статус | Проверка |
|---|---|---|---|
| REQ-040 | strict mode через `/beta` | **BLOCKED** | нет ключа/сети |
| REQ-041 | 8 инструментов, отдельный на команду | **CONTRACT** | §7.2 |
| REQ-042 | `evidence` в каждом write | **CONTRACT** | §7.2 |
| REQ-043 | Все поля required, `additionalProperties: false` | **CONTRACT** | — |
| REQ-044 | Thinking отключён для tool-calling | **BLOCKED** | требует проверки на API |
| REQ-045 | `SessionBudget` 200k / 4 раунда / 120 c | **CONTRACT** | — |
| REQ-046 | LangGraph: sequential/supervisor/debate | **CONTRACT** | §7.5 |
| REQ-047 | `SqliteSaver` для чекпоинтов | **CONTRACT** | нужен пакет `langgraph-checkpoint-sqlite` |
| REQ-048 | Resume: WS + fallback поллинг 5 c | **CONTRACT** | §7.4 |
| REQ-049 | 3 роли + orchestrator, промпты в `*.md` | **PROSE** | содержание промптов не задано |
| REQ-050 | Деградация 5xx → read-only, 1 повтор | **CONTRACT** | — |

## 6. Frontend (§8)

| REQ | Требование | Статус | Проверка |
|---|---|---|---|
| REQ-055 | R3F, GLB `line.glb`, 4 типа привязок | **PROSE** | GLB-ассета нет |
| REQ-056 | `bindings.ts` генерируется из registry | **PROSE** | скрипт в дереве отсутствует |
| REQ-057 | Reconnect 1→2→5→10 c, resume last_seq | **CONTRACT** | — |
| REQ-058 | stale/bad → меш серый, не показывать старое | **CONTRACT** | — |
| REQ-059 | Пульт — отдельная WS-ветка | **PROSE** | протокол ветки не описан |
| REQ-060 | 2D-панель: 6 экранов §8.4 | **PROSE** | расходится с 9 экранами Lovable |

## 7. 1С (§9)

| REQ | Требование | Статус | Проверка |
|---|---|---|---|
| REQ-065 | `OnesAdapter`: 2 метода чтения | **CONTRACT** | §9.1 |
| REQ-066 | Stub: 5 заказов, `POST /debug/orders` только dev | **CONTRACT** | — |
| REQ-067 | BSL HTTP-сервисы + расширение `.cfe` | **PROSE** | нет тестовой базы 1С |
| REQ-068 | Запись в 1С исключена | **CONTRACT** | §1.3, §9.1 |
| REQ-069 | 1С не в real-time, события 3D — из SCADA | **CONTRACT** | — |

## 8. Песочница (§10)

| REQ | Требование | Статус | Проверка |
|---|---|---|---|
| REQ-070 | Polling 2 c, `TARGET=opcua|satisfactory` | **CONTRACT** | этап 8 |
| REQ-071 | Игровые данные помечены недостоверными | **CONTRACT** | — |
| REQ-072 | `SatisfactoryMCP` read-only | **PROSE** | версия/эндпоинты не проверены |

## 9. Тесты и приёмка (§11, §15, §17)

| REQ | Требование | Статус | Проверка |
|---|---|---|---|
| REQ-075 | 8 уровней тестов | **PROSE** | каталога `tests/` в ТЗ §2 нет; создан |
| REQ-076 | Кассеты DeepSeek, CI без ключа — skip | **PROSE** | формат кассет не задан |
| REQ-077 | `deepseek-compat-kit lint-schema --strict` | **VERIFY** | существование инструмента не подтверждено |
| REQ-078 | Отчёт по шаблону §15 | **DONE** | `report-stage0.md` |
| REQ-079 | Assessment из 9 документов | **DONE** | этот каталог |

## 10. Эксплуатация (не описано в ТЗ, но нужно)

| REQ | Требование | Статус | Проверка |
|---|---|---|---|
| REQ-080 | Ретенция `tag_history` | **MISSING** | добавлено `TAG_HISTORY_RETENTION_H` |
| REQ-081 | Ретенция `commands` vs вечный аудит | **MISSING** | `docs/data-model.md` §2 |
| REQ-082 | Политика таймзон (UTC) | **MISSING** | зафиксировано в `docs/api.md` |
| REQ-083 | Отказ старта при `JWT_SECRET=dev-*` и `ENV≠dev` | **MISSING** | добавлено в `.env.example` |
| REQ-084 | `AUTONOMY_MAX` — флаг выключения A2 | **MISSING** | ADR-103 |
| REQ-085 | UI: 7 эндпоинтов для панели | **MISSING** | `docs/api.md` §5, PLANNED |
| REQ-086 | Совместимость UI с `/api/v1` | **MISSING** | ADR-106 |

## 11. Итог

| Статус | Кол-во |
|---|---|
| CONTRACT | 38 |
| PROSE | 13 |
| MISSING | 7 |
| CONTRADICTION | 1 |
| BLOCKED | 2 |
| DONE | 5 |
| N/A / VERIFY | 2 |

Что это значит: контрактов достаточно, чтобы начинать этап 1. Ни один `MISSING`
не блокирует этапы 1–2; блокируют только `BLOCKED` (DeepSeek) — но он нужен
к этапу 5, а не раньше. `CONTRADICTION` (REQ-032) надо снять до этапа 4a,
иначе тесты будут проверять не то правило.
