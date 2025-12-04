# states/battleblock.py
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router, types, F


class BattleBlock(StatesGroup):
    active = State()


router = Router()


@router.callback_query(
    BattleBlock.active,
    ~(
        F.data.startswith("fight:")
        | F.data.startswith("inventory:battle")
        | F.data.startswith("inventory:use:")
    ),
)
async def block_other_callbacks(callback: types.CallbackQuery):
    await callback.answer("❌ Не сбежишь!", show_alert=True)


@router.message(BattleBlock.active)
async def block_other_callbacks(message: types.Message):
    await message.answer(
        "❌ Не сбежишь!",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="Назад", callback_data="fight:menu")]
            ]
        ),
    )
