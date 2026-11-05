markdown
# ТЕХНИЧЕСКОЕ ЗАДАНИЕ
# FACTORIA & AI — мультиагентная система управления производственными процессами предприятия

**Версия:** 2.1 (development-ready, complete)  
**Дата:** 05.11.2026  
**Имя проекта:** FACTORIA & AI  
**Репозиторий:** `factoria/` (новый, рядом с `agent-1c-demo`)  
**Целевая модель:** DeepSeek V4.1 Flash (`deepseek-flash`)  
**Целевая платформа предприятия:** 1С:Предприятие  
**Статус:** передан opencode для обследования и поэтапной реализации

> Документ объединяет стратегическую программу и инженерные контракты. Все спорные места закрыты. Работать строго по этапам (раздел 12). Первое задание — только обследование (раздел 14), без кода.

---

## 0. Зафиксированные решения (ответы на открытые вопросы)

| # | Вопрос | Решение | Обоснование |
|---|---|---|---|
| 1 | Новый репозиторий или замена? | **Новый `factoria/`, рядом.** `agent-1c-demo` продолжает работать | Big-bang убьёт работающий демо-контур; параллельная разработка даёт страховку |
| 2 | Внешний API по умолчанию? | **`ALLOW_EXTERNAL_API=false` по умолчанию.** Для dev/research — `true` с явным комментарием | Безопасность и совместимость с ADR-005 (offline-only). Облачная модель — только осознанно |
| 3 | A1 или A2? | **A2 разрешён с жёсткими границами** (Δ≤5%, ≤400, interlocks OK, `q=GOOD`, только `set_setpoint`). Остальное — A1 | Автономия только в безопасном коридоре; всё остальное — через человека |
| 4 | Lovable-UI? | **Lovable — 2D-панель нового backend.** 3D — отдельный экран | Переиспользуем существующее; 3D — «витрина», не замена 2D |
| 5 | Этапы 9–10? | **Вынесены в v2 roadmap.** В v1 — только dataclass-заглушка `ImprovementCandidate` без реализации | Нет контрактов и DoD — реализовывать «как получится» опасно |
| 6 | Docker? | **План B без Docker** (локальный запуск). FUXA/InfluxDB откладываются | Не блокирует старт; контракты не меняются |
| 7 | 1С: мост или HTTP? | **HTTP-сервисы (BSL + расширение).** На первом шаге — stub | Правильнее; opencode пишет BSL, вы публикуете |
| 8 | Параллельная разработка | **Да.** `agent-1c-demo` не трогаем | Страховка; Lovable переиспользуется как 2D-панель |

---

## 1. Цель и границы

### 1.1. Цель
Создать мультиагентную систему, в которой LLM-агенты (DeepSeek V4.1 Flash, strict mode) управляют производственными процессами через мост **«1С ↔ FastAPI ↔ SCADA/OPC UA»**, с браузерной 3D-визуализацией, цифровым двойником и симуляционной песочницей. Конечная цель — не чат-бот, а **интеллектуальный помощник**, понимающий состояние предприятия, анализирующий процессы, проверяющий решения на двойнике и помогающий сотрудникам управлять производством.

### 1.2. Что входит в v1
- Сквозной контур: заказ → планирование → валидация → A1 (подтверждение) / A2 (автономно в границах) → исполнение → обратная связь → 3D.
- Агентная оркестрация (DeepSeek, strict mode, 4 роли: orchestrator, production, logistics, analyst).
- Интеграция с 1С через **HTTP-сервисы** (BSL + расширение); на первом шаге — stub.
- Телеметрия через OPC UA (эмулятор + реальный контур позже).
- Веб-HMI: 3D-станок (React + R3F) + 2D-панель (Lovable).
- Симуляционная песочница (Satisfactory) — после работающего вертикального среза.

### 1.3. Что не входит в v1
- Замена SCADA/ПЛК.
- Прямая запись LLM в ПЛК.
- Реальная 1С на этапах 0–4a (только stub).
- MQTT/Mosquitto (этап 8, опционально).
- SSO (v1 — JWT, `operator_id` из токена).
- TLS/сертификаты OPC UA (v1 — `SecurityPolicy None`, dev only).
- Этапы 9–10 (самоулучшение, sim-to-real) — v2 roadmap.
- Запись в 1С (`update_production_plan`) — после отдельного ADR.

### 1.4. Ключевой принцип безопасности
**«Модель предлагает — backend авторизует и исполняет».** LLM никогда не пишет в ПЛК напрямую. Четыре уровня защиты разделены:

