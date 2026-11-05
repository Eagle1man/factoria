# REPORT — ЭТАП 4a: команды, валидатор и stub-1С

Дата: 2026-11-06. Шаблон: ТЗ §15. Исполнитель: opencode (DeepSeek V4.1 Flash).

---

## 1. ЦЕЛЬ

Закрыть DoD §5.8/§9.5: повтор `command_id` без побочных эффектов, отказ по
RANGE/INTERLOCK с кодом, события в `/audit`. Плюс контракт команд (ADR-116)
и allowlist целей (EXT-2).

Цель достигнута: команда проходит путь `PROPOSED → AWAITING_APPROVAL →
DISPATCHING → EXECUTED`, отказ возвращает код, повтор идемпотентен.

## 2. ИЗУЧЕНО

| Источник | Что взято |
|---|---|
| ТЗ §5.1–§5.5, §6.1–§6.5, §9.1–§9.5 | состояния, стадии, коды, адаптер 1С |
| `docs/autonomy-matrix.md` | пороги A2: Δ≤60, target≤400 |
| `docs/assessment/external-projects.md` | контракт-first (EXT-1), allowlist (EXT-2) |
| `IndustriAgents/OPCUA-MCP` (MIT) | идея единого `contract` и профилей |

## 3. РЕАЛИЗОВАНО

| Файл (полный путь) | Что |
|---|---|
| `backend\src\factoria\contract\commands.json` | 5 команд: параметры, границы, риск, `evidence` |
| `backend\src\factoria\contract\loader.py` | загрузка контракта, динамические Pydantic-модели, проверка конверта |
| `backend\src\factoria\validation\pipeline.py` | 5 стадий с кодами и трассой |
| `backend\src\factoria\validation\autonomy.py` | коридор A2: Δ≤60, target≤400, GOOD, Temp≤80, Load≤95 |
| `backend\src\factoria\validation\interlocks.yaml` | 3 правила: дельта, перегрев, перегруз |
| `backend\src\factoria\opcua\commands.py` | исполнение через method-ноды |
| `backend\src\factoria\api\commands.py` | submit/list/get/approve/reject, TTL 5 мин, версия |
| `backend\src\factoria\api\orders.py` | заказы stub + `POST /debug/orders` только dev |
| `backend\src\factoria\adapters\{base,stub}.py` | 5 заказов, только чтение |
| `scripts\smoke_stage4a.py` | сквозной тест 4a |

## 4. АРХИТЕКТУРНЫЕ РЕШЕНИЯ

| Решение | Почему |
|---|---|
| Контракт команд в JSON, модели генерируются | одна правда для backend, агента и UI; CI ловит расхождение (ADR-116) |
| Allowlist целей `ALLOWED_WRITE_TARGETS` | даже при A2 команда на линию вне списка отклоняется (EXT-2) |
| A1 по умолчанию, A2 за флагом | политика «человек подтверждает» сохраняется (ADR-103) |
| Отказ — `422 {stage, code, detail}` | ТЗ §5.2; UI может показать стадию, а не текст |
| Повтор `command_id` — текущий статус + `duplicate: true` | идемпотентность §5.5 |
| `version` в approve/reject | защита от двойного подтверждения устаревшей карточки |
| TTL вычисляется лениво при чтении | нет фоновой задачи, `EXPIRED` появляется при первом обращении |
| Исполнение — отдельное подключение к OPC UA на команду | простота; цена ~50 мс, для 4a приемлемо |

## 5. ТЕСТИРОВАНИЕ (фактический вывод)

**5.1. Набор тестов:**

```
python -m pytest -q
........................................................................ [ 66%]
.....................................                                    [100%]
```

109 тестов (68 было + 41 новых: контракт 7, валидация 16, API команд 12,
адаптеры 4, исполнение 1, конфиг 1). Полный лог — `checks/stage4a-pytest.txt`.

**5.2. Сквозной смоук (реальный backend + эмулятор, `checks/stage4a-smoke.txt`):**

```
login: 200 production_specialist
orders: stub 5
submit: 202 {'status': 'AWAITING_APPROVAL', 'autonomy_level': 'A1', 'expires_in': 300, 'duplicate': False}
duplicate: 202 {'status': 'AWAITING_APPROVAL', 'duplicate': True}
interlock: 422 {'stage': 'interlock_check', 'code': 'INTERLOCK_001', 'detail': 'скачок уставки больше 800 rpm'}
approve: 200 {'status': 'EXECUTED', 'detail': 'EXECUTED'}
state: 200 EXECUTED
L1.Speed.SP: 300.0 q: GOOD
audit: [('auth','login'), ('execution','executed'), ('command','rejected'), ('command','accepted')]
```

**5.3. Реальное исполнение через OPC UA** (`tests/test_dispatch.py`):
`line_start` → `EXECUTED`, `set_setpoint(300)` → уставка на линии 300,
`switch_recipe("R4")` → рецепт R4, `switch_recipe("R9")` → `BadOutOfRange`.

## 6. DoD §5.8 / §9.5

| Требование | Итог |
|---|---|
| Повтор `command_id` без побочных эффектов | **ПРОШЛО** (возвращается текущий статус) |
| Отказ по RANGE с кодом | **ПРОШЛО** (`RANGE_001`, линия L9) |
| Отказ по INTERLOCK с кодом | **ПРОШЛО** (`INTERLOCK_001/002/004`) |
| Данные stale → отказ | **ПРОШЛО** (`DATA_STALE`) |
| События в `/audit` | **ПРОШЛО** (`command accepted/rejected`, `execution executed`) |
| Stub-1С: 5 заказов | **ПРОШЛО** |
| A1: без подтверждения не исполняется | **ПРОШЛО** (статус `AWAITING_APPROVAL`) |

## 7. ПРОБЛЕМЫ

1. **`lru_cache` на модели параметров** падал с `unhashable type`: `Contract`
   содержит dict. Заменено на явный кэш по типу команды.
2. **Время в SQLite приходит naive** — добавлено приведение к UTC в чтении.
3. **Кэш тегов обновляется раз в 0,5 c**: сразу после approve `Speed.SP` ещё
   показывает старое значение. В смоуке добавлена пауза 1,2 c; в UI это будет
   выглядеть как «команда исполнена, значение обновится через такт».
4. **A2 проверен только юнит-тестами** — в API при `AUTONOMY_MAX=A2` не
   прогонялся ни один сценарий (следующий этап).

## 8. РИСКИ

| ID | Риск |
|---|---|
| R-033 | Отдельное подключение к OPC UA на каждую команду: при потоке команд вырастет задержка и число сессий |
| R-034 | `commands` растёт без ретенции; TTL удаляет статус, но строки остаются (OD-12) |
| R-035 | Нет rate limit на `POST /commands`: агент может засыпать очередь |
| R-036 | UI ещё не умеет approve/reject — экран «Согласования» остаётся заглушкой |

## 9. СЛЕДУЮЩИЙ ШАГ

**Этап 6 (валидатор 4–5 в API + пульт) или UI-часть 2.** Рекомендую UI:
подключить экраны «Согласования» и «Документы» к готовым `/commands` и `/orders`,
затем проверить A2 на реальном сценарии через API.

---

**Запрет §15 соблюдён:** A2 в API не проверялся — это указано, а не заявлено.
