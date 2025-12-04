# setup.py (фрагмент)

import sqlite3
from config import DB_PATH, DEFAULT_HP, DEFAULT_GOLD, DEFAULT_DIAMONDS, DEFAULT_MANA


class Init:
    @staticmethod
    def create_players():
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY,
                name TEXT,
                class TEXT,
                level INTEGER DEFAULT 1,
                hp INTEGER DEFAULT {DEFAULT_HP},
                max_hp INTEGER DEFAULT {DEFAULT_HP},
                max_inventory_slots INTEGER DEFAULT 20,
                mana INTEGER DEFAULT {DEFAULT_MANA},
                max_mana INTEGER DEFAULT {DEFAULT_MANA},
                exp INTEGER DEFAULT 0,
                gold INTEGER DEFAULT {DEFAULT_GOLD},
                diamonds INTEGER DEFAULT {DEFAULT_DIAMONDS}
            )
            """)
            conn.commit()

    @staticmethod
    def create_mobs():
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS mobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                hp INTEGER,
                attack INTEGER,
                exp_reward INTEGER,
                gold_reward INTEGER,
                drop_item_id INTEGER
            )
            """)
            cur.execute("SELECT COUNT(*) FROM mobs")
            count = cur.fetchone()[0]
            if count == 0:
                cur.executemany(
                    """
                    INSERT INTO mobs (name, hp, attack, exp_reward, gold_reward, drop_item_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [
                        ("Слизень", 30, 5, 10, 5, None),
                        ("Гоблин", 50, 10, 20, 10, None),
                        ("Орк", 80, 15, 30, 20, None),
                        ("Дракончик", 120, 20, 50, 50, None),
                    ],
                )
            conn.commit()

    @staticmethod
    def create_items():
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                type TEXT,
                power INTEGER,
                max_count INTEGER DEFAULT 9,
                price_gold INTEGER,
                price_diamonds INTEGER
            )
            """)
            conn.commit()

    @staticmethod
    def create_inventory():
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER,
                item_id INTEGER,
                quantity INTEGER DEFAULT 1
            )
            """)
            conn.commit()

    @staticmethod
    def create_quests():
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                reward_exp INTEGER,
                reward_gold INTEGER,
                reward_item_id INTEGER,
                condition_type TEXT NOT NULL,       -- kill_mob, collect_item, reach_level
                condition_target INTEGER NOT NULL,  -- mob_id / item_id / level
                condition_amount INTEGER DEFAULT 1
            )
            """)
            conn.commit()
            cur.execute("SELECT COUNT(*) FROM quests")
            count = cur.fetchone()[0]
            if count == 0:
                cur.executemany(
                    """
                    INSERT INTO quests (title, description, reward_exp, reward_gold, reward_item_id, condition_type, condition_target, condition_amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            "Первый шаг",
                            "Убей любого моба",
                            10,
                            5,
                            None,
                            "kill_mob",
                            0,
                            1,
                        ),
                        (
                            "Охота на гоблина",
                            "Победи гоблина",
                            20,
                            10,
                            None,
                            "kill_mob",
                            2,
                            1,
                        ),
                        (
                            "Сила орка",
                            "Сразись с орком",
                            30,
                            20,
                            None,
                            "kill_mob",
                            3,
                            1,
                        ),
                        (
                            "Драконья угроза",
                            "Победи дракончика",
                            50,
                            50,
                            None,
                            "kill_mоб",
                            4,
                            1,
                        ),
                    ],
                )
            conn.commit()

    @staticmethod
    def create_battles():
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS battles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER,
                mob_id INTEGER,
                mob_hp INTEGER,
                player_hp INTEGER,
                status TEXT DEFAULT 'active'
            )
            """)
            conn.commit()

    @staticmethod
    def create_player_quests():
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS player_quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER,
                quest_id INTEGER,
                status TEXT DEFAULT 'active',
                progress INTEGER DEFAULT 0
            )
            """)
            conn.commit()

    @staticmethod
    def setup_all():
        Init.create_players()
        Init.create_mobs()
        Init.create_items()
        Init.create_inventory()
        Init.create_quests()
        Init.create_battles()
        Init.create_player_quests()
        print("✅ Все таблицы созданы/проверены!")