| Уровень | Где живёт | Кто управляет |
|---|---|---|
| Физические блокировки (interlocks) | ПЛК / эмулятор OPC UA | Инженер АСУ ТП |
| Программные ограничения интеграционного слоя | Backend-мост | Разработчик |
| Бизнес-ограничения процессов | 1С / валидатор | Владелец процесса |
| Политики автономности ИИ | Матрица автономности (раздел 6.4) | Руководитель проекта |

LLM не может отменить ни один из четырёх уровней. `emergency_stop` и Safety-interlocks недоступны LLM вообще (уровень A0).

---

## 2. Структура монорепозитория `factoria/`
factoria/
├── docker-compose.yml
├── .env.example
├── README.md
├── opencode.jsonc
├── pyproject.toml
├── docs/
│ ├── specification.md
│ ├── tag-registry.md
│ ├── autonomy-matrix.md
│ ├── data-model.md
│ ├── api.md
│ ├── decisions.md
│ ├── risks.md
│ └── assessment/
│ ├── repository-audit.md
│ ├── architecture-assessment.md
│ ├── technology-stack.md
│ ├── requirements-traceability.md
│ ├── risks.md
│ ├── open-decisions.md
│ ├── implementation-roadmap.md
│ ├── pilot-scenario-proposals.md
│ └── deepseek-spike.md
├── opcua-emulator/
│ ├── Dockerfile
│ └── emulator.py
├── backend/
│ ├── Dockerfile
│ ├── pyproject.toml
│ └── src/factoria/
│ ├── main.py
│ ├── config.py
│ ├── auth/{jwt.py,rbac.py}
│ ├── tags/{registry.py,registry.yaml}
│ ├── opcua/client.py
│ ├── realtime/{cache.py,ws.py}
│ ├── api/{state.py,commands.py,orders.py,audit.py}
│ ├── validation/{pipeline.py,interlocks.yaml,autonomy.py}
│ ├── audit/{events.py,storage.py}
│ ├── adapters/{base.py,stub.py,http_ones.py}
│ ├── simulator/adapter.py
│ └── storage/{db.py,migrations/}
├── agents/
│ ├── Dockerfile
│ ├── pyproject.toml
│ └── src/factoria_agents/
│ ├── client.py
│ ├── tools.py
│ ├── session.py
│ ├── graph.py
│ ├── roles/{prompts/,production.py,logistics.py,analyst.py}
│ └── strategies/{supervisor.py,debate.py,sequential.py}
├── frontend/
│ ├── Dockerfile
│ ├── package.json
│ └── src/{App.tsx,ws/client.ts,scene/,panel/}
└── ops/
├── influxdb/init.sh
└── mosquitto/

text

---

## 3. Стек и контуры

### 3.1. Стек (фиксирован)

| Слой | Технология | Обоснование |
|---|---|---|
| ПЛК-эмулятор | Python 3.11+, `asyncua` | Async, совместимость с backend |
| SCADA (витрина) | FUXA (Docker, опционально) | OPC UA, Modbus, MIT |
| Backend | Python 3.11+, FastAPI, `asyncua`, Pydantic v2 | Async, типобезопасность |
| Транзакционная БД | SQLite (dev) / PostgreSQL (pilot), SQLAlchemy + Alembic | Идемпотентность, аудит, состояние |
| TSDB | InfluxDB 2.x (опционально; на первом шаге — SQLite `tag_history`) | История тегов |
| LLM-агенты | Python, LangGraph (пиннинг), DeepSeek API | Инструменты, strict mode |
| 3D-frontend | Vite + React 18 + `@react-three/fiber` + `@react-three/drei` | Компонентный подход |
| 1С-адаптер | Интерфейс + stub (4a), HTTP-сервисы BSL (4b) | Независимость от конфигурации |
| Контейнеризация | Docker Compose (если есть; иначе — локально) | Гибкость |

### 3.2. Контуры и флаги (`.env.example`)

