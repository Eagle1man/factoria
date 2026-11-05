# DATA-MODEL.md — сущности и состояния (DRAFT, этап 0)

ТЗ §5.5 требует транзакционной БД, но схемы таблиц не приводит. Ниже —
минимальный набор для v1, покрывающий идемпотентность, аудит, согласования
и историю тегов. InfluxDB в v1 не используется (ADR-110).

## 1. `users`

| Поле | Тип | Примечание |
|---|---|---|
| `id` | UUID, PK | |
| `username` | TEXT, UNIQUE | |
| `password_hash` | TEXT | argon2id; в ТЗ не описано — добавлено |
| `role` | TEXT | 7 ролей §5.6 |
| `is_active` | BOOL | |
| `created_at` | TIMESTAMP | UTC |

Сидовый пользователь для dev — только при `ENV=dev`, пароль из переменной,
не хардкод.

## 2. `commands`

| Поле | Тип | Примечание |
|---|---|---|
| `command_id` | UUIDv7, PK | генерирует вызывающая сторона |
| `type` | TEXT | `set_setpoint` \| `switch_recipe` \| `line_start` \| `line_stop` \| `reallocate_job` |
| `target_line` | TEXT | L1…L3 |
| `params` | JSON | типизируется Pydantic-union |
| `requested_by_kind` | TEXT | `agent` \| `human` |
| `requested_by_id` | TEXT | |
| `agent_session_id` | UUID, NULL | |
| `correlation_id` | UUID | сквозной, попадает в аудит |
| `status` | TEXT | см. §5.1 ТЗ |
| `autonomy_level` | TEXT | A0…A3, вычислено валидатором |
| `validation_trace` | JSON | список стадий с кодами |
| `version` | INT | оптимистичная блокировка для approve/reject |
| `expires_at` | TIMESTAMP | TTL 5 мин на AWAITING_APPROVAL |
| `created_at`, `updated_at` | TIMESTAMP | UTC |

Индексы: `UNIQUE(command_id)`, `(status, created_at)`, `(correlation_id)`.
Ретенция строк — не меньше 24 ч (§5.5); очистка отдельной задачей,
аудит при этом не удаляется.

## 3. `approvals`

| Поле | Тип |
|---|---|
| `id` | UUID, PK |
| `command_id` | FK → commands |
| `operator_id` | FK → users |
| `decision` | `approve` \| `reject` |
| `comment` | TEXT, NOT NULL для reject |
| `decided_at` | TIMESTAMP |

`operator_id` берётся **из JWT**, не из тела запроса (§5.6).

## 4. `audit_events`

| Поле | Тип |
|---|---|
| `id` | BIGSERIAL / INTEGER PK |
| `ts` | TIMESTAMP UTC |
| `kind` | `command` \| `validation` \| `approval` \| `execution` \| `agent` \| `auth` \| `system` |
| `actor` | TEXT (user или agent session) |
| `action` | TEXT |
| `subject` | TEXT (command_id, tag, order_id) |
| `payload` | JSON |
| `correlation_id` | UUID |

Только append. Обновление и удаление запрещены на уровне репозитория.

## 5. `tag_history`

| Поле | Тип |
|---|---|
| `ts` | TIMESTAMP, PK часть |
| `tag` | TEXT, PK часть |
| `value` | REAL / TEXT |
| `quality` | `GOOD` \| `BAD` \| `STALE` |

Ретенция `TAG_HISTORY_RETENTION_H` (по умолчанию 72 ч). Без неё SQLite растёт
на гигабайты за сутки: 21 тег × 2 Гц × 86400 ≈ 3,6 млн строк/сутки.

## 6. `orders` (stub, этап 4a)

`order_id`, `product`, `qty`, `priority`, `due_date`, `spec_id`, `source`
(`stub` \| `1c`), `fetched_at`. Кэш 30 c (§5.2).

## 7. `agent_sessions`

| Поле | Тип |
|---|---|
| `id` | UUID, PK |
| `role` | orchestrator \| production \| logistics \| analyst |
| `strategy` | sequential \| supervisor \| debate |
| `state` | JSON (чекпоинт LangGraph) |
| `tokens_used` | INT |
| `tool_rounds` | INT |
| `started_at`, `ended_at` | TIMESTAMP |

Чекпоинты LangGraph — `SqliteSaver` в той же БД (§7.3), отдельная таблица.

## 8. Чего в модели нет и почему

- **Нет таблицы `twin_versions`** в v1: цифровой двойник появляется после
  этапа 2, контракт ещё не определён.
- **Нет `sim_runs`** в v1: песочница — этап 8.
- **Нет `production_plan`**: запись в 1С исключена (ADR-107).

Оба первых пункта нужны 2D-панели (экраны «Двойник» и «Эксперименты»), поэтому
это открытое решение OD-07 в `docs/assessment/open-decisions.md`.
