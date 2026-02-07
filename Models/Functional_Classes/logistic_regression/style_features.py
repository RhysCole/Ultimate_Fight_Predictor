import pandas as pd
import joblib

from config.config import DB_PATH, ENCODERS_PATH
from utils.Fighter_Style import define_style
from Database.database_manager import DatabaseManager

def get_all_fighter_styles(fighter_id):
    # Wrapper to fetch full style object for a single fighter
    style_object = define_style(fighter_id)
    return style_object

def prep_style_features(fighter_ids) -> pd.DataFrame:
    # Extract individual ids from input list
    fighter_1_id = fighter_ids[0]
    fighter_2_id = fighter_ids[1]

    with DatabaseManager(DB_PATH) as db:
        #  fetch style data for both fighters from DB
        styles_map = db.get_fighter_styles([fighter_1_id, fighter_2_id])

    fighter_1_style = styles_map.get(fighter_1_id, {})
    fighter_2_style = styles_map.get(fighter_2_id, {})

    # Structure raw  data into a dictionary for a DataFrame 
    model_data = {
        'primary_1': fighter_1_style['primary_style'],
        'secondary_1': fighter_1_style['secondary_style'],
        'tertiary_1': fighter_1_style['tertiary_attributes'],

        'primary_2': fighter_2_style['primary_style'],
        'secondary_2': fighter_2_style['secondary_style'],
        'tertiary_2': fighter_2_style['tertiary_attributes'],
    }
    model_data = pd.DataFrame([model_data])

    # Load the saved dictionary of pre-fitted encoders
    fitted_encoders = joblib.load(ENCODERS_PATH)

    encoded_parts = []

    style_groups = {
        'primary': ['primary_1', 'primary_2'],
        'secondary': ['secondary_1', 'secondary_2'],
        'tertiary': ['tertiary_1', 'tertiary_2']
    }

    for group_name, cols in style_groups.items():
        # Select the correct encoder for the current style level
        encoder = fitted_encoders[group_name]
        for col in cols:
            # Transform column and add prefix to keep features distinct
            encoded_part = encoder.transform(model_data[col], prefix=col)
            encoded_parts.append(encoded_part)

    # Combine all one-hot encoded features into one DataFrame
    features_raw = pd.concat(encoded_parts, axis=1)

    return features_raw