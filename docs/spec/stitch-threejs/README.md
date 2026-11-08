# Stitch / Three.js spec (исходник)

Распаковано из `D:\загрузки Chrome\three.js.html` (экспорт Google Stitch, 2026-11-08).

| Файл | Содержание |
|---|---|
| `spec.md` | Полная спецификация FACTORIA v4.8 (2.5D/3D/1C/OPC UA/AI Co-Pilot). |
| `prototype.html` | Standalone-прототип из §6.2 (React/Tailwind/Three.js через CDN). Только для локальной сверки, не для прод-контуры. |
| `server_app_mock.py` | Мок FastAPI из §6.1 (in-memory, не подключён к `D:\factoria`). |
| `templates_data.json` | Модель станков/шаблонов из §5.1 (DMU 50/TRUMPF/FANUC/AGV). |
| `DECISIONS.md` | Решения по интеграции в `D:\factoria` и расхождения с проектом. |

Прототип запускается изолированно: `cd docs/spec/stitch-threejs && python -m http.server 3099`, открыть `http://localhost:3099/prototype.html`. Требует доступ к CDN; в основной продукт CDN не переносятся.