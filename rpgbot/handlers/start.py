from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.db import Database, PlayerRepo
from config import DB_PATH

router = Router()
db = Database(DB_PATH)
player_repo = PlayerRepo(db)
kb_class = InlineKeyboardBuilder()
kb_class.button(text="⚔️ Воин", callback_data="class:warrior")
kb_class.button(text="🔮 Маг", callback_data="class:mage")
kb_class.button(text="🗡️ Вор", callback_data="class:rogue")
kb_class.adjust(1)

kb_menu = InlineKeyboardBuilder()
kb_menu.button(text="⚔️ В бой", callback_data="fight:start")
kb_menu.button(text="🎯 Квесты", callback_data="quests:menu")
kb_menu.button(text="🛒 Магазин", callback_data="shop:menu")
kb_menu.button(text="👤 Профиль", callback_data="profile:show")
kb_menu.adjust(2)


@router.message(Command("start"))
async def cmd_start(msg: types.Message):
    player = player_repo.get_player(msg.from_user.id)

    if player is None:
        await msg.answer("Выбери класс персонажа:", reply_markup=kb_class.as_markup())

    else:
        await msg.answer("Главное меню:", reply_markup=kb_menu.as_markup())


@router.callback_query(F.data.startswith("menu:back"))
async def back(callback: types.CallbackQuery):
    player = player_repo.get_player(callback.from_user.id)
    if player is None:
        await callback.message.edit_text(
            "Выбери класс персонажа:", reply_markup=kb_class.as_markup()
        )

    else:
        await callback.message.edit_text(
            "Главное меню:", reply_markup=kb_menu.as_markup()
        )


@router.callback_query(F.data.startswith("class:"))
async def choose_class(callback: types.CallbackQuery):
    chosen_class = callback.data.split(":")[1]
    player_repo.add_player(
        player_id=callback.from_user.id,
        name=callback.from_user.first_name,
        player_class=chosen_class,
    )
    await callback.message.edit_text(
        f"🎉 Персонаж создан!\n"
        f"Класс: {chosen_class.capitalize()}\n"
        f"Теперь можно открыть 👤 Профиль.",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:back")]
            ]
        ),
    )
