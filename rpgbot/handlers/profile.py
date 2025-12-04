from aiogram import Router, types, F

from utils.leveling import exp_required
from utils.db import Database, PlayerRepo
from config import DB_PATH

router = Router()
db = Database(DB_PATH)
player_repo = PlayerRepo(db)


@router.callback_query(F.data == "profile:show")
async def show_profile(callback: types.CallbackQuery):
    player = player_repo.get_player(callback.from_user.id)
    if player:
        (
            _,
            name,
            cls,
            lvl,
            hp,
            max_hp,
            max_inventory_slots,
            mana,
            max_mana,
            exp,
            gold,
            diamonds,
        ) = player

        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="📦 Инвентарь", callback_data="inventory:profile"
                    )
                ],
                [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:back")],
            ]
        )

        exp_to_next = exp_required(lvl)
        await callback.message.edit_text(
            f"👤 {name}\n⚔️ Класс: {cls}\n⭐ Уровень: {lvl}\n❤️ HP: {hp}/{max_hp}\n🔮 Mana: {mana}/{max_mana}\n📈 EXP: {exp}/{exp_to_next}\n💰 Gold: {gold}\n💎 Diamonds: {diamonds}",
            reply_markup=kb,
        )
    else:
        await callback.answer("Ты ещё не зарегистрирован!", show_alert=True)
