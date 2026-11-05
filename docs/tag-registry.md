# TAG-REGISTRY.md — схема реестра тегов (DRAFT, этап 0)

ТЗ ссылается на `registry.yaml` в §5.4 (`max_age_seconds`), §6.5 (`speed_threshold`),
§8.2 (генерация `bindings.ts`), DoD этапа 1 (`docs/tag-registry.md` сгенерирован),
но саму схему не задаёт. Ниже — предложение схемы. Утверждается до этапа 1.

## 1. Состав: 21 тег = 7 × 3 линии

`{L}` ∈ {L1, L2, L3}. Расхождение ТЗ §4.3 («18 тегов») с таблицей §4.2 (21) —
ошибка счёта; принимаем 21. Таблица ниже генерируется из
`backend/src/factoria/tags/registry.yaml`.

<!-- BEGIN GENERATED: не редактировать вручную, см. scripts/gen-tag-registry.py -->
| Тег | Тип | Диапазон | Ед. | max_age, c | Запись через |
|---|---|---|---|---|---|
| `L1.Running` | bool | — | — | 3 | StartLine() / StopLine() |
| `L1.Speed.SP` | float | 0…1200 | rpm | 3 | SetSpeed(value) |
| `L1.Speed.PV` | float | 0…1200 | rpm | 3 | — |
| `L1.Temp.PV` | float | 20…120 | degC | 3 | — |
| `L1.Load.Pct` | float | 0…100 | percent | 3 | — |
| `L1.Alarm.Code` | uint16 | 0…999 | — | 5 | — |
| `L1.Recipe.ID` | string | R1…R5 | — | 30 | SetRecipe(id) |
| `L2.Running` | bool | — | — | 3 | StartLine() / StopLine() |
| `L2.Speed.SP` | float | 0…1200 | rpm | 3 | SetSpeed(value) |
| `L2.Speed.PV` | float | 0…1200 | rpm | 3 | — |
| `L2.Temp.PV` | float | 20…120 | degC | 3 | — |
| `L2.Load.Pct` | float | 0…100 | percent | 3 | — |
| `L2.Alarm.Code` | uint16 | 0…999 | — | 5 | — |
| `L2.Recipe.ID` | string | R1…R5 | — | 30 | SetRecipe(id) |
| `L3.Running` | bool | — | — | 3 | StartLine() / StopLine() |
| `L3.Speed.SP` | float | 0…1200 | rpm | 3 | SetSpeed(value) |
| `L3.Speed.PV` | float | 0…1200 | rpm | 3 | — |
| `L3.Temp.PV` | float | 20…120 | degC | 3 | — |
| `L3.Load.Pct` | float | 0…100 | percent | 3 | — |
| `L3.Alarm.Code` | uint16 | 0…999 | — | 5 | — |
| `L3.Recipe.ID` | string | R1…R5 | — | 30 | SetRecipe(id) |

Всего тегов: **21** (3 линии × 7), методов: **5**.
<!-- END GENERATED -->

## 2. Поля реестра

```yaml
version: 1
namespace: urn:mfg:emulator
speed_threshold: 400        # §6.5: new > 400 → A1
speed_max: 1200             # верх диапазона
temp_alarm: 80              # физический interlock эмулятора
load_alarm: 95              # физический interlock эмулятора
load_alarm_hold_s: 60

defaults:
  max_age_seconds: 3        # §5.4: stale при отсутствии > 2× max_age_seconds
  deadband: 0.5
  publish_interval_ms: 500

tags:
  - id: L1.Speed.SP
    node: "ns=2;s=L1.Speed.SP"
    type: float
    unit: rpm
    min: 0
    max: 1200
    writable: false          # всегда false: запись только через method-ноду
    command: set_setpoint
    quality_from: L1.Speed.SP
    max_age_seconds: 3
    deadband: 0.5
```

Обязательные поля тега: `id`, `node`, `type`, `min`, `max`, `writable`,
`max_age_seconds`. `writable: true` в реестре — ошибка валидации
(ADR-105: все изменения через method-ноды).

## 3. Методы (не теги, но часть реестра)

```yaml
methods:
  - id: SetSpeed
    tag: Speed.SP
    args: { value: float }
    errors: [BadInvalidState, BadOutOfRange]
  - id: SetRecipe
    tag: Recipe.ID
    args: { recipe_id: string }
    errors: [BadOutOfRange]
  - id: StartLine
    args: {}
  - id: StopLine
    args: {}
  - id: ReallocateJob
    args: { job_id: string }
```

## 4. Генерируемые артефакты

| Артефакт | Из чего | Кто генерирует |
|---|---|---|
| `docs/tag-registry.md` (таблица выше) | `registry.yaml` | `scripts/gen-tag-registry.py` |
| `frontend/src/scene/bindings.ts` | `registry.yaml` | `scripts/gen-bindings.py` |
| `backend/src/factoria/tags/registry.py` (валидация при старте) | `registry.yaml` | рантайм |

Ручное редактирование сгенерированных файлов запрещено (ТЗ §8.2).

## 5. Проверки (DoD этапа 1)

1. `registry.yaml` валиден по схеме; 21 тег; `writable` везде `false`.
2. OPC UA-сервер поднимает ровно 21 переменную + 5 методов.
3. `docs/tag-registry.md` побайтово воспроизводим из YAML.
4. `bindings.ts` содержит ровно 21 привязку.
