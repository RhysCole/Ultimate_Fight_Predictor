from fastapi import APIRouter, HTTPException, status
from typing import List
import joblib
import json

from Fight_Predictor.Fight_Context import Fight_Context
from config.config import DB_PATH, PREDICTOR_MODEL_PATH
from Database.database_manager import DatabaseManager
from API.routes.fights.schema import UpcomingFight, PastFight
from Models.DB_Classes.Fighters import Fighter


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
        
@fights_router.get("/recent", response_model=List[PastFight])
def recent_fights(count):
    with DatabaseManager(DB_PATH) as db:
        recent_fights = db.get_recent_fights(count)
        
    if not recent_fights:
        return []
    return recent_fights

@fights_router.get("/pre_fight_data")
def prediction_data(red_fighter_id, blue_fighter_id, event_date):
    with DatabaseManager(DB_PATH) as db:
        red_fighter = db.get_fighter_by_id(red_fighter_id)
        blue_fighter = db.get_fighter_by_id(blue_fighter_id)

    context = Fight_Context(red_fighter, blue_fighter, event_date, winner_id = None)
    
    readable_features = context.create_readable_features()
    features_dict = readable_features.to_dict(orient="records")[0]
    
    prediction_features = context.create_features()
    
    bushy_model = joblib.load(PREDICTOR_MODEL_PATH)
    prediction = bushy_model.predict(prediction_features.values)
    
    return {"features": features_dict,
            "prediction": float(prediction[0]),
            "red_fighter": red_fighter,
            "blue_fighter": blue_fighter
        }

@fights_router.get("/id")
def get_fight_by_id(fight_id: int, completed: bool = True):
    with DatabaseManager(DB_PATH) as db:
        if completed:
            fight = db.get_fight_by_id(fight_id)
        else:
            fight = db.get_upcoming_by_id(fight_id)
        
    return fight


@fights_router.get("/fight_by_fighter")
def get_fight_by_fighter(fighter_id: int):
    with DatabaseManager(DB_PATH) as db:
        past_fights = db.get_fight_by_fighter_id(fighter_id)
        upcoming_fights = db.get_upcoming_by_fighter_id(fighter_id)
        
    return {
        "past": past_fights,
        "upcoming": upcoming_fights
    }
@fights_router.post("/vote")
def vote(fight_id: int, user_id: int, vote: int):
    with DatabaseManager(DB_PATH) as db:
        db.vote(fight_id, user_id, vote)
        db.update_upcoming_vote_totals()
        
@fights_router.get("/vote_check")
def vote_count(fight_id: int, user_id: int):
    with DatabaseManager(DB_PATH) as db:
        vote_data = db.check_vote(user_id, fight_id)
        
    return vote_data

@fights_router.get("/history")
def get_fight_history(fighter_id):
    with DatabaseManager(DB_PATH) as db:
        history = db.get_past_fights(fighter_id)
        
    return history        

@fights_router.get("/rivalry")
def get_fight_rivalry():
    with DatabaseManager(DB_PATH) as db:
        rivalry = db.get_active_rivalries()
        
    return rivalry

@fights_router.get("/RFights")
def get_RFights(red_fighter_id, blue_fighter_id):
    with DatabaseManager(DB_PATH) as db:
        RFights = db.get_rivalry_fights(red_fighter_id, blue_fighter_id)
        
    return RFights

@fights_router.get("/RDominance")
def get_rivalry_dominance_score(red_fighter_id, blue_fighter_id, ):
    with DatabaseManager(DB_PATH) as db:
        red_fighter = db.get_fighter_by_id(red_fighter_id)
        blue_fighter = db.get_fighter_by_id(blue_fighter_id)

    context = Fight_Context(red_fighter, blue_fighter, event_date = "2025-12-12", winner_id = None)
    return context.get_rivalry_dominance()

