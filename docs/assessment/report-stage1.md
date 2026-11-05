# REPORT — ЭТАП 1: OPC UA-эмулятор

Дата: 2026-11-05. Шаблон: ТЗ §15. Исполнитель: opencode (DeepSeek V4.1 Flash).

---

## 1. ЦЕЛЬ

Поднять эмулятор ПЛК на OPC UA: 3 линии (L1–L3), 21 тег, 5 method-нод,
физические interlocks в сервере, запись только через методы. DoD §4.6:
21 тег виден клиенту, `SetSpeed(500)` при `Temp>80` отклоняется,
`docs/tag-registry.md` генерируется.

Цель достигнута. Все три пункта DoD проверены запуском (см. §5).

## 2. ИЗУЧЕНО

| Источник | Что взято |
|---|---|
| ТЗ §4.1–§4.6 | состав тегов, методы, interlocks, DoD |
| ТЗ §6.5 | пороги 400/800 — решение OD-02 (дельта) |
| `docs/tag-registry.md` | схема реестра (написана на этапе 0) |
| `scripts/spike_opcua_methods.py` | рабочий паттерн method-нод (этап 0) |
| `asyncua 2.1.0` | реальные сигнатуры `add_variable`, `add_method`, `call_method` |

## 3. РЕАЛИЗОВАНО

| Файл (полный путь) | Строк | Что |
|---|---|---|
| `D:\factoria\backend\src\factoria\tags\registry.yaml` | 96 | 21 тег (шаблоны × 3 линии), 5 методов, пороги |
| `D:\factoria\backend\src\factoria\tags\registry.py` | 140 | загрузка, раскрытие шаблонов, валидация (ADR-104) |
| `D:\factoria\backend\src\factoria\simulator\line_physics.py` | 190 | детерминированная физика: τ=2 c, нагрев ∝(SP/1200)², interlocks, автостоп |
| `D:\factoria\opcua-emulator\emulator.py` | 218 | OPC UA-сервер: 21 переменная (writable=False), 5 методов, цикл 0.5 c |
| `D:\factoria\scripts\gen-tag-registry.py` | 72 | генерация таблицы в `docs/tag-registry.md` по маркерам |
| `D:\factoria\scripts\gen-bindings.py` | 66 | генерация `frontend/src/scene/bindings.ts` (12 привязок) |
| `D:\factoria\tests\conftest.py` | 8 | путь `backend/src` для тестов |
| `D:\factoria\tests\test_registry.py` | 74 | 7 тестов реестра |
| `D:\factoria\tests\test_physics.py` | 118 | 12 тестов физики |
| `D:\factoria\tests\test_emulator_opcua.py` | 105 | 1 интеграционный тест OPC UA (7 переменных, 5 методов, 7 блокировок записи) |
| `D:\factoria\docs\tag-registry.md` | — | обновлён генератором (21 строка) |
| `D:\factoria\frontend\src\scene\bindings.ts` | 54 | сгенерирован: 21 тег, 12 привязок |

## 4. АРХИТЕКТУРНЫЕ РЕШЕНИЯ

| Решение | Почему |
|---|---|
| Физика отдельно от транспорта (`line_physics.py`) | тестируется без OPC UA, 12 тестов идут за 0.1 с вместо секунд ожидания |
| Детерминированная физика без RNG | требование воспроизводимости; тесты не «мигают» |
| Строковые NodeId полного вида `L1.Speed.SP` | стабильная адресация `ns=2;s=L1.Speed.SP`, не зависит от порядка узлов |
| `writable=False` на всех переменных | ADR-105; клиент получает `BadUserAccessDenied`, проверить 7 из 7 |
| Порог 800 — по **дельте** (OD-02) | §6.5; `|new − current| > 800` → `BadInvalidState` |
| Порт по умолчанию 48400 | 4840 занят `opcualds` (ADR-111) |
| `docs/tag-registry.md` с маркерами | файл остаётся документом, но таблица генерируется (ADR-104) |

## 5. ТЕСТИРОВАНИЕ (команды и фактический вывод)

**5.1. Тесты:**

```
python -m pytest -q
....................                                                     [100%]
```

20 тестов, 0 падений. Полный лог — `docs/assessment/checks/stage1-pytest.txt`.

**5.2. Клиент видит значения (реальный процесс + реальный клиент):**

```
python opcua-emulator/emulator.py --seconds 6      (в фоне)
python smoke_client.py

L1.Speed.PV = 0.0
L1.Temp.PV = 20.0
L1.Recipe.ID = R1
L2.Alarm.Code = 0
L3.Running = False
client_exit=0
```

Лог — `docs/assessment/checks/stage1-smoke.txt`.

**5.3. Контракт эмулятора (из интеграционного теста):**

```
variables = 7 на линию, methods = 5
blocked = 7            (все переменные отвергают прямую запись)
initial_sp = 0.0
set_speed_code = Good  -> sp_after = 500.0
bad_recipe_code = BadOutOfRange
good_recipe_code = Good
hot_speed_code = BadInvalidState  -> alarm = 101, sp остался 500.0
```

