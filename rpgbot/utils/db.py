import sqlite3
from typing import Optional, List, Tuple
from config import DB_PATH, DEFAULT_HP, DEFAULT_MANA, DEFAULT_DIAMONDS, DEFAULT_GOLD


class Database:
    def __init__(self, path: str = DB_PATH):
        self.conn = sqlite3.connect(path)
        self.cur = self.conn.cursor()

    def execute(self, query: str, params: Tuple = ()):
        self.cur.execute(query, params)
        self.conn.commit()

    def fetchone(self, query: str, params: Tuple = ()):
        self.cur.execute(query, params)
        return self.cur.fetchone()

    def fetchall(self, query: str, params: Tuple = ()):
        self.cur.execute(query, params)
        return self.cur.fetchall()


# ------------------ Players ------------------
class PlayerRepo:
    def __init__(self, db: Database):
        self.db = db

    def add_player(self, player_id: int, name: str, player_class: str):
        self.db.execute(
            """INSERT INTO players 
            (id, name, class, level, hp, max_hp, mana, max_mana, exp, gold, diamonds, max_inventory_slots)
            VALUES (?, ?, ?, 1, ?, ?, ?, ?, 0, ?, ?, 20)""",
            (
                player_id,
                name,
                player_class,
                DEFAULT_HP,
                DEFAULT_HP,
                DEFAULT_MANA,
                DEFAULT_MANA,
                DEFAULT_GOLD,
                DEFAULT_DIAMONDS,
            ),
        )

    def get_player(self, player_id: int) -> Optional[Tuple]:
        return self.db.fetchone("SELECT * FROM players WHERE id=?", (player_id,))

    def update_hp(self, player_id: int, new_hp: int):
        self.db.execute("UPDATE players SET hp=? WHERE id=?", (new_hp, player_id))

    def update_gold(self, player_id: int, amount: int):
        self.db.execute(
            "UPDATE players SET gold = gold + ? WHERE id=?", (amount, player_id)
        )

    def update_diamonds(self, player_id: int, amount: int):
        self.db.execute(
            "UPDATE players SET diamonds = diamonds + ? WHERE id=?", (amount, player_id)
        )


# ------------------ Mobs ------------------
class MobRepo:
    def __init__(self, db: Database):
        self.db = db

    def list_mobs(self) -> List[Tuple]:
        return self.db.fetchall("SELECT * FROM mobs")

    def get_mob(self, mob_id: int) -> Optional[Tuple]:
        return self.db.fetchone("SELECT * FROM mobs WHERE id=?", (mob_id,))


# ------------------ Items ------------------
class ItemRepo:
    def __init__(self, db: Database):
        self.db = db

    def list_items(self) -> List[Tuple]:
        return self.db.fetchall("SELECT * FROM items")

    def get_item(self, item_id: int) -> Optional[Tuple]:
        return self.db.fetchone("SELECT * FROM items WHERE id=?", (item_id,))


# ------------------ Inventory ------------------
class InventoryRepo:
    def __init__(self, db: Database):
        self.db = db

    def add_item_to_player(self, player_id: int, item_id: int, quantity: int = 1):
        # Узнаём max_count для предмета
        item = self.db.fetchone("SELECT max_count FROM items WHERE id=?", (item_id,))
        max_count = item[0] if item else 9

        # Проверяем, есть ли предмет у игрока
        existing = self.db.fetchone(
            "SELECT id, quantity FROM inventory WHERE player_id=? AND item_id=? ORDER BY id DESC",
            (player_id, item_id),
        )

        if existing:
            inv_id, current_qty = existing
            new_qty = current_qty + quantity

            if new_qty <= max_count:
                self.db.execute(
                    "UPDATE inventory SET quantity=? WHERE id=?", (new_qty, inv_id)
                )
            else:
                self.db.execute(
                    "UPDATE inventory SET quantity=? WHERE id=?", (max_count, inv_id)
                )

                leftover = new_qty - max_count
                self.db.execute(
                    "INSERT INTO inventory (player_id, item_id, quantity) VALUES (?, ?, ?)",
                    (player_id, item_id, leftover),
                )
        else:
            self.db.execute(
                "INSERT INTO inventory (player_id, item_id, quantity) VALUES (?, ?, ?)",
                (player_id, item_id, min(quantity, max_count)),
            )
            leftover = quantity - max_count
            while leftover > 0:
                qty = min(leftover, max_count)
                self.db.execute(
                    "INSERT INTO inventory (player_id, item_id, quantity) VALUES (?, ?, ?)",
                    (player_id, item_id, qty),
                )
                leftover -= qty

    def get_inventory(self, player_id: int) -> List[Tuple]:
        return self.db.fetchall(
            "SELECT * FROM inventory WHERE player_id=?", (player_id,)
        )

    def get_player_items(self, player_id: int) -> List[Tuple]:
        """
        Возвращает список предметов игрока с названием, типом, количеством и флагами использования.
        Формат: (item_id, name, type, quantity, usable_in_fight, usable_in_profile)
        """
        return self.db.fetchall(
            """
            SELECT items.id, items.name, items.type, inventory.quantity,
                items.usable_in_fight, items.usable_in_profile
            FROM inventory
            JOIN items ON inventory.item_id = items.id
            WHERE inventory.player_id=?
            """,
            (player_id,),
        )


# ------------------ Quests ------------------
class QuestRepo:
    def __init__(self, db: Database):
        self.db = db

    def list_quests(self) -> List[Tuple]:
        return self.db.fetchall("SELECT * FROM quests")

    def get_quest(self, quest_id: int) -> Optional[Tuple]:
        return self.db.fetchone("SELECT * FROM quests WHERE id=?", (quest_id,))
