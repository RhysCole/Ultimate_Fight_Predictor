from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from API.routes.users.users import auth_router
from API.routes.fights.fights import fights_router
from API.routes.fighters.fighters import fighter_router
from API.routes.communities.communities import community_router

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:4002"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(fights_router)
app.include_router(fighter_router)
app.include_router(community_router)

@app.get("/")
async def root():
    return {"message": "Hello bati boy, Now use a proper path"}

