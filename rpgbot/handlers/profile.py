from aiogram import Router, types, F

from utils.db import Database, PlayerRepo
from config import DB_PATH

router = Router()
db = Database(DB_PATH)
player_repo = PlayerRepo(db)


@router.callback_query(F.data == "profile:show")
async def show_profile(callback: types.CallbackQuery):
    player = player_repo.get_player(callback.from_user.id)
    if player:
        # player = (id, name, class, level, hp, max_hp, mana, max_mana, exp, gold, diamonds)
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
                [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:back")]
            ]
        )

        await callback.message.edit_text(
            f"👤 {name}\n⚔️ Класс: {cls}\n⭐ Уровень: {lvl}\n❤️ HP: {hp}/{max_hp}\n🔮 Mana: {mana}/{max_mana}\n📈 EXP: {exp}\n💰 Gold: {gold}\n💎 Diamonds: {diamonds}",
            reply_markup=kb,
        )
    else:
        await callback.answer("Ты ещё не зарегистрирован!", show_alert=True)
