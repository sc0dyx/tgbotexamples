# handlers/fight.py

SPELL_COST = 10
import random
from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.db import Database, PlayerRepo, MobRepo, InventoryRepo
from utils.quest_logic import check_quests
from config import DB_PATH

router = Router()
db = Database(DB_PATH)
player_repo = PlayerRepo(db)
mob_repo = MobRepo(db)
inventory_repo = InventoryRepo(db)


def fight_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="⚔️ Атака", callback_data="fight:attack")
    kb.button(text="🛡️ Защита", callback_data="fight:defend")
    kb.button(text="🔮 Магия", callback_data="fight:magic")
    kb.adjust(2)
    return kb.as_markup()


async def fight_defeat(callback, player, battle_id, name, mob_dmg, text):
    db.execute("UPDATE battles SET status='finished' WHERE id=?", (battle_id,))
    db.execute("UPDATE players SET hp = max_hp WHERE id=?", (player[0],))
    db.execute("UPDATE players SET mana = max_mana WHERE id=?", (player[0],))
    lost_gold = int(player[10] * 0.2)
    db.execute("UPDATE players SET gold = gold - ? WHERE id=?", (lost_gold, player[0]))
    db.execute("UPDATE players SET exp = 0 WHERE id=?", (player[0],))
    await callback.message.edit_text(
        text + f"👊 {name} нанёс {mob_dmg}.\n💀 Ты проиграл!\n"
        f"❤️ HP восстановлено до {player[5]}.\n"
        f"💰 Потеряно {lost_gold} золота.\n"
        f"📈 Опыт обнулён."
    )


@router.callback_query(F.data == "fight:start")
async def start_fight(callback: types.CallbackQuery):
    player = player_repo.get_player(callback.from_user.id)
    if not player:
        await callback.answer("Сначала зарегистрируйся!", show_alert=True)
        return

    db.execute(
        "UPDATE battles SET status='finished' WHERE player_id=? AND status='active'",
        (player[0],),
    )

    mobs = mob_repo.list_mobs()
    if not mobs:
        await callback.answer("Нет мобов в базе!", show_alert=True)
        return

    mob = random.choice(mobs)
    mob_id, name, hp, attack, exp_reward, gold_reward, drop_item_id = mob

    db.execute(
        "INSERT INTO battles (player_id, mob_id, mob_hp, player_hp, status) VALUES (?, ?, ?, ?, 'active')",
        (player[0], mob_id, hp, player[4]),
    )

    # show mana at start
    mana, max_mana = player[7], player[8]
    await callback.message.edit_text(
        f"⚔️ Ты встретил {name}!\n"
        f"❤️ HP моба: {hp}\n"
        f"🔮 Твоя мана: {mana}/{max_mana}\n"
        f"Выбери действие:",
        reply_markup=fight_menu(),
    )


