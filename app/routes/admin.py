from fastapi import HTTPException, Depends, APIRouter
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from jose import JWTError, jwt
from app.services.user_service import UserService
from app.services.user_text_service import UserTextService
from app.config import settings

from app.models.schemas import (
    UserUpdate
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

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

async def get_user_text_service():
    return UserTextService()

async def get_user_service():
    return UserService()


# User texts router with authentication
router = APIRouter(
    prefix="/admin",
    tags=["addmini manager"],
    dependencies=[Depends(get_current_user)]  # This applies to all routes in this router
)


@router.get("/users")
async def list_users(
    service1: UserService = Depends(get_user_service),
):
    return await service1.list_users()


@router.put("/update/user")
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    service1: UserService = Depends(get_user_service),
):
    
    return await service1.update_user(user_id,user_update)

@router.delete("/delete/user",description="deletes the user and their texts")
async def delete_user(
    user_id: str,
    service1: UserService = Depends(get_user_service),
    service2: UserTextService=Depends(get_user_text_service)
):
    if await service1.delete_user(user_id):
        if await service2.delete_texts_by_user(user_id):
             return {"message":"user deleted succesfully and all texts"}
    
        return{'message':'user deleted succesfully not sure about the texts'}
    
    return  {"error":"unable to delete user"}

@router.delete("/delete/user/texts",description="delete user's texts")
async def delete_user_texts(
    user_id: str,
    service2: UserTextService=Depends(get_user_text_service)
):
   
    return await service2.delete_texts_by_user(user_id)
          
   