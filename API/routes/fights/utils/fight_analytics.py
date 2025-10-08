from Database.database_manager import DatabaseManager
from Fight_Predictor.Fight_Context import FightContext

def get_post_fight_analytics(fight_id):
    with DatabaseManager() as db:
        fight = db.get_fight_by_id(fight_id)
    print(fight)
    
        
        
    
    
    
if __name__ == "__main__":
    get_post_fight_analytics(1)