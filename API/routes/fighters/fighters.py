from fastapi import APIRouter, HTTPException, status
from typing import List

import Database
from config.config import DB_PATH
from Database.database_manager import DatabaseManager
from config.config import DB_PATH

fighter_router = APIRouter(
    prefix= "/fighters",
    tags=["Fighters"]
)

@fighter_router.get("/all")
def get_all_fighters():
    with DatabaseManager(DB_PATH) as db:
        all_fighters = db.get_all_fighters()
        
    return all_fighters

@fighter_router.get("/info")
def get_fighter_info(fighter_id: int):
    with DatabaseManager(DB_PATH) as db:
        fighter_stats = db.get_fighter_by_id(fighter_id)
        upcoming_fights = db.get_fighter_upcomings(fighter_id)
        
    return {
        "stats": fighter_stats,
        "upcoming": upcoming_fights
    }
    
@fighter_router.get('/rank')
def get_fighter_rank(fighter_id: int):
    with DatabaseManager(DB_PATH) as db:
        rank = db.get_fighter_rank(fighter_id)
        
    return rank

@fighter_router.get('/top')
def get_top_fighters(count: int, option: int):
    with DatabaseManager(DB_PATH) as db:
        top_fighters = db.get_top_fighters(count, option)
        
    return top_fighters
    
    
        