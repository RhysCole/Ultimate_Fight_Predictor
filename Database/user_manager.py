import sqlite3
import pandas as pd
from typing import Optional, List

from config.config import DB_PATH

from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from Models.DB_Classes.User import User
class UserManager:
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
            
    def create_user(self, first_name: str, last_name: str, email: str, plain_text_password: str) -> Optional[int]:

        hashed_password = generate_password_hash(plain_text_password)
        
        try:
            self.cursor.execute("""
                INSERT INTO users (first_name, last_name, email, hashed_password)
                VALUES (?, ?, ?, ?)
            """, (first_name, last_name, email, hashed_password))
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            print(f"Error: Email '{email}' already exists.")
            return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        self.cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = self.cursor.fetchone()
        return User(dict(row)) if row else None

    def update_last_login(self, user_id: int):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, user_id))
        print(f"Updated last_login for user ID: {user_id}")

    def update_balance(self, user_id: int, new_balance: float):
        self.cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))
        print(f"Updated balance for user ID: {user_id} to £{new_balance:.2f}")

    def check_password(self, email: str, plain_text_password: str) -> bool:

        user = self.get_user_by_email(email)
        if user and user.hashed_password:
            return check_password_hash(user.hashed_password, plain_text_password)
        return False
    
    
    
    
    
    
    
class CommunityManager:    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.commit()
            self.conn.close()


    def create_community(self, name: str, fight_id: int, creator_user_id: int) -> Optional[int]:
        try:
            sql_create_community = """
                INSERT INTO communities (name, fight_id, created_by_user_id)
                VALUES (?, ?, ?)
            """
            self.cursor.execute(sql_create_community, (name, fight_id, creator_user_id))
            new_community_id = self.cursor.lastrowid

            sql_add_admin = """
                INSERT INTO community_members (community_id, user_id, role)
                VALUES (?, ?, 'admin')
            """
            self.cursor.execute(sql_add_admin, (new_community_id, creator_user_id))
            
            return new_community_id
        except sqlite3.IntegrityError as e:
            print(f"Error creating community: {e}")
            return None

    def join_community(self, community_id: int, user_id: int) -> bool:
        sql = """
            INSERT INTO community_members (community_id, user_id, role)
            VALUES (?, ?, 'user')
        """
        try:
            self.cursor.execute(sql, (community_id, user_id))
            return self.cursor.rowcount > 0  # True if a row was inserted
        except sqlite3.IntegrityError:
            print("User already in community or community does not exist.")
            return False

    def leave_community(self, community_id: int, user_id: int) -> bool:
        sql = """
            DELETE FROM community_members
            WHERE community_id = ? AND user_id = ?
        """
        self.cursor.execute(sql, (community_id, user_id))
        return self.cursor.rowcount > 0  # True if a row was deleted

    def place_bet(self, community_id: int, user_id: int, bet: int) -> bool:
        sql = """
            UPDATE community_members
            SET bet = ?
            WHERE community_id = ? AND user_id = ?
        """
        try:
            self.cursor.execute(sql, (bet, community_id, user_id))
            return self.cursor.rowcount > 0  # True if a row was updated
        except sqlite3.IntegrityError:
            print("Invalid bet value.")
            return False


    def get_community_details(self, community_id: int) -> Optional[dict]:
        sql = """
            SELECT 
                c.name, c.fight_id,
                u.first_name, u.last_name, 
                cm.role, cm.bet
            FROM communities c
            JOIN community_members cm ON c.id = cm.community_id
            JOIN users u ON cm.user_id = u.id
            WHERE c.id = ?
        """
        self.cursor.execute(sql, (community_id,))
        rows = self.cursor.fetchall()
        
        if not rows:
            return None
        
        details = {"name": rows[0]["name"], "fight_id": rows[0]["fight_id"], "members": []}
        for row in rows:
            details["members"].append({
                "name": f"{row['first_name']} {row['last_name']}",
                "role": row['role'],
                "bet": "Red" if row['bet'] == 0 else "Blue" if row['bet'] == 1 else "None"
            })
        return details
    
    def get_communities_by_fightID(self, fight_id: int) -> Optional[dict]:
        sql = """
            SELECT * FROM communities
            WHERE fight_id = ?
        """
        
        self.cursor.execute(sql, (fight_id,))
        rows = self.cursor.fetchall()
        
        if not rows:
            return None
        
        communities = []
        for row in rows:
            communities.append({
                "id": row["id"],
                "name": row["name"],
                "fight_id": row["fight_id"],
                "created_by_user_id": row["created_by_user_id"]
            })
        return communities
        