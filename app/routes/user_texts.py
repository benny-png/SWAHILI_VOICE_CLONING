# app/main.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from jose import JWTError, jwt
from pydantic import BaseModel
from app.services.user_text_service import UserTextService
from app.config import settings
from fastapi.responses import StreamingResponse, FileResponse, PlainTextResponse
from app.models.schemas import (
    Token,
    UserCreate,
    UserLogin,
    LoginResponse,
    UserTrainingTextInDB,
    UserTrainingTextUpdate
)


# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

app = FastAPI()

# Dependency to get current user from token
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return user_id

# User texts router with authentication
router = APIRouter(
    prefix="/user",
    tags=["Authenticated user texts"],
    dependencies=[Depends(get_current_user)]  # This applies to all routes in this router
)

async def get_user_text_service():
    return UserTextService()

# User training text endpoints
@router.get("/texts", response_model=list[UserTrainingTextInDB])
async def list_user_texts(
    current_user: Annotated[str, Depends(get_current_user)],
    skip: int = 0,
    limit: int | None = None,
    status: str = None,
    service: UserTextService = Depends(get_user_text_service)
):
    """List user training texts with optional filters"""
    return await service.list_texts(
        skip=skip,
        limit=limit,
        status=status,
        user_id=current_user  # Use authenticated user_id
    )

@router.get("/texts/{text_id}", response_model=UserTrainingTextInDB)
async def get_user_text(
    text_id: str,
    current_user: Annotated[str, Depends(get_current_user)],
    service: UserTextService = Depends(get_user_text_service)
):
    """Get a specific user training text by ID"""
    text = await service.get_text(text_id)
    if not text or text.user_id != current_user:
        raise HTTPException(status_code=404, detail="Text not found or unauthorized")
    return text

@router.put("/texts/{text_id}", response_model=UserTrainingTextInDB)
async def update_user_text(
    text_id: str,
    text_update: UserTrainingTextUpdate,
    current_user: Annotated[str, Depends(get_current_user)],
    service: UserTextService = Depends(get_user_text_service)
):
    """Update an existing user training text"""
    text = await service.get_text(text_id)
    if not text or text.user_id != current_user:
        raise HTTPException(status_code=404, detail="Text not found or unauthorized")
    return await service.update_text(text_id, text_update)

@router.delete("/texts/{text_id}", response_model=dict)
async def delete_user_text(
    text_id: str,
    current_user: Annotated[str, Depends(get_current_user)],
    service: UserTextService = Depends(get_user_text_service)
):
    """Delete a user training text"""
    text = await service.get_text(text_id)
    if not text or text.user_id != current_user:
        raise HTTPException(status_code=404, detail="Text not found or unauthorized")
    success = await service.delete_text(text_id)
    return {"message": "Text deleted successfully"}

@router.post("/texts/import-csv/{user_id}", response_model=dict)
async def import_training_data_csv(
    user_id: str,
    current_user: Annotated[str, Depends(get_current_user)],
    service: UserTextService = Depends(get_user_text_service),
    file: UploadFile = File(...)
):
    """Import training data from CSV file"""
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Cannot import data for another user")
    count = await service.import_training_data_csv(file, user_id)
    return {"message": f"Successfully imported {count} training texts"}

