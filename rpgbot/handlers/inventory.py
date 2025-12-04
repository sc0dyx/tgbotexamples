from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import random
from utils.db import Database, ItemRepo, InventoryRepo, PlayerRepo
from config import DB_PATH
from utils.leveling import check_level_up

router = Router()
db = Database(DB_PATH)
item_repo = ItemRepo(db)
inventory_repo = InventoryRepo(db)
player_repo = PlayerRepo(db)


def fight_menu_inline():
    kb = InlineKeyboardBuilder()
    kb.button(text="⚔️ Атака", callback_data="fight:attack")
    kb.button(text="🛡️ Защита", callback_data="fight:defend")
    kb.button(text="🔮 Магия", callback_data="fight:magic")
    kb.button(text="📦 Инвентарь", callback_data="inventory:battle")
    kb.adjust(2)
    return kb.as_markup()


def victory_menu_inline():
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="menu:back")
    kb.button(text="➡️ Следующий", callback_data="fight:start")
    kb.adjust(2)
    return kb.as_markup()


# ---------- Профильный инвентарь ----------
@router.callback_query(F.data == "inventory:profile")
async def inventory_profile(callback: types.CallbackQuery):
    player = player_repo.get_player(callback.from_user.id)
    items = inventory_repo.get_player_items(player[0])

    if not items:
        kb = InlineKeyboardBuilder()
        kb.button(text="⬅️ Назад", callback_data="profile:show")
        await callback.message.edit_text(
            "📦 Инвентарь пуст!", reply_markup=kb.as_markup()
        )
        return

    kb = InlineKeyboardBuilder()
    text = "📦 Твой инвентарь:\n"
    for item_id, name, type_, qty, usable_in_fight, usable_in_profile in items:
        text += f"\n{name} x{qty}"
        if usable_in_profile:
            kb.button(
                text=f"Использовать {name}",
                callback_data=f"inventory:use:{item_id}:profile",
            )
        kb.button(text=f"Продать {name}", callback_data=f"inventory:sell:{item_id}")
    kb.button(text="⬅️ Назад", callback_data="profile:show")
    kb.adjust(2)
    await callback.message.edit_text(text, reply_markup=kb.as_markup())


# ---------- Боевой инвентарь ----------
@router.callback_query(F.data == "inventory:battle")
async def inventory_battle(callback: types.CallbackQuery):
    player = player_repo.get_player(callback.from_user.id)
    items = inventory_repo.get_player_items(player[0])

    if not items:
        kb = InlineKeyboardBuilder()
        kb.button(text="⬅️ Назад", callback_data="fight:menu")
        await callback.message.edit_text(
            "📦 Инвентарь пуст!", reply_markup=kb.as_markup()
        )
        return

    kb = InlineKeyboardBuilder()
    text = "⚔️ Боевой инвентарь:\n"
    for item_id, name, type_, qty, usable_in_fight, usable_in_profile in items:
        text += f"\n{name} x{qty}"
        if usable_in_fight:
            kb.button(
                text=f"Использовать {name}",
                callback_data=f"inventory:use:{item_id}:battle",
            )
    kb.button(text="⬅️ Назад", callback_data="fight:menu")
    kb.adjust(1)
    await callback.message.edit_text(text, reply_markup=kb.as_markup())