@router.callback_query(F.data == "fight:attack")
async def player_attack(callback: types.CallbackQuery):
    player = player_repo.get_player(callback.from_user.id)
    battle = db.fetchone(
        "SELECT id, mob_id, mob_hp, player_hp FROM battles WHERE player_id=? AND status='active'",
        (player[0],),
    )
    if not battle:
        await callback.answer("Бой не найден!", show_alert=True)
        return

    battle_id, mob_id, mob_hp, player_hp = battle
    mob = mob_repo.get_mob(mob_id)
    _, name, _, attack, exp_reward, gold_reward, drop_item_id = mob

    dmg = random.randint(5, 15)
    mob_hp = max(mob_hp - dmg, 0)
    text = f"⚔️ Ты ударил {name} на {dmg}!\n"

    if mob_hp <= 0:
        player_repo.update_gold(player[0], gold_reward)
        db.execute("UPDATE battles SET status='finished' WHERE id=?", (battle_id,))
        db.execute(
            "UPDATE players SET exp = exp + ? WHERE id=?", (exp_reward, player[0])
        )

        drop_text = ""
        if drop_item_id:
            inventory_repo.add_item_to_player(player[0], drop_item_id, 1)
            item = db.fetchone("SELECT name FROM items WHERE id=?", (drop_item_id,))
            drop_text = (
                f"\n🎁 Выпал предмет: {item[0]}" if item else "\n🎁 Выпал предмет!"
            )

        mana, max_mana = player[7], player[8]
        await callback.message.edit_text(
            text + f"🎉 Победа над {name}!\n"
            f"📈 EXP: {exp_reward}\n"
            f"💰 Gold: {gold_reward}\n"
            f"🔮 Твоя мана: {mana}/{max_mana}"
            f"{drop_text}"
        )

        messages = check_quests(player[0], "kill_mob", mob_id, 1)
        for msg in messages:
            await callback.message.answer(msg)
        return

    mob_dmg = random.randint(1, attack)
    player_hp = max(player_hp - mob_dmg, 0)
    player_repo.update_hp(player[0], player_hp)

    mana, max_mana = player[7], player[8]
    if player_hp <= 0:
        await fight_defeat(callback, player, battle_id, name, mob_dmg, text)
    else:
        db.execute(
            "UPDATE battles SET mob_hp=?, player_hp=? WHERE id=?",
            (mob_hp, player_hp, battle_id),
        )
        await callback.message.edit_text(
            text + f"👊 {name} ответил и нанёс {mob_dmg}.\n"
            f"❤️ Твоё HP: {player_hp}/{player[5]}\n"
            f"💀 HP моба: {mob_hp}\n"
            f"🔮 Твоя мана: {mana}/{max_mana}\n"
            f"Выбери действие:",
            reply_markup=fight_menu(),
        )


@router.callback_query(F.data == "fight:magic")
async def player_magic(callback: types.CallbackQuery):
    player = player_repo.get_player(callback.from_user.id)
    if not player:
        await callback.answer("Сначала зарегистрируйся!", show_alert=True)
        return

    battle = db.fetchone(
        "SELECT id, mob_id, mob_hp, player_hp FROM battles WHERE player_id=? AND status='active'",
        (player[0],),
    )
    if not battle:
        await callback.answer("Бой не найден!", show_alert=True)
        return

    battle_id, mob_id, mob_hp, player_hp = battle
    mob = mob_repo.get_mob(mob_id)
    _, name, _, attack, exp_reward, gold_reward, drop_item_id = mob

    mana, max_mana = player[7], player[8]
    if mana < SPELL_COST:
        await callback.answer(
            f"Недостаточно маны (нужно {SPELL_COST})!", show_alert=True
        )
        return

    dmg = random.randint(15, 30)
    mob_hp = max(mob_hp - dmg, 0)

    # spend mana and use updated value for display
    mana = max(mana - SPELL_COST, 0)
    db.execute("UPDATE players SET mana=? WHERE id=?", (mana, player[0]))

    text = f"🔮 Ты используешь магию и наносишь {dmg} урона {name}!\n"

    if mob_hp <= 0:
        player_repo.update_gold(player[0], gold_reward)
        db.execute("UPDATE battles SET status='finished' WHERE id=?", (battle_id,))
        db.execute(
            "UPDATE players SET exp = exp + ? WHERE id=?", (exp_reward, player[0])
        )

        drop_text = ""
        if drop_item_id:
            inventory_repo.add_item_to_player(player[0], drop_item_id, 1)
            item = db.fetchone("SELECT name FROM items WHERE id=?", (drop_item_id,))
            drop_text = (
                f"\n🎁 Выпал предмет: {item[0]}" if item else "\n🎁 Выпал предмет!"
            )

        await callback.message.edit_text(
            text + f"🎉 Победа над {name}!\n"
            f"📈 EXP: {exp_reward}\n"
            f"💰 Gold: {gold_reward}\n"
            f"🔮 Твоя мана: {mana}/{max_mana}"
            f"{drop_text}"
        )

        messages = check_quests(player[0], "kill_mob", mob_id, 1)
        for msg in messages:
            await callback.message.answer(msg)
        return

    mob_dmg = random.randint(1, attack)
    player_hp = max(player_hp - mob_dmg, 0)
    player_repo.update_hp(player[0], player_hp)

    if player_hp <= 0:
        await fight_defeat(callback, player, battle_id, name, mob_dmg, text)
    else:
        db.execute(
            "UPDATE battles SET mob_hp=?, player_hp=? WHERE id=?",
            (mob_hp, player_hp, battle_id),
        )
        await callback.message.edit_text(
            text + f"👊 {name} ответил и нанёс {mob_dmg}.\n"
            f"❤️ Твоё HP: {player_hp}/{player[5]}\n"
            f"💀 HP моба: {mob_hp}\n"
            f"🔮 Твоя мана: {mana}/{max_mana}\n"
            f"Выбери действие:",
            reply_markup=fight_menu(),
        )


