from fastapi import APIRouter, HTTPException, status

from config.config import DB_PATH
from Database.user_manager import UserManager
from Models.DB_Classes.User import User
from API.routes.users.schema import UserCreate, UserLogin, UserResponse

auth_router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate):
    with UserManager(DB_PATH) as db:
        if db.get_user_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered."
            )
        
        new_user_id = db.create_user(
            first_name=user_data.firstname,
            last_name=user_data.lastname,
            email=user_data.email,
            plain_text_password=user_data.password
        )
        
        if not new_user_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create user."
            )
            
        return 
    
@auth_router.post("/login")
def login_user(login_data: UserLogin):
    with UserManager(DB_PATH) as db:
        is_valid = db.check_password(login_data.email, login_data.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password."
            )
            
        user = db.get_user_by_email(login_data.email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_NOT_FOUND,
                detail="could not find user from email"
            )
            
        print(user)
            
        db.update_last_login(user.id)
        
        return {"message": f"Login successful for {user.email}", "id": user.id, "firstname": user.first_name, "lastname": user.last_name, "email": user.email, "balance": user.balance, "role": user.role}