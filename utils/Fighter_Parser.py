from math import e
import pandas as pd
import numpy as np
import datetime

from Models.DB_Classes.Fighters import Fighter

def parse_record(record_str: str) -> tuple[int, int , int]:
    if not record_str or not record_str.startswith('Record'):
        print("there was no record string")
        return 0, 0, 0

    try:
        parts = record_str.replace('Record:', "").strip().split('-')
        wins = int(parts[0])
        losses = int(parts[1])
        
        draws = parts[2].split(" ")
        
        drws = int(draws[0])
        return wins, losses, drws
    except:
        print('could not parse record string')
        return 0, 0, 0

def parse_height_to_cm(height_str: str) -> float:
    try:
        feet, inches = height_str.replace('"', '').split("'")
        return (int(feet) * 30.48) + (int(inches) * 2.54)
    except:
        return 0

def parse_reach_to_cm(reach_str: str) -> float:
    if not reach_str or reach_str == '--':
        return None
    try:
        return float(reach_str.replace('"', '')) * 2.54
    except ValueError:
        return None

def calc_age(dob: str, event_date: datetime.date) -> float:
    if not dob or dob == '--':
        return None
    try:
        dob = pd.to_datetime(dob).date()
        return (event_date - dob).days / 365.25
    except (ValueError, TypeError):
        return None

def calc_gausian_age_prime(age):
    
    if age is None:
        return 0.5

    prime_age = 30.0
    standard_deviation = 4

    score = np.exp(-((age - prime_age)**2) / (2 * standard_deviation**2))
    return score

def calc_record_stats(red_fighter: Fighter, blue_fighter: Fighter):
    wins_red, losses_red, draws_red = parse_record(red_fighter.record)
    wins_blue, losses_blue, draws_blue = parse_record(blue_fighter.record)
    
    red_total = wins_red + losses_red + draws_red
    blue_total = wins_blue + losses_blue + draws_blue
    experiance_diff = red_total - blue_total
    
    
    red_win_percent = wins_red / red_total if red_total > 0 else 0
    blue_win_percent = wins_blue / blue_total if blue_total > 0 else 0
    win_prop_diff = (red_win_percent - blue_win_percent)
    
    red_loss_percent = losses_red / red_total if red_total > 0 else 0
    blue_loss_percent = losses_blue / blue_total if blue_total > 0 else 0
    loss_prop_diff = (red_loss_percent - blue_loss_percent)
    
    return experiance_diff, win_prop_diff, loss_prop_diff



def create_fight_features(red_fighter: Fighter, blue_fighter: Fighter, event_date) -> pd.DataFrame:

    fight_date = pd.to_datetime(event_date).date() if event_date else datetime.date.today()

    height_red_cm = parse_height_to_cm(red_fighter.height)
    height_blue_cm = parse_height_to_cm(blue_fighter.height)
    height_diff = height_red_cm - height_blue_cm if height_red_cm and height_blue_cm else 0

    reach_red_cm = parse_reach_to_cm(red_fighter.reach)
    reach_blue_cm = parse_reach_to_cm(blue_fighter.reach)
    reach_diff = reach_red_cm - reach_blue_cm if reach_red_cm and reach_blue_cm else 0

    age_red = calc_age(red_fighter.dob, fight_date)
    age_blue = calc_age(blue_fighter.dob, fight_date)
    age_diff = age_red - age_blue if age_red and age_blue else 0

    prime_score_red = calc_gausian_age_prime(age_red)
    prime_score_blue = calc_gausian_age_prime(age_blue)
    prime_score_diff = prime_score_red - prime_score_blue

    experiance_diff, win_prop_diff, loss_prop_diff = calc_record_stats(red_fighter, blue_fighter)

    feature_dict = {
        "experiance_diff": experiance_diff,
        "win_proportion_diff": win_prop_diff,
        "loss_proportion_diff": loss_prop_diff,
        'height_diff_cm': height_diff,
        'reach_diff_cm': reach_diff,
        'age_diff': age_diff,
        'prime_score_diff': prime_score_diff,
    }

    return pd.DataFrame(feature_dict, index=[0]) 

