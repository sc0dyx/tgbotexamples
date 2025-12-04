from utils.db import Database, QuestRepo, PlayerRepo, InventoryRepo
from config import DB_PATH

db = Database(DB_PATH)
quest_repo = QuestRepo(db)
player_repo = PlayerRepo(db)
inventory_repo = InventoryRepo(db)


def complete_quest(player_id: int, quest_id: int) -> str:
    quest = quest_repo.get_quest(quest_id)
    (
        _,
        title,
        _,
        reward_exp,
        reward_gold,
        reward_item_id,
        _,
        _,
        _,
    ) = quest

    db.execute(
        "UPDATE player_quests SET status='completed' WHERE player_id=? AND quest_id=?",
        (player_id, quest_id),
    )

    player_repo.update_gold(player_id, reward_gold)
    db.execute("UPDATE players SET exp = exp + ? WHERE id=?", (reward_exp, player_id))
    if reward_item_id:
        inventory_repo.add_item_to_player(player_id, reward_item_id, 1)

    return f"🎉 Квест '{title}' выполнен!\n📈 EXP: {reward_exp}\n💰 Gold: {reward_gold}"


def check_quests(player_id: int, event_type: str, target_id: int, amount: int = 1):
    """
    event_type: 'kill_mob' | 'collect_item' | 'reach_level'
    target_id: mob_id / item_id / level
    amount: прогресс, добавляемый за событие
    """
    active = db.fetchall(
        """
        SELECT pq.quest_id, pq.progress, q.condition_type, q.condition_target, q.condition_amount
        FROM player_quests AS pq
        JOIN quests AS q ON pq.quest_id = q.id
        WHERE pq.player_id=? AND pq.status='active'
        """,
        (player_id,),
    )

    messages = []
    for quest_id, progress, cond_type, target, cond_amount in active:
        if cond_type != event_type:
            continue
        if cond_type == "kill_mob":
            if target == 0 or target == target_id:
                progress += amount
        elif cond_type == "collect_item":
            if target == target_id:
                progress += amount
        elif cond_type == "reach_level":
            if target_id >= target:
                progress = cond_amount

        db.execute(
            "UPDATE player_quests SET progress=? WHERE player_id=? AND quest_id=?",
            (progress, player_id, quest_id),
        )

        if progress >= cond_amount:
            messages.append(complete_quest(player_id, quest_id))

    return messages