@router.callback_query(F.data == "fight:defend")
async def player_defend(callback: types.CallbackQuery):
    player = player_repo.get_player(callback.from_user.id)
    battle = db.fetchone(
        "SELECT id, mob_id, mob_hp, player_hp FROM battles WHERE player_id=? AND status='active'",
        (player[0],),
    )
    if not battle:
        await callback.answer("Бой не найден!", show_alert=True)
        return

    battle_id, mob_id, mob_hp, player_hp = battle
    mob = mob_repo.get_mob(mob_id)
    _, name, _, attack, exp_reward, gold_reward, drop_item_id = mob

    dmg = random.randint(3, 8)
    mob_hp = max(mob_hp - dmg, 0)

    mob_dmg = max(random.randint(1, attack) // 2, 0)
    player_hp = max(player_hp - mob_dmg, 0)
    player_repo.update_hp(player[0], player_hp)

    text = f"🛡️ Ты защищаешься и наносишь {dmg} урона {name}!\n"

    if mob_hp <= 0:
        player_repo.update_gold(player[0], gold_reward)
        db.execute("UPDATE battles SET status='finished' WHERE id=?", (battle_id,))
        db.execute(
            "UPDATE players SET exp = exp + ? WHERE id=?", (exp_reward, player[0])
        )

        drop_text = ""
        if drop_item_id:
            inventory_repo.add_item_to_player(player[0], drop_item_id, 1)
            item = db.fetchone("SELECT name FROM items WHERE id=?", (drop_item_id,))
            drop_text = (
                f"\n🎁 Выпал предмет: {item[0]}" if item else "\n🎁 Выпал предмет!"
            )

        mana, max_mana = player[7], player[8]
        await callback.message.edit_text(
            text + f"🎉 Победа над {name}!\n"
            f"📈 EXP: {exp_reward}\n"
            f"💰 Gold: {gold_reward}\n"
            f"🔮 Твоя мана: {mana}/{max_mana}"
            f"{drop_text}"
        )

        messages = check_quests(player[0], "kill_mob", mob_id, 1)
        for msg in messages:
            await callback.message.answer(msg)
        return

    mana, max_mana = player[7], player[8]
    if player_hp <= 0:
        await fight_defeat(callback, player, battle_id, name, mob_dmg, text)
    else:
        db.execute(
            "UPDATE battles SET mob_hp=?, player_hp=? WHERE id=?",
            (mob_hp, player_hp, battle_id),
        )
        await callback.message.edit_text(
            text + f"👊 {name} атакует, но твоя защита снижает урон!\n"
            f"❤️ Твоё HP: {player_hp}/{player[5]}\n"
            f"💀 HP моба: {mob_hp}\n"
            f"🔮 Твоя мана: {mana}/{max_mana}\n"
            f"Выбери действие:",
            reply_markup=fight_menu(),
        )
