# app/main.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from .services.tts_service import generate_audio, is_swahili
from .services.text_service import TextService
from fastapi.responses import StreamingResponse, FileResponse, PlainTextResponse
from .models.schemas import (
    TrainingTextCreate, 
    TrainingTextUpdate, 
    TrainingTextInDB,
    TTSRequest
)

import os
from pathlib import Path
from .database.mongodb import connect_to_mongo, close_mongo_connection
from tarakimu import num_to_words
import io
import scipy.io.wavfile
import numpy as np
import re

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
bridget_model_name = "Benjamin-png/swahili-mms-tts-Briget_580_clips-finetuned"
emanuela_model_name = "Benjamin-png/swahili-mms-tts-Emmanuela_700_clips-finetuned"

def normalize_numbers(text: str) -> str:
    """
    Convert any numbers in the text to their Swahili word equivalents.
    """
    def replace_number(match):
        number = match.group(0)
        try:
            if '.' in number:
                return num_to_words(float(number))
            return num_to_words(number)
        except ValueError:
            return number
    
    number_pattern = r'\b\d+(?:\.\d+)?\b'
    return re.sub(number_pattern, replace_number, text)

# Dependencies
async def get_text_service():
    return TextService()

# Training text endpoints
@app.get("/texts/", response_model=list[TrainingTextInDB])
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

# TTS endpoints with number normalization
@app.post("/tts/benny")
async def tts_finetuned(request: TTSRequest):
    if not is_swahili(request.text):
        raise HTTPException(status_code=400, detail="The provided text is not in Swahili.")
    
    # Normalize numbers in the text
    normalized_text = normalize_numbers(request.text)
    audio, sample_rate = generate_audio(normalized_text, finetuned_model_name)
    
    bytes_io = io.BytesIO()
    scipy.io.wavfile.write(bytes_io, sample_rate, (audio * 32767).astype(np.int16))
    bytes_io.seek(0)
    
    return StreamingResponse(bytes_io, media_type="audio/wav")

@app.post("/tts/briget")
async def tts_original(request: TTSRequest):
    if not is_swahili(request.text):
        raise HTTPException(status_code=400, detail="The provided text is not in Swahili.")
    
    # Normalize numbers in the text
    normalized_text = normalize_numbers(request.text)
    audio, sample_rate = generate_audio(normalized_text, bridget_model_name)
    
    bytes_io = io.BytesIO()
    scipy.io.wavfile.write(bytes_io, sample_rate, (audio * 32767).astype(np.int16))
    bytes_io.seek(0)
    
    return StreamingResponse(bytes_io, media_type="audio/wav")

@app.post("/tts/emanuela")
async def tts_original(request: TTSRequest):
    if not is_swahili(request.text):
        raise HTTPException(status_code=400, detail="The provided text is not in Swahili.")
    
    # Normalize numbers in the text
    normalized_text = normalize_numbers(request.text)
    audio, sample_rate = generate_audio(normalized_text, emanuela_model_name)
    
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


    # Add this new endpoint to your main.py
@app.post("/debug/number-conversion")
async def debug_number_conversion(request: TTSRequest):
    """
    Debug endpoint to test number normalization.
    Returns both original and normalized text for comparison.
    """
    if not is_swahili(request.text):
        raise HTTPException(status_code=400, detail="The provided text is not in Swahili.")
    
    original_text = request.text
    normalized_text = normalize_numbers(request.text)
    
    return {
        "original_text": original_text,
        "normalized_text": normalized_text,
    }



# Readme file path
README_PATH = Path(__file__).parent.parent / "README.md"

@app.get("/readme", response_class=PlainTextResponse)
async def get_readme():
    """
    Returns the API readme as text/markdown
    """
    try:
        with open(README_PATH, "r") as file:
            content = file.read()
        return content
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="README.md not found")

@app.get("/readme/download")
async def download_readme():
    """
    Downloads the API readme as a markdown file
    """
    if not os.path.isfile(README_PATH):
        raise HTTPException(status_code=404, detail="README.md not found")
    
    return FileResponse(
        path=README_PATH,
        filename="swahili-voice-api-readme.md",
        media_type="text/markdown"
    )