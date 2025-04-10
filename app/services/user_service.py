from ..database.mongodb import Database
from ..models.schemas import UserCreate, UserUpdate, UserInDB, UserLogin, Token, LoginResponse, UserResponse
from bson import ObjectId
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Depends
from app.config import settings
from passlib.context import CryptContext
import jwt

from fastapi.security import OAuth2PasswordBearer

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

class UserService:
    def __init__(self):
        self.db = Database.client[settings.DB_NAME]
        self.collection = self.db.users

    # Hash password
    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    # Verify password
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    # Create JWT token
    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    async def create_user(self, user: UserCreate) -> UserInDB:
        try:
            # Check if email already exists
            if await self.collection.find_one({"email": user.email}):
                raise HTTPException(status_code=400, detail="Email already registered")
            
            user_dict = {
                "username": user.username,
                "email": user.email,
                "hashed_password": self.get_password_hash(user.password),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            result = await self.collection.insert_one(user_dict)
            created_user = await self.collection.find_one({"_id": result.inserted_id})
            if created_user:
                created_user["id"] = str(created_user["_id"])
                del created_user["_id"]
                return UserInDB(**created_user)
            raise HTTPException(status_code=500, detail="Failed to create user")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def authenticate_user(self, user_login: UserLogin) -> UserInDB:
        try:
            user = await self.collection.find_one({"username": user_login.username})
            if not user or not self.verify_password(user_login.password, user["hashed_password"]):
                raise HTTPException(status_code=401, detail="Invalid username or password")
            user["id"] = str(user["_id"])
            del user["_id"]
            return UserInDB(**user)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def login(self, user_login: UserLogin) -> LoginResponse:
        user = await self.authenticate_user(user_login)
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
             data={"sub": user.id}, expires_delta=access_token_expires
        )
    # Construct the user response without hashed_password
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email
        )
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )

    async def get_user(self, user_id: str) -> UserInDB:
        try:
            user = await self.collection.find_one({"_id": ObjectId(user_id)})
            if user:
                user["id"] = str(user["_id"])
                del user["_id"]
                return UserInDB(**user)
            return None
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    async def update_user(self, user_id: str, user_update: UserUpdate) -> UserInDB:
        try:
            user_dict = user_update.model_dump(exclude_unset=True)
            user_dict["updated_at"] = datetime.now(timezone.utc)
            
            await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": user_dict}
            )
            updated_user = await self.collection.find_one({"_id": ObjectId(user_id)})
            if updated_user:
                updated_user["id"] = str(updated_user["_id"])
                del updated_user["_id"]
                return UserInDB(**updated_user)
            raise HTTPException(status_code=404, detail="User not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    
    async def increment_total_audio_length(self, user_id: str, length: int):
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$inc": {"total_audio_length": length},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                }
            )
            if result.modified_count == 0:
                raise Exception("User not found or no change made.")
        except Exception as e:
            raise RuntimeError(f"Failed to increment audio length: {e}")
        
        
    async def get_total_audio_length(self, user_id: str):
        try:
            user = await self.collection.find_one(
                {"_id": ObjectId(user_id)},
                {"total_audio_length": 1}  # Only fetch this field
            )
            if not user:
                return None
            return user.get("total_audio_length", 0)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch total audio length: {e}")        


    async def delete_user(self, user_id: str) -> bool:
        try:
            result = await self.collection.delete_one({"_id": ObjectId(user_id)})    
            return result.deleted_count > 0
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def list_users(self, skip: int = 0, limit: int | None = None):
        try:
            cursor = self.collection.find().skip(skip)
            if limit is not None:
                cursor = cursor.limit(limit)
            
            users = await cursor.to_list(length=None)
            if not users:
                raise HTTPException(status_code=404, detail="No users found")

            for user in users:
                user["id"] = str(user["_id"])
                del user["_id"]

            total_seconds = sum(user.get("total_audio_length", 0) for user in users)

            return {
                "total_seconds_recorded": total_seconds,
                "users": [UserInDB(**user) for user in users]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    