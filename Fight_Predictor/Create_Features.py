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
    
    #counter for debugging purpsoes 
    counter = 1

    #loops through every fights and creates a fight context for it 
    for _ , fight_row in fights.iterrows():
        red_id = fight_row["red_fighter_id"]
        blue_id = fight_row["blue_fighter_id"]
        winner_id = fight_row["winner_id"]
                
        # if there is no winner or a draw then it will be skipped as the training data would be useless 
        if pd.isna(red_id) or pd.isna(blue_id):
            continue
        if pd.isna(winner_id):
            continue
        
        #gets the fighter info 
        red_fighter = fighters_map.get(red_id)
        blue_fighter = fighters_map.get(blue_id)
        
        if not red_fighter or not blue_fighter:
            print(f"Missing fighter data for fight {fight_row['fight_id']}")
            continue
        
        #instantiates the fight context class with the given data for the red and blue fighters to create final features
        context = Fight_Context(red_fighter, blue_fighter, fight_row["event_date"], winner_id)
        final_features = context.create_features()
        
        #appends this fights features in a row on the dataframe
        feature_df.append(final_features)
        
        #due to the extremely long execution time I use this to show that the function is wokring 
        print(f"fight row number {counter} loaded")
        counter += 1


        
    feature_df = pd.DataFrame([ {k: np.squeeze(v) for k, v in f.items()} 
                            for f in feature_df ])
    
    # stores the data for the final uses 
    CACHE_PATH = './data/final_feature_set.feather'
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    feature_df.to_feather(CACHE_PATH)

