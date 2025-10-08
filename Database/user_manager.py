import sqlite3
import pandas as pd
from typing import Optional, List

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