import pandas as pd
import numpy as np
import sys
import os
from tqdm import tqdm

from config.config import DB_PATH

from Database.database_manager import DatabaseManager
from Fight_Predictor.Fight_Context import Fight_Context

def create_main_features():
    #loading the fighters and past fights 
    with DatabaseManager(DB_PATH) as db:
        fights = pd.DataFrame(db.get_fights())
        fighters = db.get_fighters()
        
    # creates a map of fighters with their id as a ket for faster lookups 
    fighters_map = {f.id: f for f in fighters}

    feature_df = []

    try:
        iterator = tqdm(fights.iterrows(), total=len(fights))
    except ImportError:
        iterator = fights.iterrows()

    counter = 1

    for _ , fight_row in fights.iterrows():
        red_id = fight_row["red_fighter_id"]
        blue_id = fight_row["blue_fighter_id"]
        winner_id = fight_row["winner_id"]
        
        is_draw = False
        
        if pd.isna(red_id) or pd.isna(blue_id):
            continue
        
        if pd.isna(winner_id):
            continue
        
        red_fighter = fighters_map.get(red_id)
        blue_fighter = fighters_map.get(blue_id)
        
        if not red_fighter or not blue_fighter:
            print(f"Missing fighter data for fight {fight_row['fight_id']}")
            continue
        
        
        context = Fight_Context(red_fighter, blue_fighter, fight_row["event_date"], winner_id)
        final_features = context.create_features()
        
        feature_df.append(final_features)
        
        print(f"fight row number {counter} loaded")
        counter += 1


        
    feature_df = pd.DataFrame([ {k: np.squeeze(v) for k, v in f.items()} 
                            for f in feature_df ])
    
    CACHE_PATH = './data/final_feature_set.feather'
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    feature_df.to_feather(CACHE_PATH)

