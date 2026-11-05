# TECHNOLOGY-STACK.md — проверка стека на реальной машине

Дата: 2026-11-05. Метод: `pip install` в чистый venv, импорты, запуск спайка.
Все выводы ниже — из фактического запуска, не из документации.

## 1. Что есть на машине

| Компонент | Факт | Вывод |
|---|---|---|
| `python` (по умолчанию) | **3.14.3** (`C:\Users\diorl\AppData\Local\Programs\Python\Python314`) | рабочий |
| Python 3.11 | `py -0p` показывает `D:\1\python.exe`, **файла нет**, `py -3.11` падает `0x80070003` | **не существует** |
| Python 3.13 | Store-алиас, запуск падает `0x80070780` | **не существует** |
| Node.js | v24.14.0 | подходит для Vite/R3F |
| Docker | CLI 19.03.1 (2019), `docker info` **не ответил за 25 с** | демона нет → план B |
| `py -0p` доверять нельзя | реестр содержит мёртвые записи | версия проверяется запуском |

Следствие: «Python 3.11+» из ТЗ §3.1 на этой машине означает **ровно 3.14.3**.
Либо переустанавливаем 3.11, либо фиксируем 3.14 (ADR-109).

## 2. Глобальное окружение (Python 3.14.3)

Уже установлено и импортируется:

```
asyncua 2.1.0     fastapi 0.136.1   pydantic 2.13.4
SQLAlchemy 2.0.49 aiosqlite 0.22.1  uvicorn 0.49.0
pytest 9.0.3      httpx 0.28.1
```

Чего не было: `alembic`, `langgraph`.

## 3. Проверка установки в чистый venv

```
python -m venv venv-factoria
pip install --upgrade pip            → pip 26.2.2
pip install alembic langgraph        → OK
```

Фактический результат:

```
python 3.14.3
alembic 1.20.1
langgraph 1.2.19
StateGraph ok
SQLAlchemy 2.1.8 (подтянут langgraph)
pydantic 2.14.2
```

| Проверка | Результат |
|---|---|
| `alembic` на 3.14 | **работает** |
| `langgraph` на 3.14 | **работает** |
| `from langgraph.graph import StateGraph` | **OK** |
| `from langgraph.checkpoint.sqlite import SqliteSaver` | **ModuleNotFoundError** — нужен отдельный пакет `langgraph-checkpoint-sqlite` |
| после `pip install langgraph-checkpoint-sqlite` | **OK** |

**Вывод:** ТЗ §7.3 («Checkpointing: SqliteSaver») требует в `agents/pyproject.toml`
не только `langgraph`, но и `langgraph-checkpoint-sqlite`. В ТЗ эта зависимость
не указана — это дефект спецификации, а не среды.

## 4. Спайк OPC UA: паттерн §4.3 исполним

`scripts/spike_opcua_methods.py` — сервер 3 переменные + method-нода `SetSpeed`,
клиент пытается писать напрямую и через метод.

Фактический вывод:

```
direct_write_blocked = True
direct_write_error   = 0x801f0000              (BadUserAccessDenied по таблице OPC UA)
method_write_ok      = True                    (SP стало 500.0)
interlock_blocks     = True
interlock_error      = 0x80af0000              (BadInvalidState)
value_after_interlock = 500.0                  (значение не изменилось)
SPIKE_RESULT = PASS
```

Полный вывод сохранён в `docs/assessment/checks/stage0-spike.txt`; версии
стека — в `docs/assessment/checks/stage0-stack.txt`.

Это подтверждает ключевое архитектурное решение ТЗ:
**writable-переменные не нужны, method-ноды дают и запись, и отказ.**

Две грабли, найденные по ходу (обе воспроизводятся, обе стоят времени на этапе 1):

1. `get_child("2:Speed.SP")` падает с `BadNoMatch`: asyncua трактует часть пути
   как **строковый** NodeId (`ns=2;s=Speed.SP`), а `add_variable` создаёт
   числовые. Узлы надо искать по `BrowseName` через `get_children()`.
2. Callback метода получает `ua.Variant`, а не `float`. `float(value)` падает
   с `TypeError`, а сервер возвращает клиенту `BadUnexpectedError` без
   подробностей. Нужен `value.Value`.

## 5. Pydantic v2 и discriminated union

ТЗ §5.3 требует discriminated union по `type` для тела `POST /commands`.
`pydantic 2.13.4/2.14.2` поддерживает `Annotated[Union[...], Field(discriminator=...)]`
— используется штатно, отдельная проверка не требуется (стандартная возможность v2).

## 6. Вердикт по стеку

| Слой | Готовность | Риск |
|---|---|---|
| OPC UA-эмулятор (`asyncua`) | **проверено, работает** | низкий |
| Backend (FastAPI, pydantic, SQLAlchemy, aiosqlite) | **проверено импортом** | низкий |
| Alembic (async-шаблон) | **установлен**, шаблон не проверялся | низкий |
| LangGraph + SqliteSaver | **проверено**, нужен доп. пакет | средний (версии 1.x, API менялся) |
| DeepSeek SDK / strict mode | **не проверено** — нет ключа и сети | **высокий** |
| React/R3F (Node 24) | не проверялось (нет проекта) | низкий |
| Docker/FUXA/InfluxDB | **недоступно** | снят планом B |

Итог: **стек собирается на Python 3.14.3 без Docker.** Единственный
непроверенный и блокирующий элемент — DeepSeek (см. `deepseek-spike.md`).
