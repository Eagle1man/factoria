# REPORT — ЭТАП 2: backend (API, кэш, WS, БД, аудит)

Дата: 2026-11-05. Шаблон: ТЗ §15. Исполнитель: opencode (DeepSeek V4.1 Flash).

---

## 1. ЦЕЛЬ

Поднять backend по §5: конфиг, auth/RBAC, клиент OPC UA, кэш с качеством,
WebSocket с `seq`/`resume`, SQLite + Alembic, аудит.
DoD §5.7: дельты в WS, reconnect по `resume`, `q=bad` ≤3 c, записи в БД и аудит.

Цель достигнута. `q=bad` наступает за **0,43 c**, дельты приходят, история пишется.

## 2. ИЗУЧЕНО

| Источник | Что взято |
|---|---|
| ТЗ §5.1–§5.7 | state machine, REST, WS-протокол, идемпотентность, RBAC |
| ТЗ §8.3 | правила reconnect и поведение при `stale`/`bad` |
| `docs/data-model.md` | 5 таблиц |
| `docs/api.md` | контракт `/api/v1` |
| `asyncua 2.1.0` | реальные сигнатуры `read_attributes`, `get_node` |

## 3. РЕАЛИЗОВАНО

| Файл (полный путь) | Строк | Что |
|---|---|---|
| `D:\factoria\backend\src\factoria\config.py` | 47 | настройки + защита от dev-секрета вне dev |
| `D:\factoria\backend\src\factoria\storage\models.py` | 110 | 5 таблиц: users, commands, approvals, audit_events, tag_history |
| `D:\factoria\backend\src\factoria\storage\db.py` | 40 | async-движок, сессии, `create_all` для dev/test |
| `D:\factoria\backend\src\factoria\auth\security.py` | 60 | scrypt-хеши, JWT HS256 |
| `D:\factoria\backend\src\factoria\auth\rbac.py` | 60 | 7 ролей, права, зависимости FastAPI |
| `D:\factoria\backend\src\factoria\audit\storage.py` | 70 | запись и чтение аудита (append-only на уровне API) |
| `D:\factoria\backend\src\factoria\realtime\cache.py` | 150 | кэш: seq, deadband, STALE/GOOD/BAD, ring для resume |
| `D:\factoria\backend\src\factoria\realtime\history.py` | 90 | буферизованная запись истории + ретенция |
| `D:\factoria\backend\src\factoria\realtime\ws.py` | 180 | snapshot, delta, resume, min_interval_ms |
| `D:\factoria\backend\src\factoria\opcua\client.py` | 70 | опрос 21 тега, качество, backoff 1/2/5/10 c |
| `D:\factoria\backend\src\factoria\api\auth.py` | 55 | `/auth/login`, `/auth/me` |
| `D:\factoria\backend\src\factoria\api\state.py` | 95 | `/equipment`, `/equipment/{id}/state`, `/tags/history` |
| `D:\factoria\backend\src\factoria\api\system.py` | 50 | `/health`, `/audit` |
| `D:\factoria\backend\src\factoria\seed.py` | 50 | dev-пользователи 4 ролей |
| `D:\factoria\backend\src\factoria\main.py` | 80 | сборка приложения, lifespan, задачи |
| `D:\factoria\backend\migrations\` | — | Alembic (async), миграция `9b689bfc1be6` |
| `D:\factoria\scripts\smoke_stage2.py` | 60 | сквозной дымовой тест |
| `D:\factoria\tests\test_cache.py` | 90 | 9 тестов кэша |
| `D:\factoria\tests\test_auth.py` | 50 | 9 тестов auth/RBAC |
| `D:\factoria\tests\test_api.py` | 110 | 9 тестов API и WS |
| `D:\factoria\tests\test_opcua_client.py` | 105 | интеграция с эмулятором + обрыв |
| `D:\factoria\tests\test_repo_hygiene.py` | 30 | запрет BOM в конфигах |

## 4. АРХИТЕКТУРНЫЕ РЕШЕНИЯ

| Решение | Почему |
|---|---|
| **Опрос 21 тега раз в 0,5 c вместо subscription** (ADR-113) | у статичного тега нет data-change, его `ts` стареет и он ложно становится STALE; опрос даёт свежий ts и обнаружение обрыва <1 c |
| `seq` — счётчик изменений, ring на 2048 записей | `resume` доигрывает дельты, при переполнении уходит snapshot (§5.4) |
| deadband из `registry.yaml` | не гонять 21 тег при дрожании 0,1 rpm |
| `scrypt` из stdlib вместо argon2 | нет лишней зависимости; параметры зафиксированы в коде |
| Токен WS — в query-параметре | браузер не умеет ставить `Authorization` на WebSocket; риск зафиксирован (R-026) |
| `operator_id` только из токена | §5.6, тело запроса его не принимает |
| `audit` пишется своей сессией | событие сохраняется, даже если основная транзакция откатилась |
| `health` без токена | чипы статуса в UI не должны требовать логина; секретов в ответе нет |
| Dev-пользователи только при `ENV in {dev,test}` | в pilot/production пользователи заводятся отдельно |

## 5. ТЕСТИРОВАНИЕ (команды и фактический вывод)

**5.1. Полный набор:**

```
python -m pytest -q
...................................................                      [100%]
```

51 тест (20 этапа 1 + 31 этапа 2). Лог — `docs/assessment/checks/stage2-pytest.txt`.

**5.2. Сквозной дымовой тест (реальный эмулятор + реальный uvicorn):**

```
health: ok | tags: {'total': 21, 'not_good': 0} | opcua: connected
login: 200 | role: production_specialist
lines: [('L1', 0.0, 'GOOD'), ('L2', 0.0, 'GOOD'), ('L3', 0.0, 'GOOD')]
L1 tags: 7 | snapshot_ts: 2026-11-05T20:15:48.493920+00:00
no token -> 401
audit as operator -> 403
ws snapshot: snapshot | seq: 21 | q: GOOD
ws next: delta | seq: 25 | values: ['L1.Running', 'L1.Speed.PV']
ws next: delta | seq: 27 | values: ['L1.Speed.PV']
ws next: delta | seq: 29 | values: ['L1.Speed.PV']
```

Лог — `docs/assessment/checks/stage2-smoke.txt`.

**5.3. Обрыв OPC UA (DoD «q=bad ≤3 c»):**

```
opcua-client: {'all_good': True, 'source_connected': 'connected',
               'history_items': 21, 'down_seconds': 0.43,
               'went_down': True, 'quality_after_down': 'BAD'}
