import asyncio
import re
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
)
from config import TOKEN
from model import model
from aiogram.enums import ChatAction, ParseMode

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(F.text)
async def handle_message(message: Message):
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    answer = model(message.text, message.chat.id)
    await message.answer(answer)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
