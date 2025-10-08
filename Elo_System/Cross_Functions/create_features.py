import pandas as pd
import numpy as np
import joblib

from config.config import DOMINANCE_ENCODER_PATH

def create_features(df: pd.DataFrame) -> pd.DataFrame:
    winner_is_red = df['winner_id'] == df['red_fighter_id']
    features = pd.DataFrame(index=df.index)

    features['sig_strike_differential'] = np.where(
        winner_is_red,
        df['red_sig_strikes'] - df['blue_sig_strikes'],
        df['blue_sig_strikes'] - df['red_sig_strikes']
    )

    features['takedown_differential'] = np.where(
        winner_is_red,
        df['red_takedowns'] - df['blue_takedowns'],
        df['blue_takedowns'] - df['red_takedowns']
    )

    features['knockdown_differential'] = np.where(
        winner_is_red,
        df['red_knockdowns'] - df['blue_knockdowns'],
        df['blue_knockdowns'] - df['red_knockdowns']
    )

    features['sub_differential'] = np.where(
        winner_is_red,
        df['red_sub_attempts'] - df['blue_sub_attempts'],
        df['blue_sub_attempts'] - df['red_sub_attempts']
    )

    features['total_sig_strikes'] = df['red_sig_strikes'] + df['blue_sig_strikes']
    features['total_takedowns'] = df['red_takedowns'] + df['blue_takedowns']
    features['total_knockdowns'] = df['red_knockdowns'] + df['blue_knockdowns']
    features['total_submissions'] = df['red_sub_attempts'] + df['blue_sub_attempts']

    features['final_round'] = df['final_round']
    features['final_time_seconds'] = df['final_time_seconds']

    return features

def prep_features(df: pd.DataFrame) -> pd.DataFrame:
    features = create_features(df)

    df['win_method_clean'] = df['win_method'].str.split('\n').str[0]

    encoder = joblib.load(DOMINANCE_ENCODER_PATH)
    encoded_df = encoder.transform(df['win_method_clean'])
    final_features = pd.concat([features, encoded_df], axis=1)
    return final_features

