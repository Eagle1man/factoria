# REPORT — ЭТАП 6: A2 и события команд в WS

Дата: 2026-11-06. Исполнитель: opencode (DeepSeek V4.1 Flash).

## 1. ЦЕЛЬ

Довести пульт до §6.7: A2 исполняется без человека, но с аудитом и
уведомлением; статусы команд приходят по WebSocket, а не только опросом.

## 2. ЧТО СДЕЛАНО

| Файл | Что |
|---|---|
| `backend\src\factoria\realtime\events.py` | шина событий: подписки, публикация без блокировок |
| `backend\src\factoria\realtime\ws.py` | переписан: три задачи (дельты, события, отправка) — отправка одна, без гонок |
| `backend\src\factoria\api\commands.py` | A2 исполняется при submit; `command_status` публикуется на submit/approve/reject |
| `frontend\src\lib\stream.ts` | хук отдаёт `commandEvent` из WS |
| `frontend\src\pages\Approvals.tsx` | очередь обновляется по событию; блок «Автономные действия (A2)» |

## 3. ПРОВЕРКА (факт)

Тесты: **114 passed**, включая:
- `test_a2_executes_without_approval` — A2 в коридоре → `EXECUTED` без approve;
- `test_a2_corridor_keeps_approval_for_large_step` — 500 rpm → `AWAITING_APPROVAL`, A1;
- `test_bus_delivers_to_subscriber`, `test_bus_drops_when_full`.

Смоук (`checks/stage6-smoke.txt`, `AUTONOMY_MAX=A2`):

```
ws snapshot seq: 21
submit L2 -> 50:  202 EXECUTED, autonomy A2, expires_in 0
ws event:         command_status EXECUTED A2
submit L2 -> 500: 202 AWAITING_APPROVAL, autonomy A1, expires_in 300
```

То есть безопасная уставка ушла на линию сама, а шаг вне коридора остановлен
на человеке — и оба события видны в WS.

## 4. ПОРТ 8000: ФАКТ ОКРУЖЕНИЯ

В этой сессии uvicorn на порту 8000 перестал подниматься: процесс жив, логов
нет, соединение отклоняется. При этом `asyncio.start_server` и `http.server`
на 8000 работают, а uvicorn на 8010 поднимается штатно. Причина не установлена
(похоже на зависший сокет/фильтр в сессии). Контур переведён на **8010**:
`vite.config.ts` (прокси `/api`, `/ws`), все скрипты, README. Это ограничение
среды, а не приложения.

## 5. ЧТО ОСТАЛОСЬ

- `approve` при A1 исполняет команду синхронно в запросе: при медленном OPC UA
  ответ задержится. Очередь исполнения — этап 7.
- Уведомление при A2 — только событие в WS и запись в аудит; почта/мессенджер
  не делались (OD-13).
- История решений в карточке: показывается только текущий статус.

## 6. СЛЕДУЮЩИЙ ШАГ

Этап 5 (агенты) упирается в ключ DeepSeek. Без него можно:
1) собрать экран «Агенты» на моках с явной пометкой «демо»;
2) сделать очередь исполнения команд и `command_status` в списке;
3) начать этап 2 модели данных (двойник) — он не требует LLM.
