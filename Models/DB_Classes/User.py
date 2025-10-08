from typing import Optional

class User:
    def __init__(self, user_data: dict):

        self.id: Optional[int] = user_data.get("id")
        self.first_name: Optional[str] = user_data.get("first_name")
        self.last_name: Optional[str] = user_data.get("last_name")
        self.email: Optional[str] = user_data.get("email")
        self.hashed_password: Optional[str] = user_data.get("hashed_password")
        self.balance: float = user_data.get("balance", 1000.00)
        self.created_at: Optional[str] = user_data.get("created_at")
        self.last_login: Optional[str] = user_data.get("last_login")
        self.role: Optional[str] = user_data.get("role")

    def __repr__(self) -> str:
        return f"<User: {self.first_name} {self.last_name} (ID: {self.id}) (role: {self.role})>"