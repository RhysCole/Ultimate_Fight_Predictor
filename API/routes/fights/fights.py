from fastapi import APIRouter, HTTPException, status
from typing import List

from config.config import DB_PATH
from Database.database_manager import DatabaseManager
from API.routes.fights.schema import UpcomingFight

fights_router = APIRouter(
    prefix="/fights",
    tags=["Fights"]
)

@fights_router.get("/upcoming", response_model=List[UpcomingFight])
def get_upcoming_fights_route():
    try:
        with DatabaseManager(DB_PATH) as db:
            upcoming_fights = db.get_upcoming_fights()
        
        if not upcoming_fights:
            return [] 
        
        
        
        return upcoming_fights
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching fights: {e}"
        )
