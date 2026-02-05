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


# a class to organise all the data for a fight that is not given from preexitsing data 
# this means it can be used for past of furture fights
class Fight_Context:
    def __init__(self, red_fighter: Fighter, blue_fighter: Fighter, event_date: str, winner_id = None, training = False):
        fighters = [
            red_fighter,
            blue_fighter
        ]

        # shuffles the fighter ids so the model does not always think the red fighter will win
        if training:
            random.shuffle(fighters)
        
        #setting all of a fighters given data 
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

# a function to get the past fights of the fighters
    def get_past_fights(self):
        with DatabaseManager(DB_PATH) as db:
            fights_df = db.get_fighter_history([self.red_fighter.id, self.blue_fighter.id], self.event_date)

        self.fights = fights_df

#calculates how good a fighters form is 
    def calc_form(self, fighter_id: int):
        #loads all fights that contain the red or blue fighter
        fighter_history = self.fights[
            (self.fights['red_fighter_id'] == fighter_id) |
            (self.fights['red_fighter_id'] == fighter_id)
        ].tail(10)

        if len(fighter_history) < 2:
            return 0.0

        # a series of how the fighters elo has changed
        fighter_elo_history = np.where(
            fighter_history['red_fighter_id'] == fighter_id,
            fighter_history['red_fighter_elo_before'],
            fighter_history['blue_fighter_elo_before'],
        )

        #cretaes an array of evenly spaced values to act as a series of change 
        x_axis = np.arange(len(fighter_elo_history))

        #fits this data to a linear line
        try:
            slope, _ = np.polyfit(x_axis, fighter_elo_history, 1)
        except(np.linalg.LinAlgError, TypeError):
            slope = 0.0

        # the slope of this line is a fighters form score 
        # a higher slope means the fighter has a better form 
        return slope

# uses the the calc form function to get each form and get the difference 
    def calc_form_diff(self):
        red_form = self.calc_form(self.red_fighter.id)
        blue_form = self.calc_form(self.blue_fighter.id)

        #this is the difference between the fighters form difference 
        self.form_diff = red_form - blue_form
                

# calculates the average dominance of the two fighter shared fights if there is any 
# this will give more weight to recent fights 
    def calc_weighted_rivalry_dominance(self):
        #gathers all fights the fighters have in common and copies so you are not editing by reference
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

        #calcualtes a dominace score for each fight in the lsit 
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

        # generates a list of evenly spaced weights between 1 and 1.5 based on the number of fights if there is past fights
        num_fights = len(adjusted_scores)
        weights = np.linspace(1.0, 1.5, num=num_fights) if num_fights > 1 else [1.0]

        # adjusts the weight of each fight based on the mulitplier from weights 
        try:
            weighted_average = np.average(adjusted_scores, weights=weights)
        except ZeroDivisionError:
            weighted_average = 0.0

        #sets the average rivalry dominance 
        self.average_rivalry_dominance = weighted_average

# calculates how each fighters style will perform agaist each others 
# cannot use this in the final modal due to data leakage problems 
    def calc_style_performance(self):
        # preping feautes for the style model 
        ids = [self.red_fighter.id, self.blue_fighter.id]

        features = prep_style_features(ids)

        #loads the style model 
        style_model = joblib.load(MODEL_PATH)

        # gets the style model to give a probability of win based of style
        results_red_proba = style_model.predict_proba(features)

        self.red_style_performance = results_red_proba
        self.blue_style_performance = 1 - results_red_proba
        
        # subits style diff
        self.style_diff = self.red_style_performance[0]
        
    #getsa the style features of each fighters 
    def get_style_profiles(self):
        ids = [self.red_fighter.id, self.blue_fighter.id]

        features = prep_style_features(ids)
        
        self.style_features = features
    
# calculates how active each fighter has been in the UFC    
    def calc_fighter_activity(self, fighter_id: int) -> float:
        # gets all of the fights one fighter has been in 
        fighter_history = self.fights[
            ((self.fights['red_fighter_id'] == fighter_id) |
            (self.fights['blue_fighter_id'] == fighter_id)) &
            (pd.to_datetime(self.fights['event_date']) < self.event_date)
        ].tail(6)

        # if they have a low number of fights return a neutal 0.5 
        if len(fighter_history) < 2:
            return 0.5 

        # gets all the fight dates and then a list of days between fights 
        fight_dates = pd.to_datetime(fighter_history['event_date'])
        layoffs_in_days = fight_dates.diff().dt.days.dropna().values
        
        TIME_CONSTANT = 365.0 
        
        #calculates how active the fighter has been and then takes the average to submit it 
        # there is a lower average score for longer outputs by taking exponentials 
        activity_scores = np.exp(-layoffs_in_days / TIME_CONSTANT)
        final_score = np.mean(activity_scores)
        
        return final_score
    
