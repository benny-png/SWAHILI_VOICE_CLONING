# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")

class TextStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class TrainingText(BaseModel):
    client_id: str
    path: str
    sentence: str
    status: TextStatus = TextStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True

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
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
        arbitrary_types_allowed = True

class TTSRequest(BaseModel):
    text: str