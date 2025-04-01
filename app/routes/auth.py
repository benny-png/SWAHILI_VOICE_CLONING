# app/main.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from app.services.user_service import UserService
from app.services.user_text_service import UserTextService
from fastapi.responses import StreamingResponse, FileResponse, PlainTextResponse
from app.models.schemas import (
    Token,
    UserCreate,
    UserLogin,
    LoginResponse,
    UserInDB
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

async def get_user_service():
    return UserService()

#authentication endpoints

# Registration endpoint
@router.post("/register/", response_model=UserInDB)
async def register_user(user: UserCreate, service: UserService = Depends(get_user_service)):
    return await service.create_user(user)

# Login endpoint
@router.post("/login/", response_model=LoginResponse)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), service: UserService = Depends(get_user_service)):
    user_login = UserLogin(username=form_data.username, password=form_data.password)  # username field is email
    return await service.login(user_login)
