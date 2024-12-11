# app/models/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Annotated
from datetime import datetime
from enum import Enum
from bson import ObjectId

class PyObjectId(str):
    @classmethod
    def validate(cls, value):
        if not isinstance(value, (str, ObjectId)):
            raise ValueError("Invalid ObjectId")
        return str(value)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return handler("string")

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