from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, Annotated
from datetime import datetime, timezone
from enum import Enum
from bson import ObjectId
from pydantic_core import CoreSchema, core_schema

class PyObjectId(str):
    @classmethod
    def validate(cls, value):
        if not isinstance(value, (str, ObjectId)):
            raise ValueError("Invalid ObjectId")
        return str(value)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, _handler) -> CoreSchema:
        return core_schema.str_schema()

class TextStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class TrainingText(BaseModel):
    client_id: str
    path: str
    sentence: str
    status: TextStatus = TextStatus.PENDING
    created_at: datetime = Field(default_factory=lambda:datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda:datetime.now(timezone.utc))

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class TrainingTextCreate(BaseModel):
    client_id: str
    path: str
    sentence: str

class TrainingTextUpdate(BaseModel):
    client_id: Optional[str] = None
    path: Optional[str] = None
    sentence: Optional[str] = None
    status: Optional[TextStatus] = None

class TrainingTextInDB(TrainingText):
    id: PyObjectId = Field(alias="_id", default_factory=PyObjectId)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        populate_by_name=True
    )

class TTSRequest(BaseModel):
    text: str

# Updated User models with PyObjectId

# User creation schema (for registration)
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str  # Plaintext password from client

# User update schema (no password here for security)
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

# User in database schema (stored hashed password)
class UserInDB(BaseModel):
    id: PyObjectId = Field(alias="_id", default_factory=PyObjectId)
    username: str
    email: EmailStr
    hashed_password: str  # Stored hashed password
    total_audio_length: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda:datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda:datetime.now(timezone.utc))
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        populate_by_name=True
    )

# User login schema
class UserLogin(BaseModel):
    username: str
    password: str

# Token response schema
class Token(BaseModel):
    access_token: str
    token_type: str

# User response schema (without hashed_password)
class UserResponse(BaseModel):
    id: PyObjectId
    username: str
    email: str
    
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

# New schema for login response
class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# User training text models

# Base UserTrainingText schema with user_id
class UserTrainingText(BaseModel):
    user_id: PyObjectId  # Links to users collection
    path: Optional[str] = None
    sentence: str
    status: TextStatus = TextStatus.PENDING
    created_at: datetime = Field(default_factory=lambda:datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda:datetime.now(timezone.utc))
    audio_length: Optional[int] = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class UserTrainingTextCreate(BaseModel):
    path: Optional[str] = None
    sentence: str

class UserTrainingTextUpdate(BaseModel):
    path: Optional[str] = None
    sentence: Optional[str] = None
    status: Optional[TextStatus] = None
    audio_length: Optional[int] = None

class UserTrainingTextInDB(UserTrainingText):
    id: PyObjectId = Field(alias="_id", default_factory=PyObjectId)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        populate_by_name=True
    )