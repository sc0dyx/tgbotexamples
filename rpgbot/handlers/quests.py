# handlers/quests.py

from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.db import Database, QuestRepo, PlayerRepo, InventoryRepo
from config import DB_PATH

router = Router()
db = Database(DB_PATH)
quest_repo = QuestRepo(db)
player_repo = PlayerRepo(db)
inventory_repo = InventoryRepo(db)


@router.callback_query(F.data == "quests:menu")
async def quests_menu(callback: types.CallbackQuery):
    quests = quest_repo.list_quests()
    if not quests:
        await callback.answer("Нет доступных квестов!", show_alert=True)
        return

    kb = InlineKeyboardBuilder()
    text = "🎯 Доступные квесты:\n"
    for (
        quest_id,
        title,
        description,
        reward_exp,
        reward_gold,
        reward_item_id,
        condition_type,
        condition_target,
        condition_amount,
    ) in quests:
        cond = f"{condition_type}:{condition_target} x{condition_amount}"
        text += f"\n{title} — {description} (условие: {cond})"
        kb.button(text=f"Взять {title}", callback_data=f"quest:start:{quest_id}")
    kb.adjust(1)

    await callback.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("quest:start:"))
async def quest_start(callback: types.CallbackQuery):
    quest_id = int(callback.data.split(":")[2])
    quest = quest_repo.get_quest(quest_id)
    player = player_repo.get_player(callback.from_user.id)
    if not quest:
        await callback.answer("Квест не найден!", show_alert=True)
        return

    existing = db.fetchone(
        "SELECT status FROM player_quests WHERE player_id=? AND quest_id=?",
        (player[0], quest_id),
    )
    if existing:
        if existing[0] == "completed":
            await callback.answer("Ты уже выполнил этот квест!", show_alert=True)
            return
        elif existing[0] == "active":
            await callback.answer("Квест уже активен!", show_alert=True)
            return

    db.execute(
        "INSERT INTO player_quests (player_id, quest_id, status, progress) VALUES (?, ?, 'active', 0)",
        (player[0], quest_id),
    )

    (
        _,
        title,
        description,
        reward_exp,
        reward_gold,
        reward_item_id,
        condition_type,
        condition_target,
        condition_amount,
    ) = quest

    await callback.message.edit_text(
        f"🎯 Квест '{title}' взят!\n"
        f"Описание: {description}\n"
        f"Условие: {condition_type} → {condition_target} ×{condition_amount}\n"
        f"Награда: {reward_exp} EXP, {reward_gold}💰, {reward_item_id if reward_item_id else '—'}"
    )
