# FACTORIA & AI

Мультиагентная система управления производственными процессами предприятия.
Новый репозиторий рядом с `D:\agent-1c-demo`; старый демо-контур продолжает работать
и не изменяется (ТЗ §0 п.1, п.8).

**Текущий этап: 0 — обследование.** Код этапов 1+ не начат сознательно: ТЗ §14
запрещает массовую реализацию до утверждения assessment.

## Где что лежит

| Путь | Содержание |
|---|---|
| `docs/specification.md` | ТЗ v2.1 — копия исходного документа, источник истины |
| `docs/assessment/` | результат этапа 0: 9 документов + отчёт |
| `docs/decisions.md` | ADR проекта `factoria/` |
| `docs/api.md` | контракт API, включая пробелы под 2D-панель |
| `docs/tag-registry.md` | схема `registry.yaml` (21 тег) |
| `docs/autonomy-matrix.md` | матрица A0–A3 в data-driven виде |
| `docs/data-model.md` | сущности и состояния |
| `opcua-emulator/` | эмулятор ПЛК (этап 1, не начат) |
| `backend/` | FastAPI (этап 2, не начат) |
| `agents/` | LangGraph + DeepSeek (этап 5, не начат) |
| `frontend/` | 3D + 2D-панель (этап 3, не начат) |

## План B: без Docker

На машине разработки Docker CLI 19.03.1 без работающего демона
(проверено: `docker info` не отвечает). Все компоненты запускаются локально:

```bash
python opcua-emulator/emulator.py            # :48400 (4840 занят opcualds)
python opcua-emulator/emulator.py --seconds 10
python -m pytest -q                          # 20 тестов этапа 1
python scripts/gen-tag-registry.py           # docs/tag-registry.md
python scripts/gen-bindings.py               # frontend/src/scene/bindings.ts
uvicorn factoria.main:app --reload           # :8000, этап 2 — не начат
cd frontend && npm run dev                   # :5173, этап 3 — не начат
```

Клиент адресует теги строковым NodeId: `ns=2;s=L1.Speed.SP`.
Запись — только методами `L1.SetSpeed`, `L1.SetRecipe`, `L1.StartLine`,
`L1.StopLine`, `L1.ReallocateJob`.

FUXA и InfluxDB отложены; витрина — HTML на `GET /api/v1/equipment/{id}/state`.

## Границы безопасности

- LLM не имеет транспорта к ПЛК/OPC UA — только инструменты backend.
- Валидация и исполнение — на backend, не на LLM.
- `emergency_stop` LLM недоступен.
- 1С в v1 — только чтение.
- `ALLOW_EXTERNAL_API=false` по умолчанию.
- Автономия A2 включается флагом `AUTONOMY_MAX=A2`; по умолчанию `A1`.

## Что дальше

Читать `docs/assessment/report-stage0.md` — там итог обследования, список
противоречий ТЗ и предложения по этапам.
