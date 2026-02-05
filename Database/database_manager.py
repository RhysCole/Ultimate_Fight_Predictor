from multiprocessing import allow_connection_pickling
import sqlite3
import pandas as pd
from typing import Optional, List

from Models.DB_Classes.Fighters import Fighter
from Models.DB_Classes.Fight import Fight
 
# Initialize the class with the path to your SQLite database file
class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    # Open the database connection automatically when using the 'with' statement
    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        # Set row_factory to Row so we can access columns by name like a dictionary
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        return self

    # Save changes and close the connection when the 'with' block ends
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.commit()
            self.conn.close()
            
    # Run a SQL query and turn the raw rows into a list of clean dictionaries
    def format_web_query(self, query):
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        
        # Grab the header names from the database table (e.g., 'Name', 'Record')
        despription = self.cursor.description
        column_names = [desc[0] for desc in despription]
        
        full_list = []
        # Loop through each row and pair the column names with the actual data
        for row in rows:
            dictionary = dict(zip(column_names, row))
            full_list.append(dictionary)
                    
        # Return the data in a format ready for a web API or front-end
        return full_list

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
        
        
    def bulk_insert_upcoming_fights(self, upcoming_fights: List[dict]):
        if not upcoming_fights:
            print("No upcoming fights to insert.")
            return
        
        data_to_insert = []
        for fight in upcoming_fights:
            red_name = fight.get('red_fighter_name')
            blue_name = fight.get('blue_fighter_name')
            event_date = fight.get('event_date')
            
            print("red_name", red_name)
            print("blue_name", blue_name)
            print("event_date", event_date)

            if not all([red_name, blue_name, event_date]):
                print(f"Skipping fight due to missing data: {fight}")
                continue
            
            red_id = self.get_fighter_id_by_name(red_name)
            blue_id = self.get_fighter_id_by_name(blue_name)

            if not red_id or not blue_id:
                print(f"Skipping fight: Could not find DB entry for {red_name} or {blue_name}")
                continue
            
            fight_key = f"{event_date}-{red_id}-{blue_id}"
            
            data_to_insert.append((
                event_date,
                red_id,
                blue_id,
                red_name,
                blue_name,
            ))

        if not data_to_insert:
            print("No valid fights to insert after processing.")
            return
            
        self.cursor.executemany("""
            INSERT OR IGNORE INTO upcoming (
                event_date,
                red_fighter_id,
                blue_fighter_id,
                red_fighter_name,
                blue_fighter_name
            ) VALUES ( ?, ?, ?, ?, ?)
        """, data_to_insert)    

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

    def update_all_fighters(self, glicko_players: dict, quality_score: dict):
        update_data = [
            (
                player.rating,
                player.rating_deviation,
                player.volatility,
                quality_score.get(fighter_id, 0.0),
                fighter_id
            )
            for fighter_id, player in glicko_players.items()
        ]

        self.cursor.executemany("""
            UPDATE fighters 
            SET elo_rating = ?, 
                rating_deviation = ?, 
                rating_volatility = ?,
                quality_score = ?
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

    def save_fight_elos(self, fight_snapshots: list):
        self.cursor.executemany("""
            UPDATE fights
            SET 
                red_fighter_elo_before = ?,
                red_fighter_elo_after = ?,
                blue_fighter_elo_before = ?,
                blue_fighter_elo_after = ?
            WHERE fight_id = ?
        """, fight_snapshots)

    def get_fighter_history(self, fighter_ids: list[int], date: str):
        placeholders = ",".join("?" * len(fighter_ids))

        query = f"""
            SELECT * FROM fights
                WHERE red_fighter_id IN ({placeholders}) OR blue_fighter_id IN ({placeholders})
                AND event_date < ? 
            ORDER BY event_date ASC
        """

        params = fighter_ids + fighter_ids + [date]

        df = pd.read_sql(query, self.conn , params = params)

        return df

    def get_fighter_by_id(self, fighter_id: int):
        query = f"""
            SELECT * FROM fighters WHERE id = ?
        """

        params = (fighter_id, )

        df = pd.read_sql(query, self.conn, params = params)

        fighter_data_dict = df.iloc[0].to_dict()

        return Fighter(fighter_data_dict)

    def get_fighter_ids(self):
        query = f"""
            SELECT id FROM fighters
        """

        df = pd.read_sql(query, self.conn)

        return df

    def update_fighter_styles(self, fighter_styles: list[dict]):
        if not fighter_styles:
            print("No styles to update.")
            return

        print(f"Updating style archetypes for {len(fighter_styles)} fighters...")

        update_data = [
            (
                style['primary_style'],
                style['secondary_style'],
                style['tertiary_attributes'],
                style['fighter_id']
            ) for style in fighter_styles
        ]

        self.cursor.executemany("""
                                UPDATE fighters
                                SET primary_style       = ?,
                                    secondary_style     = ?,
                                    tertiary_attributes = ?
                                WHERE id = ?
                                """, update_data)

        print(f"-> Successfully updated styles for {self.cursor.rowcount} records.")

    def get_fighter_styles(self, fighter_ids: list[int]) -> dict:
        if not fighter_ids:
            return {}

        placeholders = ",".join("?" * len(fighter_ids))
        query = f"""
            SELECT id, primary_style, secondary_style, tertiary_attributes 
            FROM fighters 
            WHERE id IN ({placeholders})
        """

        self.cursor.execute(query, fighter_ids)
        rows = self.cursor.fetchall()

        styles_map = {
            row['id']: {
                'primary_style': row['primary_style'],
                'secondary_style': row['secondary_style'],
                'tertiary_attributes': row['tertiary_attributes']
            }
            for row in rows
        }

        return styles_map
    
    
    def get_raw_fight_by_id(self, fight_id: int):
        query = """
            SELECT * FROM fights WHERE fight_id = ?
        """
        
        self.cursor.execute(query, (fight_id,))
        
        result = self.cursor.fetchone()
        
        return dict(result) if result else None






                ########        THESE ARE NOW API QUERIES       ########









    def get_fighter_id_by_name(self, fighter_name: str) -> Optional[int]:
        self.cursor.execute("SELECT id FROM fighters WHERE Name = ?", (fighter_name,))
        result = self.cursor.fetchone()
        return result['id'] if result else None
    
    
    def get_fight_by_fighter_id(self, fighter_id):
        query = f"""
            SELECT * FROM fights WHERE red_fighter_id = {fighter_id} OR blue_fighter_id = {fighter_id}
        """
        return self.format_web_query(query)
    
    def get_upcoming_by_fighter_id(self, fighter_id):
        query = f"""
            SELECT * FROM upcoming WHERE red_fighter_id = {fighter_id} OR blue_fighter_id = {fighter_id}
        """
        return self.format_web_query(query)

    def get_fight_by_id(self, fight_id):
        query = f"""
            SELECT * FROM fights WHERE fight_id = {fight_id}
        """
        return self.format_web_query(query)
    
    
    def get_upcoming_by_id(self, fight_id):
        query = f"""
            SELECT * FROM upcoming WHERE id = {fight_id}
        """
        return self.format_web_query(query)
    
    def get_recent_fights(self, count: int):
            query = f"""
                SELECT 
                    f.*, 
                    r.Name as red_fighter_name, 
                    b.Name as blue_fighter_name
                FROM fights f
                LEFT JOIN fighters r ON f.red_fighter_id = r.id
                LEFT JOIN fighters b ON f.blue_fighter_id = b.id
                ORDER BY f.event_date DESC 
                LIMIT {count}
            """
            return self.format_web_query(query)

    def get_all_fighters(self):
        query = f"""
            SELECT id, Name, Record FROM fighters
        """
        return self.format_web_query(query)
    
    
    def get_fighter_upcomings(self, fighter_id):        
        query = f"""SELECT * FROM upcoming WHERE red_fighter_id = {fighter_id} OR blue_fighter_id = {fighter_id}"""
        return self.format_web_query(query)
    
    
    def get_upcoming_fights(self) -> dict | None:
        query = f"""
            SELECT
                u.id,
                u.event_date,
                u.red_fighter_id,
                u.blue_fighter_id,
                u.red_fighter_name,
                u.blue_fighter_name,
                rf.Record AS red_fighter_record,
                bf.Record AS blue_fighter_record
            FROM
                upcoming u
            JOIN
                fighters rf ON u.red_fighter_id = rf.id
            JOIN
                fighters bf ON u.blue_fighter_id = bf.id
            ORDER BY
                u.event_date ASC
        """
        return self.format_web_query(query)
    
        
        self.cursor.execute(query, (user_id, fight_id, vote))    
        
    def get_vote_count(self, fight_id):
        query = f"""
            SELECT red_vote, blue_vote, draw_vote FROM user_votes WHERE id = ?
        """
        self.cursor.execute(query, (fight_id,))
        return self.cursor.fetchone()[0]
    
    def update_upcoming_vote_totals(self):
        """
        Syncs the vote totals from 'upcoming_votes' back to the
        'upcoming' table.
        """
        query = """
            UPDATE upcoming
            SET
                red_vote = (
                    SELECT COUNT(*)
                    FROM upcoming_votes
                    WHERE fight_id = upcoming.id AND vote = 0
                ),
                blue_vote = (
                    SELECT COUNT(*)
                    FROM upcoming_votes
                    WHERE fight_id = upcoming.id AND vote = 1
                ),
                draw_vote = (
                    SELECT COUNT(*)
                    FROM upcoming_votes
                    WHERE fight_id = upcoming.id AND vote = 2
                )
            WHERE
                EXISTS (
                    SELECT 1
                    FROM upcoming_votes
                    WHERE fight_id = upcoming.id
                );
        """
        self.cursor.execute(query)
        
    def check_vote(self, user_id, fight_id):
        query = f"""
            SELECT * FROM upcoming_votes WHERE user_id = {user_id} AND fight_id = {fight_id}
        """
        return self.format_web_query(query)
    
    def vote(self, fight_id, user_id, vote):
        query = f"""
            INSERT INTO upcoming_votes (user_id, fight_id, vote) VALUES ({user_id}, {fight_id}, {vote})
        """
        self.cursor.execute(query)
        
    def get_past_fights(self, fighter_id):            
                query = f"""
                    SELECT 
                        f.*, 
                        r.Name AS red_fighter_name, 
                        b.Name AS blue_fighter_name
                    FROM fights f
                    LEFT JOIN fighters r ON f.red_fighter_id = r.id
                    LEFT JOIN fighters b ON f.blue_fighter_id = b.id
                    WHERE f.red_fighter_id = {fighter_id} OR f.blue_fighter_id = {fighter_id}
                    ORDER BY f.event_date ASC
                """
                return self.format_web_query(query)
        
    def get_fighter_rank(self, fighter_id: int) -> int | None:
        query = """
            WITH FighterRanks AS (
                SELECT
                    id,
                    DENSE_RANK() OVER (ORDER BY quality_score DESC) as rank
                FROM
                    fighters
            )
            SELECT
                rank
            FROM
                FighterRanks
            WHERE
                id = ?
        """
        self.cursor.execute(query, (fighter_id,))
        result = self.cursor.fetchone()
        
        if result:
            return result[0]  
        
        return None
    
    def get_top_fighters(self, count, option):
            allowed_columns = ["elo_rating", "quality_score"]
            print(option)
            print(allowed_columns[option])
            
            query = f"""
                SELECT Name, Record, elo_rating, quality_score
                FROM fighters
                ORDER BY {allowed_columns[option]} DESC
                LIMIT ?
            """
            
            self.cursor.execute(query, (count,))
            return self.cursor.fetchall()
              
        
    def get_active_rivalries(self) -> list[dict]:
        query = """
            SELECT 
                f1.Name as red_fighter_name,
                f2.Name as blue_fighter_name,
                f1.id as red_fighter_id,
                f2.id as blue_fighter_id,
                r.fight_count
            FROM (
                SELECT 
                    MIN(red_fighter_id, blue_fighter_id) as id_a,
                    MAX(red_fighter_id, blue_fighter_id) as id_b,
                    COUNT(*) as fight_count
                FROM fights
                GROUP BY id_a, id_b
                HAVING COUNT(*) > 1
            ) r
            JOIN fighters f1 ON r.id_a = f1.id
            JOIN fighters f2 ON r.id_b = f2.id
            ORDER BY f1.elo_rating DESC
        """
        
        self.cursor.execute(query)
        return self.format_web_query(query)

        
    def get_rivalry_fights(self, fighter_1, fighter_2):
        query = f"""
        SELECT 
            f.red_fighter_id,
            f.blue_fighter_id,
            f1.Name as red_fighter_name,
            f2.Name as blue_fighter_name,
            f.event_date,
            f.win_method as win_method,
            f.final_round as final_round,
            f.event_url as event_url
        FROM fights f
        JOIN fighters f1 ON f.red_fighter_id = f1.id
        JOIN fighters f2 ON f.blue_fighter_id = f2.id
        WHERE 
            (f.red_fighter_id = {fighter_1} AND f.blue_fighter_id = {fighter_2})
            OR 
            (f.red_fighter_id = {fighter_2} AND f.blue_fighter_id = {fighter_1})
        ORDER BY f.event_date DESC
        """
        self.cursor.execute(query)
        return self.format_web_query(query)
    
        