# app/main.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from .services.tts_service import generate_audio, is_swahili
from .services.text_service import TextService
from fastapi.responses import StreamingResponse
from .models.schemas import (
    TrainingTextCreate, 
    TrainingTextUpdate, 
    TrainingTextInDB,
    TTSRequest
)
from .database.mongodb import connect_to_mongo, close_mongo_connection
import io
import scipy.io.wavfile
import numpy as np

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event handlers
app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

# Models
finetuned_model_name = "Benjamin-png/swahili-mms-tts-finetuned"
original_model_name = "Benjamin-png/swahili-mms-tts-Briget_580_clips-finetuned"

# Dependencies
async def get_text_service():
    return TextService()

# Training text endpoints
@app.post("/texts/", response_model=TrainingTextInDB)
async def create_text(text: TrainingTextCreate, service: TextService = Depends(get_text_service)):
    if not is_swahili(text.sentence):
        raise HTTPException(status_code=400, detail="The provided text is not in Swahili.")
    return await service.create_text(text)

@app.get("/texts/{text_id}", response_model=TrainingTextInDB)
async def get_text(text_id: str, service: TextService = Depends(get_text_service)):
    text = await service.get_text(text_id)
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
    return text

@app.put("/texts/{text_id}", response_model=TrainingTextInDB)
async def update_text(
    text_id: str, 
    text_update: TrainingTextUpdate, 
    service: TextService = Depends(get_text_service)
):
    text = await service.update_text(text_id, text_update)
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
    return text

@app.delete("/texts/{text_id}")
async def delete_text(text_id: str, service: TextService = Depends(get_text_service)):
    success = await service.delete_text(text_id)
    if not success:
        raise HTTPException(status_code=404, detail="Text not found")
    return {"message": "Text deleted successfully"}

@app.get("/texts/", response_model=list[TrainingTextInDB])
async def list_texts(
    skip: int = 0, 
    limit: int = 10, 
    status: str = None,
    service: TextService = Depends(get_text_service)
):
    texts = await service.list_texts(skip=skip, limit=limit, status=status)
    return texts

@app.post("/import-training-data/")
async def import_training_data(
    data: list[dict],
    service: TextService = Depends(get_text_service)
):
    count = await service.import_training_data(data)
    return {"message": f"Successfully imported {count} training texts"}

@app.get("/export-training-data/")
async def export_training_data(
    status: str = None,
    service: TextService = Depends(get_text_service)
):
    return await service.export_texts_to_csv(status)

# TTS endpoints
@app.post("/tts/benny")
async def tts_finetuned(request: TTSRequest):
    if not is_swahili(request.text):
        raise HTTPException(status_code=400, detail="The provided text is not in Swahili.")
    
    audio, sample_rate = generate_audio(request.text, finetuned_model_name)
    
    bytes_io = io.BytesIO()
    scipy.io.wavfile.write(bytes_io, sample_rate, (audio * 32767).astype(np.int16))
    bytes_io.seek(0)
    
    return StreamingResponse(bytes_io, media_type="audio/wav")

@app.post("/tts/briget")
async def tts_original(request: TTSRequest):
    if not is_swahili(request.text):
        raise HTTPException(status_code=400, detail="The provided text is not in Swahili.")
    
    audio, sample_rate = generate_audio(request.text, original_model_name)
    
    bytes_io = io.BytesIO()
    scipy.io.wavfile.write(bytes_io, sample_rate, (audio * 32767).astype(np.int16))
    bytes_io.seek(0)
    
    return StreamingResponse(bytes_io, media_type="audio/wav")



@app.post("/import-training-data-csv/")
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