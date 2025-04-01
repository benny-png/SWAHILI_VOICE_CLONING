# app/main.py
from fastapi import FastAPI, APIRouter,HTTPException, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from app.services.tts_service import generate_audio, is_swahili
from app.services.text_service import TextService
from app.services.user_service import UserService
from app.services.user_text_service import UserTextService
from fastapi.responses import StreamingResponse, FileResponse, PlainTextResponse
from app.models.schemas import (
    TrainingTextCreate, 
    TrainingTextUpdate, 
    TrainingTextInDB,
    TTSRequest,
    UserInDB,
    Token,
    UserCreate,
    UserLogin,
    LoginResponse,
    UserTrainingTextInDB,
    UserTrainingTextUpdate

)

router = APIRouter(prefix="/texts", tags=["texts for all"])

async def get_text_service():
    return TextService()


# Training text endpoints
@router.get("/", response_model=list[TrainingTextInDB])
async def list_texts(
    skip: int = 0,
    limit: int | None = None,
    status: str = None,
    service: TextService = Depends(get_text_service)
):
    """
    List training texts with optional pagination and status filter.
    
    Parameters:
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: None, returns all)
    - status: Filter by status (pending/approved/rejected)
    """
    texts = await service.list_texts(skip=skip, limit=limit, status=status)
    return texts

@router.get("/{text_id}", response_model=TrainingTextInDB)
async def get_text(text_id: str, service: TextService = Depends(get_text_service)):
    text = await service.get_text(text_id)
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
    return text

@router.put("/{text_id}", response_model=TrainingTextInDB)
async def update_text(
    text_id: str, 
    text_update: TrainingTextUpdate, 
    service: TextService = Depends(get_text_service)
):
    text = await service.update_text(text_id, text_update)
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
    return text

@router.delete("/{text_id}")
async def delete_text(text_id: str, service: TextService = Depends(get_text_service)):
    success = await service.delete_text(text_id)
    if not success:
        raise HTTPException(status_code=404, detail="Text not found")
    return {"message": "Text deleted successfully"}

@router.post("/import-training-data/")
async def import_training_data(
    data: list[dict],
    service: TextService = Depends(get_text_service)
):
    count = await service.import_training_data(data)
    return {"message": f"Successfully imported {count} training texts"}

@router.get("/export-training-data/")
async def export_training_data(
    status: str = None,
    service: TextService = Depends(get_text_service)
):
    return await service.export_texts_to_csv(status)

@router.post("/import-training-data-csv/")
async def import_training_data_csv(
    file: UploadFile = File(...),
    service: TextService = Depends(get_text_service)
):
    """
    Import training data from CSV file.
    CSV should have columns: client_id, path, sentence
    """
    count = await service.import_training_data_csv(file)
    return {
        "message": f"Successfully imported {count} training texts",
        "imported_count": count
    }
