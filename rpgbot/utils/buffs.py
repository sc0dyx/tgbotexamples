from utils.db import Database, PlayerRepo, InventoryRepo
from config import DB_PATH

db = Database(DB_PATH)
player_repo = PlayerRepo(db)
inventory_repo = InventoryRepo(db)


def has_item(player_id: int, item_type: str) -> bool:
    items = inventory_repo.get_player_items(player_id)
    return any(it[2] == item_type for it in items)


def apply_attack_buff(player_id: int, base_damage: int) -> int:
    player = player_repo.get_player(player_id)
    player_class = player[2]

    if player_class == "warrior" and has_item(player_id, "weapon_warrior"):
        return base_damage + 5
    elif player_class == "mage" and has_item(player_id, "weapon_mage"):
        return base_damage + 10
    elif player_class == "rogue" and has_item(player_id, "weapon_rogue"):
        heal = int(base_damage * 0.1)
        new_hp = min(player[6], player[4] + heal)  # hp не выше max_hp
        player_repo.update_hp(player_id, new_hp)
    return base_damage


def apply_defend_buff(player_id: int, base_damage: int) -> int:
    player = player_repo.get_player(player_id)
    player_class = player[2]

    if player_class == "warrior" and has_item(player_id, "weapon_warrior"):
        return base_damage + 3
    return base_damage


def apply_gold_buff(player_id: int, base_gold: int) -> int:
    player = player_repo.get_player(player_id)
    player_class = player[2]

    if player_class == "rogue" and has_item(player_id, "weapon_rogue"):
        return int(base_gold * 1.2)  # +20% золота
    return base_gold
