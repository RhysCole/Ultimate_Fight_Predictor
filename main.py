from Database.database_manager import DatabaseManager

def main():
    db_path = 'Database/fighters.db'

    with DatabaseManager(db_path) as db:
        fights = db.get_fights()
        for fight in fights[:10]:
            print(fight)  

 
        
if __name__ == "__main__":
    main()