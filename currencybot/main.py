import asyncio
import re
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from scraper import get_rate_ru, get_rate_by  # парсеры для ЦБ РФ и НБ РБ
from config import TOKEN

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

main_kb_ru = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="💵 USD", callback_data="rate:USD"),
            InlineKeyboardButton(text="AUD", callback_data="rate:AUD"),
            InlineKeyboardButton(text="AZN", callback_data="rate:AZN"),
        ],
        [
            InlineKeyboardButton(text="💶 EUR", callback_data="rate:EUR"),
            InlineKeyboardButton(text="DZD", callback_data="rate:DZD"),
            InlineKeyboardButton(text="THB", callback_data="rate:THB"),
            InlineKeyboardButton(text="AMD", callback_data="rate:AMD"),
        ],
        [
            InlineKeyboardButton(text="BYN", callback_data="rate:BYN"),
            InlineKeyboardButton(text="BHD", callback_data="rate:BHD"),
            InlineKeyboardButton(text="BGN", callback_data="rate:BGN"),
            InlineKeyboardButton(text="BOB", callback_data="rate:BOB"),
            InlineKeyboardButton(text="BRL", callback_data="rate:BRL"),
            InlineKeyboardButton(text="KRW", callback_data="rate:KRW"),
        ],
        [
            InlineKeyboardButton(text="HKD", callback_data="rate:HKD"),
            InlineKeyboardButton(text="UAH", callback_data="rate:UAH"),
            InlineKeyboardButton(text="DDK", callback_data="rate:DDK"),
            InlineKeyboardButton(text="AED", callback_data="rate:AED"),
            InlineKeyboardButton(text="VND", callback_data="rate:VND"),
        ],
    ]
)
main_kb_by = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="💵 USD", callback_data="rate:USD"),
            InlineKeyboardButton(text="AUD", callback_data="rate:AUD"),
        ],
        [
            InlineKeyboardButton(text="💶 EUR", callback_data="rate:EUR"),
            InlineKeyboardButton(text="AMD", callback_data="rate:AMD"),
        ],
        [
            InlineKeyboardButton(text="RUB", callback_data="rate:RUB"),
            InlineKeyboardButton(text="BGN", callback_data="rate:BGN"),
            InlineKeyboardButton(text="BRL", callback_data="rate:BRL"),
        ],
        [
            InlineKeyboardButton(text="UAH", callback_data="rate:UAH"),
            InlineKeyboardButton(text="VND", callback_data="rate:VND"),
        ],
    ]
)


def back_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]]
    )


def main_kb(lang):
    if lang == "ru":
        main_kb = main_kb_ru
    elif lang == "by":
        main_kb = main_kb_by
    else:
        main_kb = main_kb_ru
    return main_kb


@dp.message(Command("start"))
async def start(message: Message):
    lang = message.from_user.language_code or "ru"
    await message.answer(
        f"Привет! Определён язык профиля: <b>{lang}</b>\nВыбери валюту:",
        reply_markup=main_kb(lang),
    )


@dp.callback_query(F.data.startswith("rate:"))
async def rate_callback(query: CallbackQuery):
    code = query.data.split(":")[1]

    lang = query.from_user.language_code or "ru"
    if lang == "ru":
        cc, count, name_b, currency, date = await get_rate_ru(code)  # ЦБ РФ
        src = "ЦБ РФ 🇷🇺"
        tr_code = "RUB"
    elif lang == "by":
        cc, count, name_b, currency, date = await get_rate_by(code)  # НБ РБ
        src = "НБ РБ 🇧🇾"
        tr_code = "BYN"
    currency = float(currency.replace(",", ".")) / int(count)
    await query.message.edit_text(
        f"Курс {code}→{tr_code}\n<b>{currency}</b>\n{name_b}\nДата: {date}\nИсточник: {src}",
        reply_markup=back_kb(),
    )

    await query.answer()


@dp.callback_query(F.data == "back")
async def back_callback(query: CallbackQuery):
    lang = query.from_user.language_code or "ru"
    await query.message.edit_text("Выбери валюту:", reply_markup=main_kb(lang))
    await query.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
