import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN
from setup import Init
from handlers import start, profile, fight, shop, quests, inventory
from states.battleblock import router as rt


async def main():
    Init.setup_all()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher()

    dp.include_router(rt)

    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(fight.router)
    dp.include_router(shop.router)
    dp.include_router(quests.router)
    dp.include_router(inventory.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
