import sqlite3
from typing import Optional, List, Any

from Models.Fighters import Fighter
from Models.Fight import Fight
 
class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.commit()
            self.conn.close()

    def clear_tables(self, tables: list[str]):
        if not tables:
            self.cursor.execute("DELETE FROM fighters")
            self.cursor.execute("DELETE FROM fights")
            print("All Tables cleared successfully.")
        for table in tables:
            self.cursor.execute(f"DELETE FROM {table}")
            print(f"Table {table} cleared successfully.")


    def bulk_insert_fighters(self, fighters: list[Fighter]):
        if not fighters:
            print("No new fighters to insert.")
            return

        data_to_insert = [fighter.to_tuple_for_insert() for fighter in fighters]

        print(f"\nInserting {len(data_to_insert)} fighters into the database...")
        
        self.cursor.executemany("""
            INSERT OR IGNORE INTO fighters (
                Name, Nickname, Height, Weight, Reach, Stance, 
                Record, DOB, profile_url, elo_rating, 
                rating_deviation, rating_volatility
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data_to_insert)

        print(f"Finished inserting fighters. Processed {self.cursor.rowcount} new rows.")

    def bulk_insert_fights(self, fights: List[Fight]):
        if not fights:
            print("No new fights to insert.")
            return

        self.cursor.execute("SELECT id, Name FROM fighters")
        name_to_id_map = {row['Name']: row['id'] for row in self.cursor.fetchall()}
        
        for fight in fights:
            fight.red_fighter_id = name_to_id_map.get(fight.red_fighter_name)
            fight.blue_fighter_id = name_to_id_map.get(fight.blue_fighter_name)
            fight.winner_id = name_to_id_map.get(fight.winner_name)
            
        data_to_insert = [f.to_tuple_for_insert() for f in fights]

        print(f"Inserting {len(data_to_insert)} fights into the database...")
        self.cursor.executemany("""
                    INSERT OR IGNORE INTO fights (
                        red_fighter_id,
                        blue_fighter_id,
                        winner_id,
                        red_knockdowns,
                        blue_knockdowns,
                        red_sig_strikes,
                        blue_sig_strikes,
                        red_takedowns,
                        blue_takedowns,
                        red_sub_attempts,
                        blue_sub_attempts,
                        win_method,
                        final_round,
                        final_time_seconds,
                        event_date,
                        event_url,
                        is_completed,
                        red_elo,
                        blue_elo
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, data_to_insert)
        
        print(f"Finished inserting fights. Processed {self.cursor.rowcount} new rows.")
    

    def get_fighters(self, names: Optional[list[str]] = None) -> list[Fighter]:
        if names:
            placeholders = ",".join("?" * len(names))  # (?, ?, ?, ...)
            query = f"SELECT * FROM fighters WHERE name IN ({placeholders})"
            self.cursor.execute(query, names)
        else:
            query = "SELECT * FROM fighters"
            self.cursor.execute(query)

        rows = self.cursor.fetchall()
        if not rows:
            return []

        col_names = [desc[0] for desc in self.cursor.description]

        fighters = []
        for row in rows:
            fighter_data = dict(zip(col_names, row))
            fighters.append(Fighter(fighter_data))

        return fighters

    def get_fights(self, fighter_names: Optional[list[str]] = None) -> list[Fight]:
        if fighter_names:
            placeholders = ",".join("?" * len(fighter_names))

            query = f"""
                SELECT * FROM fights
                WHERE red_fighter_id IN (SELECT id FROM fighters WHERE Name IN ({placeholders}))
                   OR blue_fighter_id IN (SELECT id FROM fighters WHERE Name IN ({placeholders}))
            """
            self.cursor.execute(query, fighter_names * 2)
        else:
            query = "SELECT * FROM fights"
            self.cursor.execute(query)

        rows = self.cursor.fetchall()
        if not rows:
            return []

        fights = []
        for row in rows:
            fight_data = dict(row)
            fights.append(fight_data)

        return fights

    def update_all_fighters(self, glicko_players: dict):
        update_data = [
            (
                player.rating,
                player.rating_deviation,
                player.volatility,
                fighter_id
            )
            for fighter_id, player in glicko_players.items()
        ]

        self.cursor.executemany("""
            UPDATE fighters 
            SET elo_rating = ?, 
                rating_deviation = ?, 
                rating_volatility = ?
            WHERE id = ?
        """, update_data)

    def reset_fighter_ratings(self):
        default_rating = 1500.0
        default_rd = 350.0
        default_volatility = 0.06

        self.cursor.execute("""
            UPDATE fighters
            SET elo_rating        = ?,
                rating_deviation  = ?,
                rating_volatility = ?
            """, (default_rating, default_rd, default_volatility))