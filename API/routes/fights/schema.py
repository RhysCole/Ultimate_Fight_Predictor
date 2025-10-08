from pydantic import BaseModel
from typing import Optional

class UpcomingFight(BaseModel):
    id: int
    event_date: str
    red_fighter_id: int
    blue_fighter_id: int
    red_fighter_name: str
    blue_fighter_name: str