# sets the activity scores for each fighter based of the activity algorithm from beofre 
    def set_activity(self):
        red_fighter_activity = self.calc_fighter_activity(self.red_fighter.id)
        blue_fighter_activity = self.calc_fighter_activity(self.blue_fighter.id)
        
        self.red_activity_score = red_fighter_activity
        self.blue_activity_score = blue_fighter_activity
        self.activity_diff = red_fighter_activity - blue_fighter_activity
        
        
# plots the activity of a fighter for visualisation purposes 
    def plot_activity(self):
        # settign up the matplot lib paramerters
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

        # plotting the activity scores
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
        
# calculates the how dangerous a fighter is for volitile finished
    def calc_finishing_power(self, fighter_id):
        # gets a fighters full history 
        fighter_history = self.fights[
            ((self.fights['red_fighter_id'] == fighter_id) |
            (self.fights['blue_fighter_id'] == fighter_id))
        ]
        
        if fighter_history.empty:
            return 0.0

        # gets of the the fights a fighter has won / finished and the win method 
        wins = fighter_history[fighter_history['winner_id'] == fighter_id]
        finishes_df = wins[
            wins['win_method'].str.contains('KO|SUB', na=False)
        ]

        if finishes_df.empty:
            return 0.0

        # applies a weight to the finishing score based on the round
        finishing_score = finishes_df['final_round'].apply(lambda r: 1 / r).sum()
        
        # generates a final finishing score
        total_fights = len(fighter_history)
        normalized_score = finishing_score / total_fights
        
        return normalized_score
    
# sets the finish power scores for each fighter based of the algorithm above 
    def set_finish_power(self):
        red_finish_power = self.calc_finishing_power(self.red_fighter.id)
        blue_finish_power = self.calc_finishing_power(self.blue_fighter.id)
                
        self.red_finish_score = red_finish_power
        self.blue_finish_score = blue_finish_power
        self.finish_diff = red_finish_power - blue_finish_power
        
# calculates the defensive rating of a fighter
    def calc_defensive_rating(self, fighter_id):
        # gets all of a fighters fights from the df 
        fighter_history =self.fights[
            ((self.fights['red_fighter_id'] == fighter_id) |
            (self.fights['blue_fighter_id'] == fighter_id))
        ]
        
        # sets arbitary values if the fighter has no fights 
        if fighter_history.empty:
            return {"strikes_absorbed_per_min": 4.0, "takedowns_absorbed_per_min": 4.0}
        
        
        # loops through all of a fighters fights to get the total amout of  different types of strikes that they have taken
        # also gets the amount of time they have fought for in seconds
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
        
        # gets the average amount of strikes and takedowns per minute    
        strikes_per_min = total_strikes_absorbed / total_fight_time
        takedowns_per_min = total_takedowns_absorbed / total_fight_time
        
        return {"strikes_absorbed_per_min": strikes_per_min, "takedowns_absorbed_per_min": takedowns_per_min}
    

# sets a fighters defensive rating from the algortihm above
    def get_defence_diff(self):
        red_defense_profile = self.calc_defensive_rating(self.red_fighter.id)
        blue_defense_profile = self.calc_defensive_rating(self.blue_fighter.id)
        
        self.strikes_absorbed_diff = red_defense_profile["strikes_absorbed_per_min"] - blue_defense_profile["strikes_absorbed_per_min"]
        self.takedowns_absorbed_diff = red_defense_profile["takedowns_absorbed_per_min"] - blue_defense_profile["takedowns_absorbed_per_min"]
            
# sets of the the scores from above  
    def fit(self):
        self.get_past_fights()
        self.calc_form_diff()
        self.calc_weighted_rivalry_dominance()
        self.get_style_profiles()
        self.set_activity()
        self.set_finish_power()
        self.get_defence_diff()
  
 # creates the features for the model training        
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

# createss features to send via the web API so they can be understood 
    def create_readable_features(self):
        self.fit()
        self.calc_style_performance()
        
        fighters_features = create_fight_features(self.red_fighter, self.blue_fighter, self.event_date, readable=True)
        
        features = {
            "red_fighter_elo": self.red_fighter.elo_rating,
            "blue_fighter_elo": self.blue_fighter.elo_rating,
            "red_fighter_quality_score": self.red_fighter.quality_score,
            "blue_fighter_quality_score": self.blue_fighter.quality_score,
            "rivalry_dominance": self.average_rivalry_dominance,
            "red_style_score": self.red_style_performance,
            "blue_style_score": self.blue_style_performance,
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
    
    def get_rivalry_dominance(self):
        self.set_activity()
        return self.average_rivalry_dominance
        

