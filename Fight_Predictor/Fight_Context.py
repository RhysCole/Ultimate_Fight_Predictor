from difflib import context_diff
from multiprocessing import context
from matplotlib import style
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import random

from Models.DB_Classes.Fighters import Fighter
from Database.database_manager import DatabaseManager
from Models.Functional_Classes.logistic_regression import style_features
from utils.dominance_prediction import dominance_prediction
from Models.Functional_Classes.logistic_regression.style_features import prep_style_features
from config.config import MODEL_PATH, DB_PATH
from utils.Fighter_Parser import create_fight_features


class Fight_Context:
    def __init__(self, red_fighter: Fighter, blue_fighter: Fighter, event_date: str, winner_id = None):
        fighters = [
            red_fighter,
            blue_fighter
        ]

        random.shuffle(fighters)
        
        self.red_fighter = fighters[0]
        self.blue_fighter = fighters[1]
        
        self.winner_id = winner_id if winner_id is not None else None
        
        self.event_date = event_date

        self.fights = None

        self.elo_diff = red_fighter.elo_rating - blue_fighter.elo_rating
        self.quality_score_diff = red_fighter.quality_score - blue_fighter.quality_score

        self.form_diff = None
        self.average_rivalry_dominance = None

        self.style_features = None

        self.red_style_performance = None
        self.blue_style_performance = None
        self.style_diff = None
        
        self.red_activity_score = None
        self.blue_activity_score = None
        self.activity_diff = None
        
        self.red_finish_score = None
        self.blue_finish_score = None
        self.finish_diff = None

    def get_past_fights(self):
        with DatabaseManager(DB_PATH) as db:
            fights_df = db.get_fighter_history([self.red_fighter.id, self.blue_fighter.id], self.event_date)

        self.fights = fights_df

    def calc_form(self, fighter_id: int):
        fighter_history = self.fights[
            (self.fights['red_fighter_id'] == fighter_id) |
            (self.fights['red_fighter_id'] == fighter_id)
        ].tail(10)

        if len(fighter_history) < 2:
            return 0.0

        fighter_elo_history = np.where(
            fighter_history['red_fighter_id'] == fighter_id,
            fighter_history['red_fighter_elo_before'],
            fighter_history['blue_fighter_elo_before'],
        )

        x_axis = np.arange(len(fighter_elo_history))

        try:
            slope, _ = np.polyfit(x_axis, fighter_elo_history, 1)
        except(np.linalg.LinAlgError, TypeError):
            slope = 0.0

        return slope

    def calc_form_diff(self):
        red_form = self.calc_form(self.red_fighter.id)
        blue_form = self.calc_form(self.blue_fighter.id)

        self.form_diff = red_form - blue_form

    def calc_weighted_rivalry_dominance(self):
        rivalry_fights = self.fights[
            (
                ((self.fights['red_fighter_id'] == self.red_fighter.id) & 
                 (self.fights['blue_fighter_id'] == self.blue_fighter.id)) |
                ((self.fights['red_fighter_id'] == self.blue_fighter.id) & 
                 (self.fights['blue_fighter_id'] == self.red_fighter.id))
            ) &
            (pd.to_datetime(self.fights['event_date']) < self.event_date)
        ].copy()
        if rivalry_fights.empty:
            self.average_rivalry_dominance = 0.0
            return

        dominance_scores_df = dominance_prediction(rivalry_fights)

        adjusted_scores = []
        for i, fight_row in enumerate(rivalry_fights.itertuples()):
            base_dominance = dominance_scores_df.iloc[i, 0]

            if fight_row.winner_id == self.red_fighter.id:
                adjusted_scores.append(base_dominance)
            elif fight_row.winner_id == self.blue_fighter.id:
                adjusted_scores.append(-base_dominance)
            else:
                adjusted_scores.append(0.0)

        num_fights = len(adjusted_scores)
        weights = np.linspace(1.0, 1.5, num=num_fights) if num_fights > 1 else [1.0]

        try:
            weighted_average = np.average(adjusted_scores, weights=weights)
        except ZeroDivisionError:
            weighted_average = 0.0

        self.average_rivalry_dominance = weighted_average

    def calc_style_performance(self):
        ids = [self.red_fighter.id, self.blue_fighter.id]

        features = prep_style_features(ids)

        style_model = joblib.load(MODEL_PATH)

        results_red_proba = style_model.predict_proba(features)

        self.red_style_performance = results_red_proba
        self.blue_style_performance = 1 - results_red_proba
        
        self.style_diff = self.red_style_performance[0] - self.blue_style_performance[0]
        
    def get_style_profiles(self):
        ids = [self.red_fighter.id, self.blue_fighter.id]

        features = prep_style_features(ids)
        
        self.style_features = features
        
    def calc_fighter_activity(self, fighter_id: int) -> float:
        fighter_history = self.fights[
            ((self.fights['red_fighter_id'] == fighter_id) |
            (self.fights['blue_fighter_id'] == fighter_id)) &
            (pd.to_datetime(self.fights['event_date']) < self.event_date)
        ].tail(6)

        if len(fighter_history) < 2:
            return 0.5 

        fight_dates = pd.to_datetime(fighter_history['event_date'])
        layoffs_in_days = fight_dates.diff().dt.days.dropna().values
        
        TIME_CONSTANT = 365.0 
        
        activity_scores = np.exp(-layoffs_in_days / TIME_CONSTANT)

        final_score = np.mean(activity_scores)
        
        return final_score
    
    def set_activity(self):
        red_fighter_activity = self.calc_fighter_activity(self.red_fighter.id)
        blue_fighter_activity = self.calc_fighter_activity(self.blue_fighter.id)
        
        self.red_activity_score = red_fighter_activity
        self.blue_activity_score = blue_fighter_activity
        self.activity_diff = red_fighter_activity - blue_fighter_activity
        
    def plot_activity(self):
        plt.style.use("seaborn-v0_8-darkgrid")
        fig, ax = plt.subplots(figsize=(10, 6))
        
        red_slope = self.red_activity_score['slope']
        red_intercept = self.red_activity_score['intercept']
        
        blue_slope = self.blue_activity_score['slope']
        blue_intercept = self.blue_activity_score['intercept']
        
        red_name = self.red_fighter.name
        blue_name = self.blue_fighter.name
        
        x_axis = np.linspace(0, 1460, 100)

        red_trend_line = red_slope * x_axis + red_intercept
        blue_trend_line = blue_slope * x_axis + blue_intercept

        ax.plot(x_axis, red_trend_line, color='red', linewidth=3, 
                label=f"{red_name} Trend (Slope: {red_slope:.2f})")
                
        ax.plot(x_axis, blue_trend_line, color='blue', linewidth=3, 
                label=f"{blue_name} Trend (Slope: {blue_slope:.2f})")    
    
        ax.set_title(f"Fighter Activity Rhythm: {self.red_fighter.name} vs. {self.blue_fighter.name}", fontsize=16, fontweight='bold')
        ax.set_xlabel("Career Timeline (Days from first fight in series)", fontsize=12)
        ax.set_ylabel("Layoff Period (Days)", fontsize=12)
        ax.legend(fontsize=11)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.show()
        
    def calc_finishing_power(self, fighter_id):
        fighter_history = self.fights[
            ((self.fights['red_fighter_id'] == fighter_id) |
            (self.fights['blue_fighter_id'] == fighter_id))
        ]

        if fighter_history.empty:
            return 0.0

        wins = fighter_history[fighter_history['winner_id'] == fighter_id]
        finishes_df = wins[
            wins['win_method'].str.contains('KO|SUB', na=False)
        ]

        if finishes_df.empty:
            return 0.0

        finishing_score = finishes_df['final_round'].apply(lambda r: 1 / r).sum()
        
        total_fights = len(fighter_history)
        normalized_score = finishing_score / total_fights
        
        return normalized_score
    
    def set_finish_power(self):
        red_finish_power = self.calc_finishing_power(self.red_fighter.id)
        blue_finish_power = self.calc_finishing_power(self.blue_fighter.id)
                
        self.red_finish_score = red_finish_power
        self.blue_finish_score = blue_finish_power
        self.finish_diff = red_finish_power - blue_finish_power
        
    def calc_defensive_rating(self, fighter_id):
        fighter_history =self.fights[
            ((self.fights['red_fighter_id'] == fighter_id) |
            (self.fights['blue_fighter_id'] == fighter_id))
        ]
        
        if fighter_history.empty:
            return {"strikes_absorbed_per_min": 4.0, "takedowns_absorbed_per_min": 4.0}
        
        total_strikes_absorbed = 0
        total_takedowns_absorbed = 0
        total_fight_time = 0
        
        fighter_history = pd.DataFrame(fighter_history)
        
        for _ , fight in fighter_history.iterrows():
            if fight['red_fighter_id'] == fighter_id:
                total_strikes_absorbed += fight.get('blue_sig_strikes', 0)
                total_takedowns_absorbed += fight.get('blue_takedowns', 0)
            else:
                total_strikes_absorbed += fight.get('red_sig_strikes', 0)
                total_takedowns_absorbed += fight.get('red_takedowns', 0)
                
            total_fight_time += fight['final_time_seconds'] / 60
            
        strikes_per_min = total_strikes_absorbed / total_fight_time
        takedowns_per_min = total_takedowns_absorbed / total_fight_time
        
        return {"strikes_absorbed_per_min": strikes_per_min, "takedowns_absorbed_per_min": takedowns_per_min}
    


    def get_defence_diff(self):
        red_defense_profile = self.calc_defensive_rating(self.red_fighter.id)
        blue_defense_profile = self.calc_defensive_rating(self.blue_fighter.id)
        
        self.strikes_absorbed_diff = red_defense_profile["strikes_absorbed_per_min"] - blue_defense_profile["strikes_absorbed_per_min"]
        self.takedowns_absorbed_diff = red_defense_profile["takedowns_absorbed_per_min"] - blue_defense_profile["takedowns_absorbed_per_min"]
            
        
    def fit(self):
        self.get_past_fights()
        self.calc_form_diff()
        self.calc_weighted_rivalry_dominance()
        self.get_style_profiles()
        self.set_activity()
        self.set_finish_power()
        self.get_defence_diff()
        
    def create_features(self):
        self.fit()

        fighters_features = create_fight_features(self.red_fighter, self.blue_fighter, self.event_date)
        
        context_features = {
            'elo_diff': self.elo_diff,
            'quality_score_diff': self.quality_score_diff,
            'form_diff': self.form_diff,
            'average_rivalry_dominance': self.average_rivalry_dominance,
            'activity_diff': self.activity_diff,
            'finish_power_diff': self.finish_diff,
            'strikes_absorbed_diff': self.strikes_absorbed_diff,
            'takedowns_absorbed_diff': self.takedowns_absorbed_diff
        }
        
        context_features_df = pd.DataFrame(context_features, index=[0])
        
        X = pd.concat([
            fighters_features.reset_index(drop=True), 
            context_features_df.reset_index(drop=True),
            self.style_features.reset_index(drop=True)
        ], axis=1)
        
        if self.winner_id is not None:
            X['target'] = 1 if self.winner_id == self.red_fighter.id else 0
            
        return X
    
    def create_readable_features(self):
        self.fit()
        
        fighters_features = create_fight_features(self.red_fighter, self.blue_fighter, self.event_date, readable=True)
        
        features = {
            "red_fighter_elo": self.red_fighter.elo_rating,
            "blue_fighter_elo": self.blue_fighter.elo_rating,
            "red_fighter_quality_score": self.red_fighter.quality_score,
            "blue_fighter_quality_score": self.blue_fighter.quality_score,
            "style_diff": self.style_diff,
            "red_finish_score": self.red_finish_score,
            "blue_finish_score": self.blue_finish_score,      
        }
        
        feature_df = pd.DataFrame(features, index=[0])
        
        X = pd.concat([
            fighters_features.reset_index(drop = True),
            feature_df.reset_index(drop=True)
        ], axis=1)
        
        return X 

           

