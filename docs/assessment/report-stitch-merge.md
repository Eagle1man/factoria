# REPORT — интеграция спеки Stitch/Three.js в FACTORIA

Дата: 2026-11-08. Исполнитель: opencode (Iceman Contributor Free).
Основание: `docs/spec/stitch-threejs/spec.md` (экспорт `D:\загрузки Chrome\three.js.html`, FACTORIA v4.8).

## Цель
Перенести ценное из спеки в `D:\factoria` без нарушения правил проекта:
1C read-only, действия A1 (согласование, не прямой транспорт к PLC/1C), без CDN в основном контуре, без внешних API по умолчанию.

## Выполнено (факт) — план + продолжение (без остановки)

### Блок 0 — подготовка
- Спека распакована в `docs/spec/stitch-threejs/`:
  - `spec.md`, `prototype.html` (изолированный прототип, CDN), `server_app_mock.py`, `templates_data.json`, `DECISIONS.md`, `README.md`.
- Зафиксированы расхождения: станки спеки (DMU 50/TRUMPF/FANUC/AGV, `ns=2;s=PLANT.*`, метрики rpm/feed/vibration/queue/takt) vs реестр проекта (L1-L3, 21 тег, `urn:mfg:emulator`).
- Решение: шаблоны цеха — слой представления с явной привязкой к линиям L1-L3; реестр тегов не изменён.

### Блок 1 — данные и шаблоны
- `backend/src/factoria/templates/catalog.py`: 4 шаблона — `cnc_metal`, `drone_assembly`, `cubesat_satellite`, `battery_gigafactory` (адаптированы из `templates_data.json`, узкое место/такт/заказ/станции, `sim_scenario`, `bottleneck_line_id`).
- API (read, auth): `GET /api/v1/templates`, `GET /api/v1/templates/{id}` (`backend/src/factoria/api/templates.py`, зарегистрирован в `main.py`).
- Frontend: типы `ShopTemplate/ShopStation`, `api.templates()/template()`, маршрут `/flow`, пункт навигации «Поток цеха».
- Тесты: `tests/test_templates.py` (4).

### Блок 2 — 2.5D-схема потока
- `frontend/src/components/FlowCanvas.tsx`: Canvas 2D (конвейер, анимация деталей, станции, подсветка `BOTTLENECK`/аварии), привязан к выбранному шаблону и живым данным `L1-L3` (`Load.Pct`, `Alarm.Code`, качество). `overflow:hidden`, ширина по контейнеру.
- Интегрировано в `pages/Flow.tsx`. Узкое место отображается честно: где есть сигнал — нагрузка OPC UA; иначе — расчётный/описательный показатель витрины.

### Блок 3 — Co-Pilot / узкие места (честный режим)
- `frontend/src/components/CoPilotPanel.tsx`: детерминированная 3-шаговая цепочка рассуждений (состояние → рекомендация → границы) по живым тегам (`load/temp/alarm/speed SP`) и шаблону.
- **Режим явно маркирован**: «детерминированный, LLM не подключён/недоступен» с динамической подсказкой из `/health.llm`. Внешний LLM не вызывался (нет env/ключа/VM в контексте выполнения).
- Действие с записью: кнопка создаёт **реальный запрос `POST /api/v1/commands`** типа `set_setpoint` (A1, `requires_evidence`) с evidence — попадает в существующий контур валидации/согласований. Исполнение — только после подтверждения человеком в «Согласованиях».
- На `/flow` добавлен запуск связанного сценария симулятора (`api.createSimRun`, существующий API).
- **Не реализованы как прямые действия** (намеренно): «перенаправить AGV», «наряд 1С:ТОиР», любой PUSH в 1C/OData/PLC — показаны как вне автоматического транспорта/экспорт, без fake-execution. Соответствует read-only 1C и A1.

### Блок 4 — 3D-инспектор
- Улучшен существующий процедурный станок (не заменён примитивом из спеки): `pages/Scene.tsx` — переключатель «Инспекция» (`OrbitControls.autoRotate`); `scene/LineModel.tsx` — метка показывает `Speed.PV (SP)`, температуру, нагрузку, код аварии.
- `Lathe.tsx` сохранён (вращение патрона по `Speed.PV`, нагрев/маячок/качество) — изменений геометрии не требовалось.

