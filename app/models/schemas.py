# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

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
    id: str = Field(alias="_id")

class TTSRequest(BaseModel):
    text: str