# ---------- Использование предметов ----------
@router.callback_query(F.data.startswith("inventory:use:"))
async def inventory_use(callback: types.CallbackQuery, state: FSMContext):
    _, _, item_id, mode = callback.data.split(":")
    item_id = int(item_id)
    player = player_repo.get_player(callback.from_user.id)
    item = item_repo.get_item(item_id)

    if not item or not player:
        await callback.answer("Ошибка!", show_alert=True)
        return

    (
        _,
        name,
        type_,
        power,
        max_count,
        price_gold,
        price_diamonds,
        usable_in_fight,
        usable_in_profile,
    ) = item

    if mode == "profile" and not usable_in_profile:
        await callback.answer(
            "Этот предмет нельзя использовать в профиле!", show_alert=True
        )
        return
    if mode == "battle" and not usable_in_fight:
        await callback.answer(
            "Этот предмет нельзя использовать в бою!", show_alert=True
        )
        return

    msg = ""

    if type_ == "potion_hp":
        new_hp = min(player[4] + power, player[5])
        db.execute("UPDATE players SET hp=? WHERE id=?", (new_hp, player[0]))
        msg = f"🧪 Ты использовал {name}! HP восстановлено до {new_hp}/{player[5]}"
        if mode == "battle":
            db.execute(
                "UPDATE battles SET player_hp=? WHERE player_id=? AND status='active'",
                (new_hp, player[0]),
            )
    elif type_ == "potion_mana":
        new_mana = min(player[7] + power, player[8])
        db.execute("UPDATE players SET mana=? WHERE id=?", (new_mana, player[0]))
        msg = f"🧪 Ты использовал {name}! Мана восстановлена до {new_mana}/{player[8]}"
    elif type_ == "bomb" and mode == "battle":
        battle = db.fetchone(
            "SELECT id, mob_id, mob_hp, player_hp FROM battles WHERE player_id=? AND status='active'",
            (player[0],),
        )
        if not battle:
            await callback.answer("Нет активного боя!", show_alert=True)
            return
        battle_id, mob_id, mob_hp, player_hp = battle
        mob_hp = max(mob_hp - power, 0)
        db.execute("UPDATE battles SET mob_hp=? WHERE id=?", (mob_hp, battle_id))
        msg = f"💣 Ты использовал {name}! Моб получил {power} урона.\n💀 HP моба: {mob_hp}"
    else:
        await callback.answer(
            "Этот предмет не имеет боевого/профильного эффекта!", show_alert=True
        )
        return

    db.execute(
        "UPDATE inventory SET quantity = quantity - 1 WHERE player_id=? AND item_id=?",
        (player[0], item_id),
    )
    db.execute(
        "DELETE FROM inventory WHERE player_id=? AND item_id=? AND quantity<=0",
        (player[0], item_id),
    )

    if mode == "profile":
        await callback.message.edit_text(
            msg,
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="⬅️ Назад", callback_data="inventory:profile"
                        )
                    ]
                ]
            ),
        )
        return

    battle = db.fetchone(
        "SELECT id, mob_id, mob_hp, player_hp FROM battles WHERE player_id=? AND status='active'",
        (player[0],),
    )
    if not battle:
        await callback.message.edit_text(
            msg,
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="⬅️ Назад", callback_data="menu:back"
                        )
                    ]
                ]
            ),
        )
        return

    battle_id, mob_id, mob_hp, player_hp = battle
    mob = db.fetchone(
        "SELECT id, name, hp, attack, exp_reward, gold_reward, drop_item_id FROM mobs WHERE id=?",
        (mob_id,),
    )
    _, mob_name, _, mob_attack, exp_reward, gold_reward, drop_item_id = mob

    if mob_hp <= 0:
        player_repo.update_gold(player[0], gold_reward)
        db.execute("UPDATE battles SET status='finished' WHERE id=?", (battle_id,))
        db.execute(
            "UPDATE players SET exp = exp + ? WHERE id=?", (exp_reward, player[0])
        )
        check_level_up(player[0])
        await state.clear()
        drop_text = ""
        if drop_item_id:
            inventory_repo.add_item_to_player(player[0], drop_item_id, 1)
            item_row = db.fetchone("SELECT name FROM items WHERE id=?", (drop_item_id,))
            drop_text = (
                f"\n🎁 Выпал предмет: {item_row[0]}"
                if item_row
                else "\n🎁 Выпал предмет!"
            )

        current_mana = player_repo.get_player(player[0])[7]
        max_mana = player_repo.get_player(player[0])[8]
        await callback.message.edit_text(
            msg
            + f"\n🎉 Победа над {mob_name}!\n📈 EXP: {exp_reward}\n💰 Gold: {gold_reward}\n🔮 Твоя мана: {current_mana}/{max_mana}{drop_text}",
            reply_markup=victory_menu_inline(),
        )
        return

    mob_dmg = random.randint(1, mob_attack)

    battle = db.fetchone("SELECT player_hp FROM battles WHERE id=?", (battle_id,))
    current_player_hp = battle[0] if battle else player_hp
    current_player_hp = max(current_player_hp - mob_dmg, 0)

    player_repo.update_hp(player[0], current_player_hp)
    db.execute(
        "UPDATE battles SET player_hp=? WHERE id=?", (current_player_hp, battle_id)
    )

    if current_player_hp <= 0:
        db.execute("UPDATE battles SET status='finished' WHERE id=?", (battle_id,))

        db.execute(
            "UPDATE players SET hp = max_hp, mana = max_mana, exp = 0 WHERE id=?",
            (player[0],),
        )
        lost_gold = int(player[10] * 0.2)
        db.execute(
            "UPDATE players SET gold = gold - ? WHERE id=?", (lost_gold, player[0])
        )

        await state.clear()
        await callback.message.edit_text(
            msg
            + f"\n👊 {mob_name} нанёс {mob_dmg}.\n💀 Ты проиграл!\n❤️ HP восстановлено до {player[5]}.\n💰 Потеряно {lost_gold} золота.\n📈 Опыт обнулён.",
            reply_markup=victory_menu_inline(),
        )
        return

    refreshed = player_repo.get_player(player[0])
    mana, max_mana = refreshed[7], refreshed[8]

    await callback.message.edit_text(
        msg + f"\n👊 {mob_name} ответил и нанёс {mob_dmg}.\n"
        f"❤️ Твоё HP: {current_player_hp}/{refreshed[5]}\n"
        f"💀 HP моба: {mob_hp}\n"
        f"🔮 Твоя мана: {mana}/{max_mana}\n"
        f"Выбери действие:",
        reply_markup=fight_menu_inline(),
    )


# ---------- Продажа предметов (только профиль) ----------
@router.callback_query(F.data.startswith("inventory:sell:"))
async def inventory_sell(callback: types.CallbackQuery):
    item_id = int(callback.data.split(":")[2])
    player = player_repo.get_player(callback.from_user.id)
    item = item_repo.get_item(item_id)

    if not item or not player:
        await callback.answer("Ошибка!", show_alert=True)
        return

    (
        _,
        name,
        type_,
        power,
        max_count,
        price_gold,
        price_diamonds,
        usable_in_fight,
        usable_in_profile,
    ) = item
    sell_price = max(price_gold // 2, 1)

    player_repo.update_gold(player[0], sell_price)
    db.execute(
        "UPDATE inventory SET quantity = quantity - 1 WHERE player_id=? AND item_id=?",
        (player[0], item_id),
    )
    db.execute(
        "DELETE FROM inventory WHERE player_id=? AND item_id=? AND quantity<=0",
        (player[0], item_id),
    )

    await callback.message.answer(f"💰 Ты продал {name} за {sell_price} золота!")
