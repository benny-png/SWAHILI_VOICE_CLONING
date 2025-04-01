# app/main.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File,APIRouter
from app.services.tts_service import generate_audio, is_swahili
from app.services.text_service import TextService
from fastapi.responses import StreamingResponse, FileResponse, PlainTextResponse
from app.models.schemas import (
    TrainingTextCreate, 
    TrainingTextUpdate, 
    TrainingTextInDB,
    TTSRequest,
)

import os
from pathlib import Path
from app.database.mongodb import connect_to_mongo, close_mongo_connection
from tarakimu import num_to_words
import io
import scipy.io.wavfile
import numpy as np
import re



router = APIRouter(prefix="/tts", tags=["tts"])

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


# TTS endpoints with number normalization
@router.post("/benny")
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

@router.post("/briget")
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

@router.post("/emanuela")
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


    # Add this new endpoint to your main.py
@router.post("/debug/number-conversion")
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
