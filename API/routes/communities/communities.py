from fastapi import APIRouter, HTTPException, status

from Database.user_manager import CommunityManager

community_router = APIRouter(
    prefix="/community",
    tags=["Community"]
)

@community_router.post("/join")
def join_community(community_id: int, user_id: int, bet: int):
    with CommunityManager() as db:
        return db.join_community(community_id, user_id, bet)
    
@community_router.post("/leave")
def leave_community(community_id: int, user_id: int):
    with CommunityManager() as db:
        return db.leave_community(community_id, user_id)
    
@community_router.post("/create")
def create_community(name: str, fight_id: int, creator_user_id: int):
    with CommunityManager() as db:
        return db.create_community(name, fight_id, creator_user_id)
    
@community_router.post("/bet")
def bet(community_id: int, user_id: int, bet: int):
    with CommunityManager() as db:
        return db.place_bet(community_id, user_id, bet)
    

@community_router.get('/details')
def get_details(community_id: int):
    with CommunityManager() as db:
        return db.get_community_details(community_id)
    
@community_router.get('/byFightID')
def get_communities(fight_id: int):
    with CommunityManager() as db:
        return db.get_communities_by_fightID(fight_id)

@community_router.get('/all')    
def get_all_communities():
    with CommunityManager() as db:
        return db.get_all_communities()
    

