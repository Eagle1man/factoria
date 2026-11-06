# ONES-HTTP-CONTRACT.md — контракт HTTP-сервисов 1С (этап 4b)

Версия: 1. Дата: 2026-11-07. Только чтение. Запись в 1С запрещена (ADR-107).

## 1. База и публикация

| Параметр | Значение на машине разработки |
|---|---|
| Платформа | 1С:Предприятие **8.3.27.1508** |
| База | файловая, `File="C:\1c_bases\DemoAgent"` |
| IIS | служба `W3SVC` запущена, публикаций 1С нет |
| Инструмент публикации | `webinstt.exe` в `C:\Program Files (x86)\1cv8t\8.3.27.1508\bin` |
| Конфигурация | **неизвестна** — уточняется владельцем (OD-09) |

Публикация (делает человек, не агент):

```
"C:\Program Files (x86)\1cv8t\8.3.27.1508\bin\webinstt.exe" ^
  -deploy ^
  -wsdir mfg ^
  -dir C:\inetpub\wwwroot\mfg ^
  -connstr "File=C:\1c_bases\DemoAgent;" ^
  -confpath C:\inetpub\wwwroot\mfg\default.vrd
```

Проверка: `GET http://localhost/mfg/hs/mfg/orders/open` должен вернуть JSON,
а не HTML-страницу ошибки.

## 2. Авторизация

Basic-аутентификация пользователя 1С с правами только на чтение.
Логин и пароль передаются через `ONES_HTTP_USER` / `ONES_HTTP_PASSWORD`,
в репозиторий не попадают.

## 3. Эндпоинты

### GET `/hs/mfg/orders/open`

```json
{
  "orders": [
    {
      "order_id": "ORD-1001",
      "product": "Корпус редуктора",
      "qty": 120,
      "priority": "high",
      "due_date": "2026-11-08",
      "spec_id": "SPEC-01"
    }
  ]
}
```

Обязательные поля: `order_id`, `product`, `qty`, `priority` (`low|normal|high`),
`due_date` (`YYYY-MM-DD`), `spec_id`. Дополнительные поля игнорируются.

### GET `/hs/mfg/orders/{order_id}`

Тот же объект заказа. `404` — заказа нет. `5xx` — ошибка источника.

### POST `/hs/mfg/plan`

Заглушка: `501 Not Implemented` до отдельного ADR. Запись плана в 1С
исключена из v1.

## 4. Ошибки

| Код | Что означает | Что делает адаптер |
|---|---|---|
| 401/403 | неверные учётные данные | `OnesUnavailable`, сообщение в лог, без подмены данных |
| 404 | заказа нет | `None` только для `get_order` |
| 5xx | ошибка 1С | `OnesUnavailable` |
| не JSON | неверная публикация | `OnesUnavailable` |

Пустой список заказов (`orders: []`) — валидный ответ, он не превращается
в ошибку.

## 5. Что должен сделать человек

1. Открыть базу в Конфигураторе (`1cv8t.exe` → база `DemoAgent`).
2. Создать расширение `mfg` и HTTP-сервис по шаблону из `1c-extension/`.
3. Опубликовать на IIS командой выше.
4. Создать пользователя с правами только чтения.
5. Выдать `ONES_HTTP_URL`, `ONES_HTTP_USER`, `ONES_HTTP_PASSWORD`.

До пункта 5 backend работает с `ONES_MODE=stub` и честно помечает данные
как демонстрационные.

## 6. OData — путь без правки конфигурации (v1)

Публикация базы включает стандартный интерфейс OData, и данные читаются
без расширения и без BSL.

**URL:** `http://<host>/mfg/odata/standard.odata`
**Сущность демо-базы:** `Document_РеализацияТоваровУслуг`
**Запрос:**

```
GET /mfg/odata/standard.odata/Document_РеализацияТоваровУслуг
    ?$format=json&$top=50&$orderby=Date desc&$expand=Контрагент
```

**Маппинг в контракт заказа (демо-решение, не свойство 1С):**

| Поле заказа | Источник |
|---|---|
| order_id | `Number` |
| product | `Контрагент.Description` |
| qty | сумма `Товары.Количество` |
| due_date | дата `Date` без времени |
| spec_id | `РеализацияТоваровУслуг` (тип документа) |
| priority | всегда `normal` |

Важно: в DemoAgent **нет документа заказов**, есть продажи. Поэтому
`spec_id` показывает реальный тип документа, а не выдаёт продажи за заказ.

**Публикация (нужен администратор):**

```
"C:\Program Files (x86)\1cv8t\8.3.27.1508\bin\webinstt.exe" ^
  -deploy -wsdir mfg -dir C:\inetpub\wwwroot\mfg ^
  -connstr "File=C:\1c_bases\DemoAgent;" ^
  -confpath C:\inetpub\wwwroot\mfg\default.vrd
```

После публикации в свойствах публикации включить «Стандартный интерфейс OData».

**Настройки backend:**

```
ONES_MODE=odata
ONES_HTTP_URL=http://localhost/mfg/odata/standard.odata
ONES_HTTP_USER=<пользователь 1С>
ONES_HTTP_PASSWORD=<пароль>
```

**Проверка:** `GET /api/v1/orders` → `"source": "odata"`.
