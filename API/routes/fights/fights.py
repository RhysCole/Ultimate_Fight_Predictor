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

