import pandas as pd
import numpy as np
import datetime

import pandas as pd
import datetime


def safe_to_datetime(date_str, format):

    if not date_str or date_str == '--':
        return pd.NaT

    try:
        return pd.to_datetime(date_str, format=format)
    except (ValueError, TypeError):
        return pd.NaT

def ranking_model(glicko_players: dict, all_fighters: list, all_fights_df: pd.DataFrame):

    WEIGHT_ACTIVITY = 35
    WEIGHT_SOS = 0.5
    WEIGHT_AGE = 0.1
    Z_SCORE = 2.0

    fighter_name_map = {f.id: f.name for f in all_fighters}
    fighter_dob_map = {f.id: safe_to_datetime(f.dob, '%b %d, %Y') for f in all_fighters}

    ranking_data = []
    today = datetime.date.today()

    for fighter_id, player in glicko_players.items():
        if fighter_id not in fighter_name_map: continue

        skill_component = player.rating - (Z_SCORE * player.rating_deviation)

        fighter_fights = all_fights_df[
            (all_fights_df['red_fighter_id'] == fighter_id) |
            (all_fights_df['blue_fighter_id'] == fighter_id)
            ]

        if fighter_fights.empty: continue

        last_fight_date = pd.to_datetime(fighter_fights['event_date']).max().date()
        days_since_last_fight = (today - last_fight_date).days
        activity_penalty = -np.log((days_since_last_fight / 180) + 1) * WEIGHT_ACTIVITY

        recent_fights = fighter_fights.tail(5)
        opponent_elos = []
        for _, fight in recent_fights.iterrows():
            if fight['red_fighter_id'] == fighter_id:
                opponent_elos.append(fight['blue_elo'])
            else:
                opponent_elos.append(fight['red_elo'])

        avg_opponent_rating = np.mean(opponent_elos)
        sos_bonus = (avg_opponent_rating - 1500) * WEIGHT_SOS

        age = (pd.to_datetime(today) - fighter_dob_map.get(fighter_id, pd.to_datetime(today))).days / 365.25
        age_penalty = -((age - 30) ** 2) * WEIGHT_AGE if age > 30 or age < 24 else 0

        advanced_quality_score = skill_component + activity_penalty + sos_bonus + age_penalty

        ranking_data.append({
            'id': fighter_id,
            'Name': fighter_name_map[fighter_id],
            'Rating': player.rating,
            'RD': player.rating_deviation,
            'Quality Score': advanced_quality_score
        })

    if not ranking_data: return

    rankings_df = pd.DataFrame(ranking_data)
    final_rankings = rankings_df.sort_values(by='Quality Score', ascending=False)

    final_rankings.insert(0, '#', range(1, 1 + len(final_rankings)))
    return final_rankings
