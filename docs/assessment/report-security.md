# REPORT — БЕЗОПАСНОСТЬ ДО ПИЛОТА (вариант B)

Дата: 2026-11-07. Исполнитель: opencode (DeepSeek V4.1 Flash).

## 1. ЦЕЛЬ

Закрыть пункты, которые отделяют демо от пилота: JWT в URL, отсутствие
refresh/отзыва, перебор пароля, экспорт аудита, рост истории двойника.

## 2. ЧТО СДЕЛАНО

| Файл | Что |
|---|---|
| `auth/tickets.py` | одноразовые WS-тикеты с TTL 30 c |
| `auth/limiter.py` | лимит попыток входа: 5 неудач → блокировка 5 мин |
| `auth/security.py` | access (15 мин) + refresh (7 дней), тип в токене |
| `api/auth.py` | login, refresh с ротацией, logout, ws-ticket |
| `realtime/ws.py` | подключение только по тикету, JWT в URL убран |
| `api/system.py` | `GET /audit/export` → NDJSON |
| `model/history.py` | ретенция `twin_versions` (`TWIN_HISTORY_KEEP`, 500) |
| `storage/models.py` | таблица `refresh_tokens`, миграция `88a600a45ec6` |
| `frontend/src/lib/api.ts` | хранение refresh, автопродление при 401 |
| `frontend/src/lib/stream.ts` | тикет перед каждым подключением WS |
| `tests/test_auth_flow.py` | 8 тестов на новый контур |

## 3. ПРОВЕРКА (факт)

```
python -m pytest -q
172 passed
```

Смоук (`checks/security-smoke.txt`):

```
login: access+refresh ok
ws ticket issued
ws with ticket: snapshot
ticket reuse rejected: InvalidStatus
refresh: 200
old refresh reuse: 401
audit export: 200 application/x-ndjson lines: 5
```

## 4. ЧТО ЭТО ЗАКРЫВАЕТ

| Риск | Было | Стало |
|---|---|---|
| R-026 | JWT в query-строке WS | одноразовый тикет, 30 c, повтор отклоняется |
| R-027 | нет отзыва токена | refresh-ротация + отзыв при logout |
| — | перебор пароля | блокировка после 5 неудач |
| EXT-5 | аудит только в UI | NDJSON-экспорт для SIEM |
| — | история двойника росла | хранится 500 последних срезов |

## 5. ЧЕСТНЫЕ ОГРАНИЧЕНИЯ

1. **Тикеты и лимитер — в памяти процесса.** При нескольких воркерах
   каждый будет иметь свой список; для пилота нужен Redis или БД.
2. **TLS не включён**: OPC UA без шифрования, HTTP без HTTPS — только localhost.
3. **Access-токен не отзывается по списку**: отзыв действует на refresh,
   access живёт до 15 минут. Для пилота это приемлемо, для продакшена — нет.
4. Ретенция аудита по-прежнему бессрочная (OD-12).

## 6. СЛЕДУЮЩИЙ ШАГ

Вариант C: CI (pytest + сборка + тест дизайн-системы), ruff, отчёт покрытия.
Затем — TLS и HTTPS перед пилотом.
