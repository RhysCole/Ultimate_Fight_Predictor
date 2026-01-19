import pandas as pd
import numpy as np
import joblib

# Import the file path for the saved LabelEncoder or OneHotEncoder
from config.config import DOMINANCE_ENCODER_PATH

# Define a function to calculate performance gaps between the winner and the loser
def create_features(df: pd.DataFrame) -> pd.DataFrame:
    # Identify if the red fighter won to help decide how to subtract the stats
    winner_is_red = df['winner_id'] == df['red_fighter_id']
    features = pd.DataFrame(index=df.index)

    # Calculate strike gaps: positive means the winner landed more than the loser
    features['sig_strike_differential'] = np.where(
        winner_is_red,
        df['red_sig_strikes'] - df['blue_sig_strikes'],
        df['blue_sig_strikes'] - df['red_sig_strikes']
    )

    # Calculate takedown gaps based on which fighter actually took the win
    features['takedown_differential'] = np.where(
        winner_is_red,
        df['red_takedowns'] - df['blue_takedowns'],
        df['blue_takedowns'] - df['red_takedowns']
    )

    # Calculate knockdown gaps to show how much the winner dropped the loser
    features['knockdown_differential'] = np.where(
        winner_is_red,
        df['red_knockdowns'] - df['blue_knockdowns'],
        df['blue_knockdowns'] - df['red_knockdowns']
    )

    # Calculate submission attempt gaps to measure ground control dominance
    features['sub_differential'] = np.where(
        winner_is_red,
        df['red_sub_attempts'] - df['blue_sub_attempts'],
        df['blue_sub_attempts'] - df['red_sub_attempts']
    )

    # Sum up the total activity in the fight to gauge the overall pace
    features['total_sig_strikes'] = df['red_sig_strikes'] + df['blue_sig_strikes']
    features['total_takedowns'] = df['red_takedowns'] + df['blue_takedowns']
    features['total_knockdowns'] = df['red_knockdowns'] + df['blue_knockdowns']
    features['total_submissions'] = df['red_sub_attempts'] + df['blue_sub_attempts']

    # Keep track of when the fight ended to help the model weight the stats
    features['final_round'] = df['final_round']
    features['final_time_seconds'] = df['final_time_seconds']

    return features

# The main function to process raw fight data into a format for the AI model
def prep_features(df: pd.DataFrame) -> pd.DataFrame:
    # First, generate all the numerical gap and total stats
    features = create_features(df)

    # Clean up the win_method text by taking only the name and not the web formatted version the multipul /n s 
    df['win_method_clean'] = df['win_method'].str.split('\n').str[0]

    # Load the encoder to turn text categories into numbers the AI understands
    encoder = joblib.load(DOMINANCE_ENCODER_PATH)
    encoded_df = encoder.transform(df['win_method_clean'])
    
    # Combine the  stats and the encoded win method into one  dataset
    final_features = pd.concat([features, encoded_df], axis=1)
    return final_features