# AUTONOMY-MATRIX.md — матрица автономности (DRAFT, этап 0)

ТЗ §6.4 задаёт матрицу таблицей. Для реализации она должна быть data-driven
dict, а не `if`-цепочкой. Ниже — предлагаемая структура и правила.

## 1. Уровни

| Уровень | Смысл |
|---|---|
| A0 | запрещено полностью |
| A1 | требуется подтверждение человека |
| A2 | автономно в границах §6.4 + уведомление оператору |
| A3 | полная автономия (только чтение и только в симуляции) |

## 2. Матрица v1

```python
# validation/autonomy.py
AUTONOMY: dict[str, dict[str, str]] = {
    "read":               {"analyst": "A3", "logistics": "A3", "production": "A3", "orchestrator": "A3"},
    "set_setpoint_safe":  {"analyst": "A0", "logistics": "A2", "production": "A2", "orchestrator": "A2"},
    "set_setpoint_risky": {"analyst": "A0", "logistics": "A1", "production": "A1", "orchestrator": "A1"},
    "switch_recipe":      {"analyst": "A0", "logistics": "A1", "production": "A1", "orchestrator": "A1"},
    "line_start_stop":    {"analyst": "A0", "logistics": "A1", "production": "A1", "orchestrator": "A1"},
    "reallocate_job":     {"analyst": "A0", "logistics": "A1", "production": "A1", "orchestrator": "A1"},
    "emergency_stop":     {"analyst": "A0", "logistics": "A0", "production": "A0", "orchestrator": "A0"},
}
```

`set_setpoint` разбит на два ключа, потому что уровень зависит от значения,
а не только от роли. Это единственная развилка в матрице.

## 3. Условия A2 (все одновременно)

| Условие | Значение | Источник |
|---|---|---|
| Дельта уставки | ≤ 5% диапазона (≤ 60 rpm) | `speed_max` из registry |
| Новое значение | ≤ 400 rpm | `speed_threshold` |
| Interlock | Temp ≤ 80, Load ≤ 95 | кэш, свежесть ≤ 2×max_age |
| Качество данных | `q = GOOD`, не stale | кэш |
| Тип команды | только `set_setpoint` | — |
| Флаг | `AUTONOMY_MAX=A2` | окружение |

Нарушено хотя бы одно → A1 (`set_setpoint`) либо отказ (stale/bad — §6.4).
При A2 оператор получает **уведомление**, событие пишется в аудит.

## 4. Противоречие §6.2 / §6.5, которое надо снять до кода

ТЗ §6.2 даёт правило:

```yaml
- id: speed-delta-warn
  if:   { tag: "{line}.Speed.SP", op: "<", value: 400 }
  when: { param: setpoint_value, op: ">", value: 800 }
  prohibit: ["set_setpoint"]
  code: INTERLOCK_003
```

а §6.5 говорит: «|Δ| > 800 → interlock». Это **разные предикаты**:
первый — «текущая SP < 400 и новая > 800», второй — «модуль разницы > 800».
При разбросе 0…1200 они дают разные вердикты.

Предложение: один предикат на дельту, второй — на абсолютное значение:

```yaml
rules:
  - id: delta-too-large
    when: { param: abs_delta, op: ">", value: 800 }
    prohibit: ["set_setpoint"]
    code: INTERLOCK_001
  - id: target-above-threshold
    when: { param: setpoint_value, op: ">", value: 400 }
    level: A1                       # не запрет, а подтверждение
    code: AUTONOMY_002
  - id: job-already-reallocated
    if:   { tag: "{line}.Load.Pct", op: ">", value: 95 }
    prohibit: ["reallocate_job"]
    code: INTERLOCK_004
```

Так «A1» и «interlock» перестают пересекаться.

## 5. Тесты (DoD §6.4)

- 7 действий × 4 роли = 28 ячеек, по одному тесту на ячейку.
- Для `set_setpoint` — дополнительно 6 граничных: Δ=59, 60, 61; new=399, 400, 401.
- A2 при `q=BAD` → отказ, не A1 и не A2.
- A2 при флаге `AUTONOMY_MAX=A1` → A1.
- Каждая A2-команда порождает уведомление и запись в аудите.
