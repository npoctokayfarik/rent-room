import asyncio

from aiogram import Bot, Dispatcher

from app.bot.handlers import router
from app.core.config import get_settings
from app.core.database import init_models


async def main() -> None:
    settings = get_settings()
    await init_models()

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
