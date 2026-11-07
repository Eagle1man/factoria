# REPORT — HTTPS, OPC UA TLS и визуальная проверка в CI

Дата: 2026-11-07. Исполнитель: opencode (DeepSeek V4.1 Flash).

## 1. HTTPS для API — работает

| Файл | Что |
|---|---|
| `scripts/gen_certs.py` | HTTPS-пара (PEM) + OPC UA пары (DER) в `certs/` |
| `scripts/run_backend_https.ps1` | uvicorn на `:8443` с `--ssl-certfile/--ssl-keyfile` |
| `.gitignore` | `certs/` не коммитится |

Проверка:

```
curl -k https://127.0.0.1:8443/api/v1/health → 200
curl    http://127.0.0.1:8443/api/v1/health → 000
```

## 2. OPC UA TLS — работает, причина зависания найдена

Первые попытки зависали на `SecureOpen`. Причина оказалась не в версии Python
и не в сертификатах, а в двух ошибках вызова:

1. **`Server.load_certificate` грузит только сертификат.** Приватный ключ
   загружается отдельно: `await server.load_private_key(path)`. Без ключа
   сервер не публикует ни одного защищённого endpoint — список endpoints
   приходил пустым, клиент ждал ответ и падал по таймауту.
2. **`Server.set_application_uri` — асинхронный.** Без `await` URI приложения
   оставался дефолтным, и сертификат «не совпадал» с приложением.

Дополнительно: ключи для asyncua должны быть в **DER** (PKCS8), а
`setup_self_signed_certificate` пишет PEM и потом читает его как DER —
поэтому сертификаты генерируются своим кодом (`factoria/security/certs.py`).

Проверка (факт):

```
endpoints: [('Basic256Sha256', '3')]
read over TLS: 42.0
```

Интеграционный тест `tests/test_opcua_tls.py`:

- генерирует пары в `tmp_path`;
- поднимает эмулятор с `Basic256Sha256_SignAndEncrypt`;
- подключает `OpcuaClient` с клиентским сертификатом и закреплённым
  серверным;
- требует `source == "connected"` и все 21 тег `GOOD`.

Сквозная проверка: backend с TLS-переменными → `/health`:
`opcua: connected`, `tags: 21, not_good: 0`.

Включение — переменными окружения (по умолчанию `None`, чтобы демо не
требовало сертификатов):

```
OPCUA_SECURITY=Basic256Sha256_SignAndEncrypt
OPCUA_CERT=...opcua-server.cert.der
OPCUA_KEY=...opcua-server.key.der
# backend:
OPCUA_CLIENT_CERT, OPCUA_CLIENT_KEY, OPCUA_SERVER_CERT
```

## 3. Визуальная проверка в CI

Job `visual` в `.github/workflows/ci.yml`:

1. поднимает эмулятор, backend на 8010 и Vite на 5173;
2. ждёт `/api/v1/health` и страницу;
3. запускает `scripts/shots.py` (все экраны, 4 ширины);
4. падает при горизонтальном переполнении;
5. выгружает скриншоты артефактом, при падении — логи сервисов.

`shots.py`: встроенный Chromium → фолбэк на системный Chrome, 3D-сцена не
валит job при отсутствии canvas, код возврата 1 при overflow.

## 4. ЧЕСТНЫЕ ОГРАНИЧЕНИЯ

1. **Сертификаты самоподписанные.** Для пилота нужен внутренний PKI или CA.
2. **TLS не включает аутентификацию пользователя**: анонимный доступ к
   эмулятору остаётся допустимым только в dev.
3. **Пиксельного сравнения с эталоном нет** — job проверяет переполнение и
   складывает скриншоты; baseline-дифф не делался (шрифты Linux/Windows дают
   ложные различия).
4. Job `visual` ещё не запускался на GitHub: репозиторий локальный.
5. Тикеты WS и лимитер входа — в памяти процесса; для нескольких воркеров
   нужен общий store.
