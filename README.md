# Travel Assistant Backend (MVP)

Python 3.12 + FastAPI + SQLite. В первой версии ответы и цены **демонстрационные**: AI-агент и реальные API пока не подключены.

## Docker

```bash
docker compose up --build
```

Swagger UI: http://localhost:8000/docs
Health: http://localhost:8000/health

## Без Docker

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Тестовый сценарий

1. В Swagger откройте POST /chat и отправьте `{"message":"Хочу на море на неделю"}`.
2. Скопируйте `session_id` из ответа.
3. В GET /trips/{session_id} посмотрите сохранённый план.
4. POST /bookings: `{"session_id":"<ваш session_id>","option_id":"demo-antalya"}`.
5. После перезапуска сервера записи сохранятся благодаря SQLite.

## Следующие задачи

- согласовать схему TripOption с AI-разработчиком и командой данных;
- заменить mock-ответ на интеграцию агента;
- интегрировать поставщиков авиабилетов/отелей через разрешённые API;
- добавить реальные даты, состав группы, разбивку цен и проверки бюджета;
- добавить управление доступом перед публичным релизом.

Не публикуйте этот учебный API в интернете без авторизации и ограничений запросов.