### Блок 5 — экспорт (без PUSH)
- `backend/src/factoria/exports/enterprise.py`: `1C:EnterpriseData v1.14` из реестра линий + выбранного шаблона; статус «Выгружено_ТолькоЧтение», примечание о запрете PUSH/OData.
- `backend/src/factoria/exports/nodeset2.py`: OPC UA `NodeSet2` из **реального** реестра — namespace `urn:mfg:emulator`, **21 UAVariable** (3×7 тегов), **15 UAMethod** (5×3 линий).
- API (read, auth): `GET /api/v1/exports/1c-enterprise.xml?template_id=...`, `GET /api/v1/exports/opcua-nodeset2.xml`.
- UI «Поток цеха»: скачивание XML с bearer-токеном; кнопки PUSH в 1C отсутствуют.
- Тесты: `tests/test_exports.py` (3) — структура XML, namespace/количества узлов, auth.

### Блок 6 / продолжение — LLM-слой и проверки
- `LLM_PROVIDER=none|deepseek|ollama` (`config.py`), `backend/src/factoria/llm/provider.py`, `/api/v1/health` содержит `llm` **без секретов** (проверено тестом). DeepSeek — только при `ALLOW_EXTERNAL_API=true` и ключе; Ollama — `OLLAMA_URL`/`OLLAMA_MODEL` (по умолчанию `qwen3.5:35b`; thinking для tool-calling отключать на стороне вызова). ADR-121 в `docs/decisions.md`. `.env.example` приведён к чистому UTF-8 с LLM/OPCUA.
- Frontend: тип `LlmStatus` в `api.ts`, CoPilot показывает статус провайдера.
- Тесты: `tests/test_llm.py` (5, моки httpx).

| Проверка | Команда | Результат (факт) |
|---|---|---|
| Stitch + LLM (точечно) | `python -m pytest tests/test_templates.py tests/test_exports.py tests/test_llm.py -q` | **12 passed** |
| Полный набор | `python -m pytest tests -q` (workdir `D:\factoria`, `PYTHONPATH=D:\factoria\backend\src`) | **185 тестов**, прогресс 100%, без FAILED/ERROR в выводе (было 173) |
| Ruff | `python -m ruff check backend tests scripts` | **All checks passed** |
| Frontend types | `cd frontend && npx tsc --noEmit` | успешно |
| Frontend build | `cd frontend && npm run build` | **успешно** (`✓ built`); предупреждение о крупном чанке `Scene` (>500 kB) — существующее |

## Изменённые/добавленные файлы (основные)
- Backend: `templates/{__init__,catalog}.py`, `exports/{__init__,enterprise,nodeset2}.py`, `llm/{__init__,provider}.py`, `api/{templates,exports,system}.py`, `config.py`, `main.py`, `backend/pyproject.toml` (+httpx).
- Frontend: `pages/Flow.tsx`, `components/{FlowCanvas,CoPilotPanel}.tsx`, `lib/api.ts` (типы/LLM/команды), `App.tsx`, `components/Layout.tsx`, `pages/Scene.tsx`, `scene/LineModel.tsx`.
- Тесты: `tests/test_templates.py`, `tests/test_exports.py`, `tests/test_llm.py`.
- Документация/конфиг: `docs/spec/stitch-threejs/*`, `docs/PROJECT-STATE.md`, `docs/decisions.md` (ADR-121), `.env.example`, этот отчёт.

## Что намеренно НЕ сделано / ограничения
1. **PUSH в 1C, запись в PLC/оборудование из UI/агента** — запрещено правилами проекта; экспорт только read-only.
2. **Фактическое подключение LLM (вызовы/агент/tool-calling)** — не выполнено: нет `DEEPSEEK_API_KEY`/адреса Ollama VM+тега/auth в среде прогона. Слой конфигурации+health готов; агентный контур — при наличии env.
3. **Реальная 1С (этап 4b)** — заблокирована лицензией/базой (ADR-118, как и ранее).
4. **OPC UA TLS re-attempt** (Python 3.12/новый asyncua) — не выполнялся в этом прогоне.
5. **Скриншоты `scripts/shots.py`** — не перегенерированы (требуют поднятого контура); фронтенд собран, визуальная проверка переполнения в CI/скрипте не прогонялась.
6. **Покрытие** — не пересчитывалось после добавления 7 тестов (ранее 91%).
7. **Метрики очереди/такта** для станков без прямых тегов — расчётные/демонстрационные, помечены в UI.
8. **Коммит/push/теги** — не выполнялись; публикация — действие владельца.

## Воспроизводимость
```powershell
# backend
$env:PYTHONPATH="D:\factoria\backend\src"
python -m ruff check backend tests scripts
python -m pytest tests -q

# frontend
cd D:\factoria\frontend
npm run build
```

Прототип спеки (изолированно, требует CDN): `cd D:\factoria\docs\spec\stitch-threejs && python -m http.server 3099` → `/prototype.html`.