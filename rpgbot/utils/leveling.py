import math
from utils.db import Database, PlayerRepo
from config import DB_PATH

db = Database(DB_PATH)
player_repo = PlayerRepo(db)


def exp_required(level: int) -> int:
    base = 50
    p = 2
    scale = 5
    m = 0.1
    return int(base * (level**p) + scale * math.exp(m * level))


def check_level_up(player_id: int):
    player = player_repo.get_player(player_id)
    level = player[3]
    exp = player[9]
    max_hp = player[5]
    max_mana = player[8]

    while exp >= exp_required(level):
        exp -= exp_required(level)
        level += 1
        max_hp += 10
        max_mana += 5

        db.execute(
            "UPDATE players SET level=?, exp=?, max_hp=?, hp=?, max_mana=?, mana=? WHERE id=?",
            (level, exp, max_hp, max_hp, max_mana, max_mana, player_id),
        )
