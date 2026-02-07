import pandas as pd
import joblib

from Elo_System.Cross_Functions.create_features import prep_features
from config.config import DOMINANCE_MODEL_PATH


#get a dominance prediction for a list of fights 
def dominance_prediction(fights):
    #loading dominance model
    performance_modal = joblib.load(DOMINANCE_MODEL_PATH)

    #preparing features
    features = prep_features(fights)
    
    #predicting
    dominance_scores = performance_modal.predict(features)
    dominance_scores = pd.DataFrame(dominance_scores)

    return dominance_scores