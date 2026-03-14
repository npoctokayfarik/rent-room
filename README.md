# RentRoomWithCodex

Telegram bot + Mini App for apartment rentals.

## Stack

- aiogram 3
- FastAPI
- PostgreSQL (SQLAlchemy async + asyncpg)

## Как запустить

### 1) Подготовить окружение

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Подготовить `.env`

```bash
cp .env.example .env
```

Заполните минимум:
- `BOT_TOKEN` — токен Telegram-бота от BotFather
- `DATABASE_URL` — строка подключения к PostgreSQL

Пример `DATABASE_URL`:

```text
postgresql://postgres:postgres@localhost:5432/rent_room
```

> Важно: по умолчанию приложение рассчитано на PostgreSQL (`asyncpg`).

### 3) Запустить API

```bash
uvicorn app.main:app --reload
```

Проверка здоровья:

```bash
curl http://127.0.0.1:8000/health
```

Открыть Mini App:
- http://127.0.0.1:8000/miniapp

### 4) Запустить Telegram-бота (отдельным процессом)

```bash
python -m app.bot_runner
```

## Быстрый локальный старт PostgreSQL (Docker)

Если PostgreSQL не установлен локально:

```bash
docker run --name rent-room-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=rent_room \
  -p 5432:5432 -d postgres:16
```

Тогда `DATABASE_URL` в `.env`:

```text
postgresql://postgres:postgres@localhost:5432/rent_room
```


## Частая ошибка: `ConnectionRefusedError: [Errno 111] Connection refused`

Эта ошибка при `uvicorn app.main:app --reload` означает, что API не может подключиться к PostgreSQL по `DATABASE_URL`.

Что проверить:
1. PostgreSQL запущен и доступен на хосте/порту из `DATABASE_URL`.
2. Пользователь/пароль/БД в `DATABASE_URL` существуют.
3. Если работаете в Codespaces/DevContainer, используйте правильный хост (часто `localhost`, если порт проброшен).

Быстро поднять БД через Docker:

```bash
docker run --name rent-room-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=rent_room \
  -p 5432:5432 -d postgres:16
```

И в `.env`:

```text
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rent_room
```

Если нужно запустить API без падения на старте (например, для проверки роутов/шаблонов), можно временно отключить fail-fast:

```text
DB_FAIL_FAST_ON_STARTUP=false
```

Тогда приложение стартует, но роуты, требующие БД, всё равно будут недоступны, пока БД не поднимется.
