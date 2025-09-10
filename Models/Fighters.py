from typing import Optional

class Fighter:

    def __init__(self, fighter_data: dict):

        self.id: Optional[int] = fighter_data.get("id")
        self.name: Optional[str] = fighter_data.get("Name")
        self.nickname: Optional[str] = fighter_data.get("Nickname")
        self.height: Optional[str] = fighter_data.get("Height")
        self.weight: Optional[str] = fighter_data.get("Weight")
        self.reach: Optional[str] = fighter_data.get("Reach")
        self.stance: Optional[str] = fighter_data.get("Stance")
        self.record: Optional[str] = fighter_data.get("Record")
        self.dob: Optional[str] = fighter_data.get("DOB")
        self.profile_url: Optional[str] = fighter_data.get("profile_url")

        self.elo_rating: float = fighter_data.get("elo_rating", 1500.0)
        self.rating_deviation: float = fighter_data.get("rating_deviation", 350.0)
        self.rating_volatility: float = fighter_data.get("rating_volatility", 0.06)

    def to_tuple_for_insert(self) -> tuple:

        return (
            self.name,
            self.nickname,
            self.height,
            self.weight,
            self.reach,
            self.stance,
            self.record,
            self.dob,
            self.profile_url,
            self.elo_rating,
            self.rating_deviation,
            self.rating_volatility
        )

    def __repr__(self) -> str:
        """Provides a developer-friendly string representation of the object."""
        return f"<Fighter: {self.name} (ID: {self.id}, Elo: {round(self.elo_rating)})>"
