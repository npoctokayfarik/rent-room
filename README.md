# RentRoomWithCodex

Telegram bot + Mini App for apartment rentals.

## Stack

- aiogram 3
- FastAPI
- PostgreSQL (SQLAlchemy async + asyncpg)

## Run

1. Create `.env` from `.env.example`.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Start API:
   - `uvicorn app.main:app --reload`
4. Start bot:
   - `python -m app.bot_runner`