**5.4. Генераторы:**

```
python scripts/gen-tag-registry.py  -> обновлено: D:\factoria\docs\tag-registry.md
python scripts/gen-bindings.py      -> обновлено: ...bindings.ts (привязок: 12, тегов: 21)
```

## 6. РЕЗУЛЬТАТЫ

| DoD §4.6 | Итог |
|---|---|
| 21 тег виден клиенту | **ПРОШЛО**: 3 линии × 7 |
| `SetSpeed(500)` при `Temp>80` отклоняется | **ПРОШЛО**: `BadInvalidState`, `Alarm.Code=101` |
| `docs/tag-registry.md` генерируется | **ПРОШЛО**: воспроизводится из YAML |
| FUXA видит 21 тег | **НЕ ПРОВЕРЕНО**: FUXA отложена (ADR-110, нет Docker) |
| Тесты зелёные | **ПРОШЛО**: 20 passed |

## 7. ПРОБЛЕМЫ

1. **Порт 4840 занят** процессом `opcualds` (OPC UA Local Discovery Server, PID 5452).
   Эмулятор на 4840 падает с `WinError 10013`. Локальный порт изменён на 48400
   (ADR-111). В Docker/TZ остаётся 4840.
2. **`get_child("2:Name")` не работает для NodeId-строк** — путь трактуется как
   BrowseName. Адресация только `get_node("ns=2;s=L1.Speed.SP")` либо
   `get_child` по QualifiedName. Заложено в код и в тест.
3. **Возврат `StatusCode` из метода** приводит к исключению у клиента
   (`UaStatusCodeError`), а не к значению. Это ожидаемое поведение OPC UA:
   клиент обязан ловить. Задокументировано в тесте.
4. **Испорченная кодировка при правке из PowerShell.** `Get-Content -Raw` без
   BOM читает UTF-8 как ANSI, `Set-Content -Encoding UTF8` записывает мусор.
   Два файла были перезаписаны заново; проверка на `\uFFFD` по репозиторию
   теперь проходит чисто. Правило: править файлы инструментом, не через Replace.
5. **FUXA не проверена** — DoD пункт про витрину не закрыт осознанно.

## 8. РИСКИ (новые)

| ID | Риск |
|---|---|
| R-023 | Порт 4840 конфликтует с системным LDS на любой машине с OPC UA-стеком; нужен параметр, а не константа (сделано) |
| R-024 | `call_method` возвращает исключение на отказе — backend обязан обрабатывать `UaStatusCodeError`, иначе 500 вместо 422 |
| R-025 | Физика — правдоподобная модель, а не идентифицированная по реальным данным; для пилота нужна валидация |

## 9. ОСТАТОЧНЫЕ ВОПРОСЫ

| ID | Вопрос | Статус |
|---|---|---|
| OD-01 | Python 3.14.3 | **закрыт** |
| OD-02 | Порог 800 = дельта (§6.5) | **закрыт** |
| OD-07 | Ключ DeepSeek | **частично**: сеть доступна (HTTP 401), ключа нет |
| — | Нужна ли FUXA как витрина | открыт (Docker недоступен) |

## 10. СООТВЕТСТВИЕ ТЗ

| REQ | Требование | Статус | Тест |
|---|---|---|---|
| REQ-010 | 21 тег | **выполнено** | `test_registry_has_21_tags_and_5_methods` |
| REQ-011 | Только method-ноды | **выполнено** | `test_emulator_contract` (blocked=7) |
| REQ-012 | Interlock Temp>80 | **выполнено** | `test_interlock_rejects_high_speed_when_hot` |
| REQ-013 | SetRecipe вне R1..R5 | **выполнено** | `test_recipe_validation`, `bad_recipe_code` |
| REQ-014 | Автостоп Load>95/60 c | **выполнено** | `test_overload_autostop_after_60s` |
| REQ-016 | `tag-registry.md` генерируется | **выполнено** | `scripts/gen-tag-registry.py` |
| REQ-017 | 5 методов | **выполнено** | `test_emulator_contract` (methods=5) |
| REQ-032 | Порог 800 | **выполнено** (дельта) | `test_delta_interlock_uses_absolute_delta` |
| REQ-015 | FUXA read-only | **N/A** | FUXA отложена |

## 11. СЛЕДУЮЩИЙ ЭТАП (предложение)

**Этап 2 — backend:** `config`, `auth/jwt`, `tags/registry` (готов), клиент OPC UA
с подпиской, кэш с `q`/`stale`, WS с `seq`/`resume`, SQLite + Alembic, аудит.

DoD §5.7: дельты в WS, reconnect по `resume`, `q=bad` ≤3 c, записи в БД и аудит.
Первый шаг — Alembic-миграции `commands`, `audit_events`, `users`, `tag_history`
(схема готова в `docs/data-model.md`).

---

**Запрет §15 соблюдён:** пункт DoD про FUXA не закрыт и это указано явно,
остальные проверки подтверждены фактическим выводом, а не описанием.
