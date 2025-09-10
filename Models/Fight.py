from typing import Optional

class Fight:

    def __init__(self, fight_data: dict):

        self.fight_id: Optional[int]
        self.red_fighter_id: Optional[int]
        self.blue_fighter_id: Optional[int]
        self.winner_id: Optional[int]
        
        self.red_knockdowns: int = fight_data.get("red_knockdowns", 0)
        self.blue_knockdowns: int = fight_data.get("blue_knockdowns", 0)
        self.red_sig_strikes: int = fight_data.get("red_sig_strikes", 0)
        self.blue_sig_strikes: int = fight_data.get("blue_sig_strikes", 0)
        self.red_takedowns: int = fight_data.get("red_takedowns", 0)
        self.blue_takedowns: int = fight_data.get("blue_takedowns", 0)
        self.red_sub_attempts: int = fight_data.get("red_sub_attempts", 0)
        self.blue_sub_attempts: int = fight_data.get("blue_sub_attempts", 0)
        
        self.win_method: Optional[str] = fight_data.get("win_method")
        self.final_round: Optional[int] = fight_data.get("final_round")
        self.final_time_seconds: Optional[int] = fight_data.get("final_time_seconds")
        self.event_date: Optional[str] = fight_data.get("event_date")
        self.event_url: Optional[str] = fight_data.get("event_url")
        self.is_completed: bool = fight_data.get("is_completed", False)

        self.red_elo: int = fight_data.get("red_elo", 1500)
        self.blue_elo: int = fight_data.get("blue_elo", 1500)

    def to_tuple_for_insert(self) -> tuple:
        return (
            self.fight_id,
            self.red_fighter_id,
            self.blue_fighter_id,
            self.winner_id,
            self.red_knockdowns,
            self.blue_knockdowns,
            self.red_sig_strikes,
            self.blue_sig_strikes,
            self.red_takedowns,
            self.blue_takedowns,
            self.red_sub_attempts,
            self.blue_sub_attempts,
            self.win_method,
            self.final_round,
            self.final_time_seconds,
            self.event_date,
            self.event_url,
            self.is_completed,
            self.red_elo,
            self.blue_elo
        )

    def __repr__(self) -> str:
        return f"<Fight: {self.red_fighter_id} vs. {self.blue_fighter_id}>"