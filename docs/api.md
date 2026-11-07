# API.md — контракт v1 (DRAFT, этап 0)

База: `/api/v1`. Формат ошибок: `422/4xx {stage, code, detail}` (§5.2).
Все временные метки — ISO 8601 UTC.

## 0. Статус реализации (2026-11-06)

| Реализовано | Не реализовано |
|---|---|
| `POST /auth/login`, `GET /auth/me` | 7 PLANNED путей под 2D-панель (§5) |
| `GET /equipment`, `GET /equipment/{id}/state`, `GET /tags/history` | `GET /agents/sessions`, `/twin`, `/sim/runs` |
| `POST /commands`, `GET /commands`, `GET /commands/{id}` | `command_status` / `command_resolved` в WS |
| `POST /commands/{id}/approve`, `/reject` (A1, TTL 5 мин) | уведомление оператору при A2 |
| `GET /orders`, `GET /orders/{id}`, `POST /debug/orders` (только dev) | HTTP-сервисы 1С (этап 4b) |
| `GET /twin` (структура, покрытие, свежесть) | расписание снимков |
| `GET /twin/history` (срезы и дельты) | сравнение двух произвольных срезов в UI |
| `POST /twin/snapshot` (роль operator) | |
| `GET /health`, `GET /audit`, `WS /ws` | |

Команды исполняются через method-ноды эмулятора: `set_setpoint → SetSpeed`,
`switch_recipe → SetRecipe`, `line_start/stop → StartLine/StopLine`,
`reallocate_job → ReallocateJob`.
Ошибки валидации: `422 {stage, code, detail}`; повтор `command_id` возвращает
текущий статус с `duplicate: true`.

## 1. Аутентификация

| Метод | Путь | Тело | Ответ |
|---|---|---|---|
| POST | `/auth/login` | `{username, password}` | `{access_token, role, expires_in}` |
| GET | `/auth/me` | — | `{user_id, role}` |

`operator_id` всегда берётся из токена. В теле запроса его быть не должно.

## 2. Оборудование и теги

| Метод | Путь | Ответ |
|---|---|---|
| GET | `/equipment/{id}/state` | `{values: {tag: {v, q, ts}}, snapshot_ts}` |
| GET | `/equipment` | список линий L1…L3 со статусом |
| GET | `/tags/history?tag&from&to&max_points` | `[[ts, v, q], …]` |

`q ∈ GOOD | BAD | STALE`. `STALE` — нет обновления дольше `2 × max_age_seconds`.

## 3. Команды

| Метод | Путь | Тело | Ответ |
|---|---|---|---|
| POST | `/commands` | §5.3 ТЗ | `202 {command_id, status, autonomy_level}` |
| GET | `/commands/{id}` | — | `{status, validation_trace[], approval?}` |
| POST | `/commands/{id}/approve` | `{version, comment?}` | `{status}` |
| POST | `/commands/{id}/reject` | `{version, reason}` | `{status}` |
| GET | `/commands?status&from&to&limit` | — | список (нужен 2D-панели) |

Состояния — §5.1: `PROPOSED → VALIDATING → [REJECTED] → AWAITING_APPROVAL → APPROVED → REVALIDATING → DISPATCHING → EXECUTED | FAILED | TIMEOUT | CANCELLED | EXPIRED | REJECTED_AT_REVALIDATION`.

## 4. Заказы и аудит

| Метод | Путь | Примечание |
|---|---|---|
| GET | `/orders/{id}` | из 1С, кэш 30 c |
| GET | `/orders?status=open` | `list_open_orders` |
| GET | `/audit?kind&actor&from&to&limit&cursor` | пагинация |

## 5. Пробелы под 2D-панель (предложение)

ТЗ §5.2 этих путей не содержит, но 9 экранов Lovable-UI без них не собрать.
Помечены как **PLANNED**, реализуются вместе с этапом 3:

| Метод | Путь | Для экрана |
|---|---|---|
| GET | `/health` | чипы статуса 1С / SCADA / агенты |
| GET | `/agents/sessions?active=true` | «Агенты и трассы» |
| GET | `/agents/sessions/{id}/trace` | таймлайн трассы |
| GET | `/twin` | «Цифровой двойник» (этап 2+) |
| GET | `/sim/runs`, GET `/sim/runs/{id}` | «Эксперименты» (этап 8) |
| GET | `/commands?status=AWAITING_APPROVAL` | «Согласования» |
| GET | `/settings` | «Настройки» (только чтение флагов, без секретов) |

Альтернатива — оставить панель на 6 экранах (§8.4). Решение — OD-03.

## 6. WebSocket `/ws`

```jsonc
{"type":"subscribe","tags":["L1.Speed.PV"],"delta_only":true,"min_interval_ms":100}
{"type":"resume","last_seq":10231}
{"type":"snapshot","seq":10231,"values":{"L1.Speed.PV":{"v":712.4,"q":"good","ts":"…"}}}
{"type":"delta","seq":10232,"values":{"L1.Speed.PV":{"v":712.9}}}
{"type":"command_status","command_id":"…","status":"AWAITING_APPROVAL"}
{"type":"command_status","command_id":"…","status":"EXECUTED","autonomy_level":"A2","line_id":"L2"}
{"type":"error","code":"stale","tags":["L3.Load.Pct"]}
```

Правила: дельта не чаще `min_interval_ms`; `resume` с `last_seq`; `stale` при
отсутствии обновлений дольше `2 × max_age_seconds`; `seq` — uint32 с
переполнением; подписка фильтруется по роли из JWT; пульт оператора —
отдельная ветка.

## 7. Коды ошибок

| Код | Смысл |
|---|---|
| `SCHEMA_001…` | не прошла схема |
| `RANGE_001` | значение вне диапазона тега |
| `INTERLOCK_001…` | запрет физики/процесса |
| `AUTONOMY_001` | A0 — действие запрещено роли |
| `APPROVAL_001` | требуется подтверждение (A1) |
| `APPROVAL_TTL_EXPIRED` | истёк TTL 5 мин |
| `REVALIDATION_FAILED` | условия изменились перед исполнением |
| `DUPLICATE_SUPPRESSED` | повтор `command_id`, возвращён текущий статус |
| `BUDGET_EXHAUSTED` | лимит токенов/раундов агента |

| `GET /twin/compare?a=&b=` (любые два среза) | |
