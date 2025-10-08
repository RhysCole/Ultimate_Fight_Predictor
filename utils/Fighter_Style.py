from typing import List

import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys

from config.config import DB_PATH

notebook_dir = os.getcwd()
project_root = os.path.abspath(os.path.join(notebook_dir, '..'))
sys.path.append(project_root)

from Database.database_manager import DatabaseManager

def define_style(fighter_id):
    with DatabaseManager(DB_PATH) as db:
        fighter_history = db.get_fighter_history([fighter_id], datetime.now())
        fighter = db.get_fighter_by_id(fighter_id)

    if fighter_history.empty or len(fighter_history) < 2:
        return {
            "fighter_id": fighter.id,
            "primary_style": 'Newcomer',
            "secondary_style": 'Newcomer',
            "tertiary_attributes": 'Newcomer'
        }

    num_fights = len(fighter_history)

    total_takedowns_landed = 0
    total_sub_attempts = 0
    total_sig_strikes_landed = 0
    total_knockdowns_scored = 0
    total_wins = 0
    total_finishes = 0
    total_fight_time_seconds = 0

    for _, fight in fighter_history.iterrows():
        is_red = fight['red_fighter_id'] == fighter_id

        total_takedowns_landed += fight['red_takedowns'] if is_red else fight['blue_takedowns']
        total_sub_attempts += fight['red_sub_attempts'] if is_red else fight['blue_sub_attempts']
        total_sig_strikes_landed += fight['red_sig_strikes'] if is_red else fight['blue_sig_strikes']
        total_knockdowns_scored += fight['red_knockdowns'] if is_red else fight['blue_knockdowns']

        total_fight_time_seconds += fight['final_time_seconds'] + (fight['final_round'] - 1) * 300

        if fight['winner_id'] == fighter_id:
            total_wins += 1
            if 'KO' in fight['win_method'] or 'SUB' in fight['win_method']:
                total_finishes += 1

    avg_takedowns = total_takedowns_landed / num_fights
    avg_subs = total_sub_attempts / num_fights
    grappling_tendency = (avg_takedowns * 2.0) + (avg_subs * 1.0)

    if grappling_tendency >= 3.5:
        primary_style = "Power Grappler"
    elif grappling_tendency >= 1.5:
        primary_style = "Wrestle-Boxer"
    elif grappling_tendency > 0.5:
        primary_style = "Striker"
    else:
        primary_style = "Pure Striker"


    total_minutes = total_fight_time_seconds / 60
    slpm = total_sig_strikes_landed / total_minutes if total_minutes > 0 else 0

    finish_rate = total_finishes / total_wins if total_wins > 0 else 0

    if slpm > 4.5:
        pacing = "Pressure"
    elif slpm > 2.5:
        pacing = "Paced"
    else:
        pacing = "Counter"

    if finish_rate > 0.7:
        intent = "Finisher"
    elif total_knockdowns_scored / num_fights > 0.5:
        intent = "Power Puncher"
    else:
        intent = "Decision Fighter"

    if primary_style in ["Power Grappler", "Wrestle-Boxer"]:
        secondary_style = f"Grinding {intent}"
    else:
        secondary_style = f"{pacing} {intent}"

    try:
        height_val = float(fighter.height.replace('"', '')) * 2 if fighter.height and fighter.height != '--' else 0
        reach_val = float(fighter.reach.replace('"', '')) * 2 if fighter.reach and fighter.reach != '--' else 0
        ape_index = reach_val - height_val if height_val and reach_val else 0

        if ape_index > 8:
            frame = "Long-Limbed"
        elif ape_index < -5:
            frame = "Compact"
        else:
            frame = "Conventional Frame"
    except:
        frame = "Conventional Frame"

    stance = fighter.stance if fighter.stance and fighter.stance != '--' else "Orthodox"
    tertiary_attributes = f"{frame} ({stance})"

    return {
        "fighter_id": fighter_id,
        "primary_style": primary_style,
        "secondary_style": secondary_style,
        "tertiary_attributes": tertiary_attributes
    }

def get_all_fighter_styles(fighter_ids: pd.DataFrame) -> List[dict]:
    figher_ids_list = fighter_ids['id'].tolist()

    style_results = []
    for fighter_id in figher_ids_list:
        style_object = define_style(fighter_id)
        style_results.append(style_object)

    return style_results