```bash
# LLM
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com/beta
LLM_PROVIDER=deepseek          # deepseek | local
ALLOW_EXTERNAL_API=false       # по умолчанию false; для dev/research — true

# OPC UA
OPCUA_ENDPOINT=opc.tcp://opcua-emulator:4840

# 1С
ONES_MODE=stub                 # stub | http
ONES_HTTP_URL=

# Симулятор
TARGET=opcua                   # opcua | satisfactory
SIMULATOR_POLL_INTERVAL_S=2

# БД
DATABASE_URL=sqlite+aiosqlite:///./data/factoria.db
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost/factoria

# Auth
JWT_SECRET=dev-secret-change-me
JWT_TTL_MIN=60

# Среда
ENV=dev                        # dev | pilot | production
Правило: при 
ALLOW_EXTERNAL_API=false
 агент работает в read-only режиме и не вызывает внешний API. Это сохраняет offline-only контур. Включать true — только осознанно, с записью в docs/decisions.md.

3.3. Настройка opencode для DeepSeek
jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "providers": {
    "deepseek": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "DeepSeek",
      "options": {
        "baseURL": "https://api.deepseek.com/beta",
        "apiKey": "{env:DEEPSEEK_API_KEY}"
      },
      "models": {
        "deepseek-flash": {
          "name": "DeepSeek V4.1 Flash",
          "tool_call": true,
          "limit": { "context": 1048576, "output": 393216 }
        }
      }
    }
  },
  "model": "deepseek/deepseek-flash"
}
Критично:

baseURL обязательно /beta — strict работает только через Beta-эндпоинт.

strict: true — в схеме каждого инструмента в коде, не в конфиге модели.

deepseek-flash — алиас; фактический ID — через GET /models.

thinking по умолчанию включён; для tool-calling отключать или reasoning_effort: low. tool_choice: required + thinking → 400.

minLength/maxLength/minItems/maxItems не поддерживаются и молча игнорируются.

3.4. Спайк DeepSeek (обязателен до кода агентов)
Результат — docs/assessment/deepseek-spike.md.

#	Проверить	Как	Если не работает
1	GET /models → deepseek-flash	curl -H "Authorization: Bearer $KEY" https://api.deepseek.com/beta/models	Взять актуальный ID; если пусто — LLM_PROVIDER=local
2	Strict mode работает	Один инструмент "strict": true, additionalProperties: false	Fallback: клиентская валидация Pydantic
3	tool_choice: required + thinking → 400	Оба параметра в запросе	Подтвердить: всегда отключать thinking
4	Thinking отключается	{"thinking": {"type": "disabled"}}	reasoning_effort: "low"
5	Контекст 1M / output 384K	Длинный input (~100K)	Скорректировать SessionBudget
6	Цена off-peak	3–5 вызовов, сверка с прайсом	Зафиксировать в отчёте
Оценка: 0.5–1 день. Блокирует только этап 5 (агенты).

3.5. План B без Docker
Компонент	Как запускать
OPC UA-эмулятор	python opcua-emulator/emulator.py
Backend	uvicorn factoria.main:app --reload (:8000)
БД	SQLite (./data/factoria.db)
История тегов	SQLite-таблица tag_history
FUXA	Отложена. Витрина — HTML-страница на GET /api/v1/equipment/{id}/state
Frontend	npm run dev (:5173)
4. OPC UA-эмулятор (этап 1)
4.1. Функции
Сервер asyncua на opc.tcp://0.0.0.0:4840, namespace urn:mfg:emulator. 3 линии (L1..L3).

4.2. Теги (21 = 7 × 3)
Тег	Тип	Диапазон	Поведение
Running	Boolean	—	run-цикл 500 мс
Speed.SP	Float	0–1200 об/мин	метод-нода SetSpeed(value) → StatusCode
Speed.PV	Float	0–1200	стремится к SP (τ=2 c)
Temp.PV	Float	20–120 °C	растёт ∝ (SP/1200)²
Load.Pct	Float	0–100	профиль normal/overload
Alarm.Code	UInt16	0–999	0 = нет; 100+ = стоп
Recipe.ID	String	R1..R5	метод-нода SetRecipe(recipe_id) → StatusCode
4.3. Safety-interlocks (в сервере, не в backend)
Temp.PV > 80 → SetSpeed(value > 400) → BadInvalidState, Alarm.Code=101.

Load.Pct > 95 дольше 60 c → Alarm.Code=102, автостоп.

SetRecipe не из R1..R5 → BadOutOfRange.

Паттерн записи: method-нода, не writable-переменная. Writable без callback не даёт отклонить запись. В asyncua — через method-call или переопределение AttributeService.

4.4. Дополнительные методы (обязательны)
SetSpeed(value), SetRecipe(recipe_id), StartLine(), StopLine(), ReallocateJob(job_id).
Без method-нод команды line_start, line_stop, reallocate_job некуда исполнять.

4.5. FUXA — read-only витрина
FUXA — только просмотр. Запись через неё запрещена. Иначе человек обходит валидатор, и принцип «backend — единственный путь исполнения» нарушается.

4.6. DoD этапа 1
FUXA (:1881) видит 21 тег.

SetSpeed(500) при Temp>80 отклоняется.

docs/tag-registry.md сгенерирован.

5. Backend: API, state machine, идемпотентность
5.1. State machine команд
text
PROPOSED → VALIDATING → [REJECTED]
VALIDATING → AWAITING_APPROVAL → APPROVED
VALIDATING → APPROVED                (A2)
VALIDATING → EXPIRED                 (TTL)
AWAITING_APPROVAL → EXPIRED          (TTL)
AWAITING_APPROVAL → REJECTED         (оператор)
APPROVED → REVALIDATING → [REJECTED_AT_REVALIDATION] | DISPATCHING
DISPATCHING → EXECUTED
DISPATCHING → FAILED | TIMEOUT
APPROVED → CANCELLED
Ключевое: APPROVED → REVALIDATING. Перед исполнением — повторная проверка interlocks и актуальности. Если за 5 минут условия изменились — команда отклоняется.

5.2. REST API (/api/v1)
Метод	Путь	Тело/Ответ	Примечание
POST	/auth/login	{username, password} → {access_token, role}	JWT
GET	/equipment/{id}/state	{values, snapshot_ts}	из кэша
POST	/commands	см. 5.3 → 202 {command_id, status}	идемпотентен
GET	/commands/{id}	{status, validation_trace[], approval?}	
POST	/commands/{id}/approve	{version, comment?}	operator_id из JWT
POST	/commands/{id}/reject	{version, reason}	
GET	/orders/{id}	заказ из 1С	кэш 30 c
GET	/audit	фильтры	пагинация
GET	/tags/history	[ts, v, q]	SQLite/Influx
Ошибки: 422 {stage, code, detail}, 404, 401, 403.

5.3. Тело POST /commands
json
{
  "command_id": "018f-uuid-v7",
  "type": "set_setpoint",
  "target": {"line_id": "L2"},
  "params": {"setpoint_value": 540},
  "requested_by": {"kind": "agent", "id": "logist#sess-77"},
  "agent_session_id": "uuid",
  "correlation_id": "uuid"
}
Pydantic discriminated union:

set_setpoint → setpoint_value: float

switch_recipe → recipe_id: enum[R1..R5]

line_start / line_stop → {}

reallocate_job → job_id: string

5.4. WebSocket /ws
jsonc
{"type":"subscribe","tags":["L1.Speed.PV"],"delta_only":true,"min_interval_ms":100}
{"type":"resume","last_seq":10231}
{"type":"snapshot","seq":10231,"values":{"L1.Speed.PV":{"v":712.4,"q":"good","ts":"..."}}}
{"type":"delta","seq":10232,"values":{"L1.Speed.PV":{"v":712.9}}}
{"type":"command_status","command_id":"...","status":"AWAITING_APPROVAL"}
{"type":"error","code":"stale","tags":["L3.Load.Pct"]}
Правила: дельта не чаще min_interval_ms; resume с last_seq; stale при отсутствии > 2× max_age_seconds; seq uint32 wraparound; подписки разграничены по ролям.

5.5. Идемпотентность (транзакционная)
command_id — UUIDv7, генерирует вызывающая сторона.

Хранится в БД (commands с UNIQUE), не в памяти.

Повтор в 24 ч → текущий статус (duplicate_suppressed).

In-memory cache — не единственный источник истины.

5.6. Auth/RBAC
POST /auth/login → JWT с role и user_id.

operator_id — из токена, не из тела.

Роли: project_lead, employee, enterprise_head, technologist, production_specialist, it_admin, auditor.

WS: подписка по роли; пульт — только operator/production_specialist.

5.7. DoD этапа 2
Backend поднимается, WS получает дельты, reconnect по resume, обрыв OPC UA → q="bad" ≤3 c, записи в БД и аудит.

5.8. DoD этапа 4a
Повтор command_id без побочных эффектов; отказ по RANGE/INTERLOCK с кодом; события в /audit.

6. Валидатор: 5 стадий
6.1. Конвейер
python
STAGES = [schema_check, range_check, interlock_check, autonomy_check, approval_gate]
#	Стадия	Проверки	Коды
1	schema_check	Pydantic, enum, discriminated union	SCHEMA_001..
2	range_check	Диапазон тега	RANGE_001
3	interlock_check	IF <условие> THEN prohibit; читает текущий кэш	INTERLOCK_001..
4	autonomy_check	Матрица 6.4 → A0–A3; A0 → отказ	AUTONOMY_001
5	approval_gate	A1 → WS-пуш, AWAITING_APPROVAL, TTL 5 мин; A2 → уведомление	APPROVAL_001
6.2. Interlocks (operational)
yaml
rules:
  - id: speed-delta-warn
    if: {tag: "{line}.Speed.SP", op: "<", value: 400 }
    prohibit: ["set_setpoint"]
    when: {param: setpoint_value, op: ">", value: 800 }
    code: INTERLOCK_003
  - id: job-already-reallocated
    if: {tag: "{line}.Load.Pct", op: ">", value: 95 }
    prohibit: ["reallocate_job"]
    code: INTERLOCK_004
Разрешение противоречия 400/800:

|Δ| > 400 → A1 (подтверждение), не отказ.

|Δ| > 800 → interlock (отказ).

Два порога для двух целей.

Физические interlocks (Temp>80, Load>95) — в эмуляторе/ПЛК, не здесь.

6.3. Уровни
A0 — запрет · A1 — подтверждение · A2 — автономно + уведомление · A3 — полная автономия (симуляция).

6.4. Матрица прав (v1: A2 с границами)
Действие \ роль	analyst	logistics	production	orchestrator
Чтение	A3	A3	A3	A3
set_setpoint Δ≤5% и ≤400	A0	A2	A2	A2
set_setpoint Δ>5% или >400	A0	A1	A1	A1
switch_recipe	A0	A1	A1	A1
line_start / line_stop	A0	A1	A1	A1
reallocate_job	A0	A1	A1	A1
emergency_stop	A0	A0	A0	A0 (LLM недоступно)
A2 разрешён только при одновременном выполнении всех условий:

Условие	Значение
Дельта уставки	≤ 5% диапазона (≤ 60 об/мин при 0–1200)
Новое значение	≤ 400 об/мин
Interlock	не нарушен (Temp ≤ 80, Load ≤ 95)
Данные	q = GOOD, не stale
Тип	только set_setpoint
Всё остальное → A1. Данные stale/bad → отказ (не A1, не A2).

При A2 оператор получает уведомление (не запрос), событие в аудит.

Юнит-тест на каждую ячейку матрицы. Хранить как data-driven dict.

6.5. Унификация порогов
Базовый: 400 (из registry.yaml, speed_threshold).

Δ > 5% или new > 400 → A1.

|Δ| > 800 → interlock.

6.6. Повторная валидация
На REVALIDATING:

interlocks по текущему кэшу;

q != stale/bad;

TTL не истёк.
Не прошло → REJECTED_AT_REVALIDATION, оператор уведомлён.

6.7. DoD этапа 6
Каждая ячейка матрицы — юнит-тест.

A1 → approve → REVALIDATING → EXECUTED.

A2 → без approve, но с уведомлением и аудитом.

TTL → EXPIRED.

Revalidate отклоняет при изменившихся условиях.

7. LLM-агенты DeepSeek V4.1 Flash
7.1. Клиент strict mode
Обязательно:

base_url=https://api.deepseek.com/beta.

Модель deepseek-flash (алиас; ID — из GET /models).

В каждом инструменте "strict": true.

Схемы: все поля required, additionalProperties: false, без patternProperties/format/minItems/minLength/числовых границ.

Thinking: для tool-calling отключать ({"thinking": {"type": "disabled"}}) или reasoning_effort: "low". tool_choice: required + thinking → 400.

Лимиты:

python
@dataclass
class SessionBudget:
    token_limit: int = 200_000
    tool_round_limit: int = 4
    decision_timeout_s: int = 120
    agent_turn_timeout_s: int = 30
Превышение → budget_exhausted, отказ (не «докручивать»).

7.2. Инструменты (8)
Инструмент	Режим	Схема (сокращённо)
get_line_state	read	{line_id: enum[L1,L2,L3], include_tags: array[enum]}
get_factory_summary	read	{lines: array[enum], metrics: array[enum]}
get_tag_history	read	{tag, from, to, max_points}
query_order	read	{order_id, fields: array[enum]}
propose_set_setpoint	write	{line_id, setpoint_value: float, justification, expected_effect, risk_self_assessment, evidence: array[tool_call_id]}
propose_switch_recipe	write	{line_id, recipe_id: enum[R1..R5], justification, expected_effect, risk_self_assessment, evidence}
propose_line_start_stop	write	{line_id, action: enum[start,stop], justification, expected_effect, risk_self_assessment, evidence}
propose_reallocate_job	write	{job_id, target_line_id, justification, expected_effect, risk_self_assessment, evidence}
Ключевое: отдельные инструменты вместо params: object; в каждом write — evidence. request_operator_attention удалён (approval gate уже реализует уведомление).

7.3. LangGraph-граф
text
perceive → route_strategy ──sequential──► run_role
                          ──supervisor─► orchestrator.call
                          ──debate────► debate(≤3)
            ▼
        propose_* (если действие)
            ▼
        POST /commands ── AWAITING_APPROVAL ─► interrupt()
            ▼
        report (аудит)
Checkpointing: SqliteSaver.

Деградация: 5xx/таймаут → read-only, уведомление, событие. Максимум 1 повтор с backoff.

7.4. Resume после approval
POST /approve пишет в БД.

Backend публикует command_resolved в WS агента.

Агент вызывает graph.resume(thread_id, checkpoint).

Если WS потерян — поллинг GET /commands/{id} каждые 5 c.

WS-сообщение — не доказательство подтверждения.

7.5. Стратегии
Ситуация	Стратегия
Мониторинг	sequential
Срочный заказ	supervisor
Конфликт интересов	debate (≤3)
Ничья	consensus (3 роли, эскалация)
Конфликты: критичность > confidence > специализация. Усреднение запрещено.

Жюри debate: production + logistics (2 голоса), модератор — orchestrator (не голосует). Ничья → consensus: production, logistics, analyst. Повторная ничья → эскалация (A1).

7.6. Роли
Роль	Модель	Ограничения
orchestrator	deepseek-flash	Не голосует в debate
production	deepseek-flash	A2 в границах; A1 на остальное
logistics	deepseek-flash	A2 в границах; A1 на остальное
analyst	deepseek-flash	A0 на write
Промпты — в roles/prompts/*.md: «Контекст завода», «Инструменты», «Ограничения» (не предлагать A0; всегда evidence), «Формат отчёта».

Роутинг: одна модель на сессию; переключение внутри хода запрещено.

7.7. DoD этапа 5
Summary строго по схеме; budget-стоп; кассеты DeepSeek; CI не ходит в API без ключа.

7.8. DoD этапа 7
Сценарий B end-to-end; ничья → эскалация; сессия восстанавливается после рестарта.

8. 3D-визуализация и 2D-панель
8.1. Стек
Vite + React 18 + R3F + drei. GLB в frontend/public/models/line.glb. Ноды: rotor, body, indicator, label.

8.2. Привязка
typescript
type Binding = { mesh: string; tag: string; mode: 'spin' | 'heat' | 'visibility' | 'label' };
// spin: Speed.PV → rpm (clamp 0..1200, интерполяция ~100 мс)
// heat: Temp.PV → цвет body (20..120 °C)
// visibility: Running → indicator.visible; Alarm.Code>0 → мигающий красный
// label: Load.Pct → HTML-overlay
bindings.ts генерируется из registry.yaml (scripts/gen-bindings.py). Ручное редактирование запрещено.

8.3. WS-клиент
Подписка на теги, delta_only, min_interval_ms: 100.

Reconnect: 1→2→5→10 c; resume с last_seq.

q="stale"/"bad" → меш «серым», не показывать последнее.

Пульт оператора — отдельная WS-ветка, operator_id из JWT.

8.4. 2D-панель (Lovable)
Lovable-UI из agent-1c-demo → 2D-панель нового backend: обзор, документы, производство, согласования, агенты, журнал. 3D — отдельный экран. Существующее не выбрасываем.

8.5. DoD этапа 3
Модель реагирует на 3 параметра ≥10 мин; stale ≤3 c; reconnect без snapshot.

9. Адаптер 1С
9.1. Контракт (v1 — только чтение)
python
class OnesAdapter(Protocol):
    def get_order(self, order_id: str) -> Order: ...
    def list_open_orders(self) -> list[Order]: ...
update_production_plan удалён из v1. Запись — после ADR.

9.2. Stub (4a)
In-memory: 5 заказов {order_id, product, qty, priority, due_date, spec_id}. POST /debug/orders (только ENV=dev). ONES_MODE=stub.

9.3. HTTP-сервисы 1С (4b)
Opencode пишет:

BSL-модуль HTTP-сервиса:

GET
/mfg/orders/{id}
 → 
get_order

GET /mfg/orders/open → list_open_orders

POST /mfg/plan → заглушка (501/202 без записи) до ADR

XML-выгрузку расширения .cfe.

Инструкцию: Общие → HTTP-сервисы, корневой URL, шаблоны, методы; публикация через веб-сервер; расширение без снятия с поддержки.

Python-клиент http_ones.py.

Нужно от вас:

Версия платформы 1С (8.3.XX).

Конфигурация (УТ, ERP, КА, своя?).

Тестовый доступ к 1С (хотя бы одна база).

Кто публикует расширение.

Без доступа opencode напишет «по спецификации», но не проверит. Для v1 (stub) допустимо.

MCP-серверы 1С (опционально): feenlace/mcp-1c (19 инструментов), Artuganov/MCP35 (51 инструмент для ERP).

9.4. Ограничение
1С не в real-time. События для 3D — «SCADA → backend → WS → браузер», минуя адаптер.

9.5. DoD 4a
Повтор command_id без побочных эффектов; отказ по RANGE/INTERLOCK; события в /audit.

9.6. DoD 4b
Чтение корректно; ошибки обрабатываются; проекты операций без записи.

10. Песочница Satisfactory (этап 8)
Polling. Internet Card делает исходящие HTTP; push невозможен. Интервал 2 c (SIMULATOR_POLL_INTERVAL_S). Задержка видна пользователю.

Fallback: TARGET=opcua.

Игровая среда — не достоверный двойник. Результаты не переносятся напрямую.

Включать после этапа 7.

SatisfactoryMCP — read-only для аналитика (через FRM).

10.1. DoD этапа 8
TARGET=satisfactory: команда меняет состояние; те же записи в аудите.

11. Тестирование
Уровень	Что	Инструмент
Unit	Валидатор (все стадии, все ячейки), реестр, идемпотентность, state machine	pytest
Integration	Эмулятор → backend → WS, reconnect, stale	pytest + websockets
Contract	API, схемы, интерфейсы	pytest + schemathesis
Agent	Против stub; strict-схема, лимит раундов, аудит	pytest + vcr (кассеты)
E2E (C)	propose → approve → REVALIDATING → EXECUTED → аудит	playwright + pytest
E2E (A)	debug/orders → supervisor → план	compose + скрипт
E2E (B)	overload L2 → debate → команда	compose
Safety	Обход approval, повтор, TTL, LLM→ПЛК, stale	pytest
Правило: кассеты DeepSeek; CI без ключа — пропуск. Strict-схемы — deepseek-compat-kit lint-schema --strict.

12. Этапы и DoD
Этап	Содержание	DoD	Оценка
0	Обследование репозитория	docs/assessment/*.md	1–2 нед.
0.5	Спайк DeepSeek	deepseek-spike.md	0.5–1 день
1	Эмулятор + FUXA (если Docker)	21 тег; interlock отклоняет	1 нед.
2	Backend: config, auth, registry, OPC UA, кэш, WS, SQLite/Alembic	Дельты; reconnect; q="bad" ≤3 c	2 нед.
3	3D + 2D-панель	3 параметра ≥10 мин; stale ≤3 c	1–2 нед.
4a	Stub-1C + POST /commands + валидатор 1–3 + аудит	Повтор без эффектов; RANGE/INTERLOCK	1 нед.
4b	HTTP-сервисы 1С (BSL + расширение + клиент)	Чтение; проекты без записи	2–3 нед.
5	Агент sequential + strict + 8 инструментов	Summary по схеме; budget-стоп	1–2 нед.
6	Валидатор 4–5 + матрица (A2) + пульт + revalidate	Каждая ячейка — тест; A1 → approve → EXECUTED; A2 → уведомление; TTL	2 нед.
7	supervisor + debate + чекпоинты	B end-to-end; ничья → эскалация; resume после рестарта	2 нед.
8	Песочница + MQTT (опц.)	TARGET=satisfactory: команда меняет состояние	2–3 нед.
Правило: каждый этап — коммит + DoD. Переход — после approve.

Параллельная разработка: agent-1c-demo работает; factoria/ рядом. Big-bang запрещён.

12.1. v2 roadmap (вне v1)
Этап 9 — самоулучшение (минимальный контракт ImprovementCandidate).

Этап 10 — sim-to-real validation.

Запись в 1С (update_production_plan) — после ADR.

A3-автономия — только в симуляции.

TLS/сертификаты OPC UA, SSO, MQTT-шина.

13. Ограничения (регламент)
LLM не получает транспорт к OPC UA/Modbus — только инструменты backend.

Валидация не на LLM. «Агент-валидатор» запрещён.

emergency_stop недоступен; Safety-interlocks — на эмуляторе/ПЛК.

Данные агента устаревают: стадия 3 читает текущий кэш.

Real-time не требуется; защиты — на ПЛК.

Модели не хардкодить: GET /models на старте.

Лимиты расходов — часть системы (budget_exhausted).

Все решения — в аудите с correlation_id.

DeepSeek: /beta; strict: true; tool_choice: required + thinking → 400; minLength/minItems не поддерживаются.

Thinking: для tool-calling отключать или reasoning_effort: low.

Транзакционная БД обязательна для идемпотентности, аудита, состояния.

FUXA — read-only.

1С v1 — только чтение.

Параллельная разработка: не ломать agent-1c-demo; Lovable — 2D-панель.

ALLOW_EXTERNAL_API=false по умолчанию. Включение — через docs/decisions.md.

A2 — только в границах 6.4. Всё остальное — A1.

Этапы 9–10 — v2. В v1 только заглушки.

14. Первое задание opencode (только обследование)
Не начинай массовую реализацию.

Изучи agent-1c-demo и все документы/конфигурации.

Изучи docs/assessment/ (если есть) и сопоставь с архитектурой ТЗ.

Определи переиспользуемое: файловый мост 1С, scada_client, platform/sim, Lovable-UI, ADR.

Выяви дублирование и противоречия между agent-1c-demo и factoria/.

Выяви отсутствующие критические компоненты.

Определи минимальный стек (с учётом «Docker нет»).

Проверь совместимость (FastAPI, asyncua, SQLAlchemy, Alembic, LangGraph, React/R3F).

Карта зависимостей.

Архитектурная схема.

Реестр требований (REQ-NNN).

Реестр рисков.

Открытые решения.

Поэтапный план с уточнёнными оценками.

Предложи 3–5 пилотных сценариев с оценкой сложности (не утверждай).

Результаты — в docs/assessment/:

text
repository-audit.md
architecture-assessment.md
technology-stack.md
requirements-traceability.md
risks.md
open-decisions.md
implementation-roadmap.md
pilot-scenario-proposals.md
deepseek-spike.md
В конце — отчёт по шаблону §15. Не переходи к следующему этапу самостоятельно.

15. Формат отчёта opencode
text
ЭТАП: [номер и название]

1. ЦЕЛЬ
2. ИЗУЧЕНО (компоненты, документы)
3. РЕАЛИЗОВАНО (файлы, функции)
4. АРХИТЕКТУРНЫЕ РЕШЕНИЯ (что и почему)
5. ТЕСТИРОВАНИЕ (команды, результаты)
6. РЕЗУЛЬТАТЫ (прошло/не прошло)
7. ПРОБЛЕМЫ (что не удалось)
8. РИСКИ (новые)
9. ОСТАТОЧНЫЕ ВОПРОСЫ (что требует человека)
10. СООТВЕТСТВИЕ ТЗ (REQ-NNN → статус → тест)
11. СЛЕДУЮЩИЙ ЭТАП (предложение)
Запрещено: скрывать неудачные тесты, выдавать частичное за завершённое, заявлять о работоспособности без проверки.

16. Открытые вопросы (уточнить до этапа 1)
Какая конфигурация 1С?

Какой бизнес-процесс первый?

Есть ли OPC UA на реальном оборудовании?

Есть ли Historian?

Инфраструктура (GPU, сеть)?

Владелец данных и кто согласует доступ?

Кто утверждает изменения в 1С?

Кто отвечает за промышленную безопасность?

Какие операции требуют подтверждения?

Требования к хранению (срок, регион)?

Docker есть? (план B)

Кто публикует расширение 1С?

Доступ к тестовой базе 1С для BSL?

Нерасшифрованное сокращение — не додумывать, запросить у владельца.

17. Критерии общей приёмки (v1)
Архитектура: разделение, документированные интерфейсы, обоснованные зависимости.

Данные: происхождение, качество, разделение факта и синтетики.

Интеграция: 1С (stub + HTTP), промышленный слой на эмуляторе, ошибки обрабатываются, LLM без прямого доступа к ПЛК.

Двойник и симуляция: воспроизводимы, сценарии проверены, метрики, сравнение.

Агенты: роли, состояние, ошибки, история.

Безопасность: auth/RBAC, A1 — подтверждение, A2 — в границах, повтор исключён, TTL, опасное заблокировано.

Бизнес-эффект: базовые показатели, сравнение, подтверждение, ограничения, отчёт.

Документ полный. Учтены: имя FACTORIA & AI, репозиторий factoria/ (новый, рядом), ALLOW_EXTERNAL_API=false по умолчанию, A2 с границами, Lovable-UI как 2D-панель + 3D-экран, этапы 9–10 в v2, HTTP-сервисы 1С, план B без Docker, 18 правок v2. Готов к передаче opencode после approve руководителя проекта.