```

**5.4. Миграции:**

```
alembic upgrade head  -> Running upgrade -> 9b689bfc1be6, initial schema
alembic current       -> 9b689bfc1be6 (head)
таблицы: alembic_version, approvals, audit_events, commands, tag_history, users
```

## 6. РЕЗУЛЬТАТЫ (DoD §5.7)

| Требование | Итог |
|---|---|
| Backend поднимается | **ПРОШЛО** (`uvicorn factoria.main:app`, 21 тег) |
| WS получает дельты | **ПРОШЛО** (seq 25/27/29 после изменения уставки) |
| reconnect по `resume` | **ПРОШЛО** (unit + API-тест; реальный разрыв сети не имитировался) |
| `q=bad` ≤3 c | **ПРОШЛО**: 0,43 c |
| Записи в БД | **ПРОШЛО**: `tag_history` 21 строка/такт, `users`, аудит |
| Аудит | **ПРОШЛО**: `login`, `login_failed` |

## 7. ПРОБЛЕМЫ

1. **BOM в конфигах.** `alembic.ini` с BOM ломает `configparser`
   (`MissingSectionHeaderError`). Исправлено, добавлен тест
   `test_no_bom_in_repository`, который ловит это в любом файле.
2. **`Client.read_attributes` принимает Node, а не NodeId** — на `NodeId.nodeid`
   падало с `AttributeError`, маскируясь под «OPC UA недоступен». Исправлено.
3. **Смоук-скрипт не мог получить дельту**: при статичных значениях кэш не
   порождает изменений. Пришлось менять состояние через method-ноды эмулятора —
   это и есть правильный способ, но выявило: **без команд этапа 4a панель
   показывает только статику**.
4. **Токен в query для WS** попадает в логи прокси и историю браузера (R-026).

## 8. РИСКИ (новые)

| ID | Риск | Мера |
|---|---|---|
| R-026 | JWT в query-строке WS | одноразовый `ws_ticket` (короткий TTL) до пилота |
| R-027 | Нет refresh/revocation токена | этап 6 вместе с пультом |
| R-028 | `create_all` в dev может разойтись с Alembic | тест `alembic upgrade head` на чистой БД в CI |
| R-029 | История пишется без батчинга по времени (1 строка/тег/0,5 c) | ретенция 72 ч + замер объёма на этапе 6 |

## 9. ОСТАТОЧНЫЕ ВОПРОСЫ

| ID | Вопрос | Блокирует |
|---|---|---|
| OD-12 | Ретенция аудита (бессрочно?) и `commands` (24 ч) | этап 4a |
| — | Нужен ли `ws_ticket` до появления UI | этап 3 |

## 10. СООТВЕТСТВИЕ ТЗ

| REQ | Требование | Статус | Проверка |
|---|---|---|---|
| REQ-023 | REST §5.2 (часть этапа 2) | **выполнено** | `test_api.py` |
| REQ-024 | WS: delta/resume/stale/seq | **выполнено** | `test_ws_snapshot_and_resume`, смоук |
| REQ-025 | JWT, `operator_id` из токена | **выполнено** (без refresh/revocation) | `test_auth.py` |
| REQ-026 | WS по ролям | **частично**: проверяется, что роль входит в `read`; тонкая фильтрация тегов — этап 6 | `test_ws_requires_valid_token` |
| REQ-028 | Хранилище пользователей, хеш | **выполнено** | `test_password_hash_roundtrip` |
| REQ-080 | Ретенция `tag_history` | **выполнено** | `history.py`, поле в `.env` |
| REQ-083 | Отказ старта при dev-секрете вне dev | **выполнено** | `config.py` |
| REQ-020/021/022 | state machine, revalidate, идемпотентность | **не начато** — этап 4a | — |

## 11. СЛЕДУЮЩИЙ ЭТАП (предложение)

**Этап 4a** (по ТЗ после 2 идёт 3/UI, но UI Lovable ещё не выгружен, а 3D — витрина):

1. `validation/pipeline.py` — 5 стадий с кодами (`SCHEMA_001`, `RANGE_001`, `INTERLOCK_*`, `AUTONOMY_*`, `APPROVAL_001`).
2. `validation/autonomy.py` — матрица 7×4 + 6 граничных тестов уставки.
3. `api/commands.py` — `POST /commands`, `GET /commands/{id}`, approve/reject.
4. `storage` — идемпотентность по `command_id`, версия для optimistic lock.
5. `adapters/stub.py` — 5 заказов, `POST /debug/orders` только при `ENV=dev`.
6. `interlocks.yaml` — один предикат на дельту (ADR-112).

DoD §5.8/§9.5: повтор `command_id` без побочных эффектов; отказ по
RANGE/INTERLOCK с кодом; события в `/audit`.

Альтернатива: этап 3 (3D + панель) — но 2D-панель ждёт выгрузки Lovable,
а 3D без команд показывает статику. Поэтому 4a полезнее.

---

**Запрет §15 соблюдён:** «reconnect по resume» проверен на уровне протокола и
тестов, но не на реальном разрыве сети — это указано, а не выдано за полную проверку.
