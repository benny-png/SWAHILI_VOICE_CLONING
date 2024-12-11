# app/models/schemas.py
from pydantic import BaseModel, Field, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from typing import Optional, Any, Annotated
from datetime import datetime
from enum import Enum
from bson import ObjectId

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, (str, ObjectId)):
            raise ValueError("Invalid ObjectId")
        return str(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
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
    id: Annotated[PyObjectId, Field(alias="_id", default_factory=PyObjectId)]

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True

class TTSRequest(BaseModel):
    text: str