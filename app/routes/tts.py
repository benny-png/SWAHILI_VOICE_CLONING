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
@router.post("/benny", description="""
Generate speech using Benny's voice model. The text will be automatically normalized, converting numbers to their Swahili word equivalents.

Example using curl:
```bash
curl -X POST "http://localhost:8000/tts/benny" \\
     -H "Content-Type: application/json" \\
     -d '{"text":"Nina umri wa miaka 25"}' \\
     --output benny_speech.wav
```

Example using Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/tts/benny",
    json={"text": "Nina umri wa miaka 25"}
)

with open("benny_speech.wav", "wb") as f:
    f.write(response.content)
```

The API will:
1. Convert any numbers to their Swahili word equivalents
2. Generate speech using Benny's voice model
3. Return a WAV audio file
""")
async def tts_finetuned(request: TTSRequest):
    # Normalize numbers in the text
    normalized_text = normalize_numbers(request.text)
    audio, sample_rate = generate_audio(normalized_text, finetuned_model_name)
    
    bytes_io = io.BytesIO()
    scipy.io.wavfile.write(bytes_io, sample_rate, (audio * 32767).astype(np.int16))
    bytes_io.seek(0)
    
    return StreamingResponse(bytes_io, media_type="audio/wav")

@router.post("/briget", description="""
Generate speech using Briget's voice model. The text will be automatically normalized, converting numbers to their Swahili word equivalents.

Example using curl:
```bash
curl -X POST "http://localhost:8000/tts/briget" \\
     -H "Content-Type: application/json" \\
     -d '{"text":"Nina shilingi 100.50"}' \\
     --output briget_speech.wav
```

Example using Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/tts/briget",
    json={"text": "Nina shilingi 100.50"}
)

with open("briget_speech.wav", "wb") as f:
    f.write(response.content)
```

The API will:
1. Convert any numbers to their Swahili word equivalents
2. Generate speech using Briget's voice model
3. Return a WAV audio file
""")
async def tts_original(request: TTSRequest):
    # Normalize numbers in the text
    normalized_text = normalize_numbers(request.text)
    audio, sample_rate = generate_audio(normalized_text, bridget_model_name)
    
    bytes_io = io.BytesIO()
    scipy.io.wavfile.write(bytes_io, sample_rate, (audio * 32767).astype(np.int16))
    bytes_io.seek(0)
    
    return StreamingResponse(bytes_io, media_type="audio/wav")

@router.post("/emanuela", description="""
Generate speech using Emanuela's voice model. The text will be automatically normalized, converting numbers to their Swahili word equivalents.

Example using curl:
```bash
curl -X POST "http://localhost:8000/tts/emanuela" \\
     -H "Content-Type: application/json" \\
     -d '{"text":"Nataka kununua vitu 10"}' \\
     --output emanuela_speech.wav
```

Example using Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/tts/emanuela",
    json={"text": "Nataka kununua vitu 10"}
)

with open("emanuela_speech.wav", "wb") as f:
    f.write(response.content)
```

The API will:
1. Convert any numbers to their Swahili word equivalents
2. Generate speech using Emanuela's voice model
3. Return a WAV audio file
""")
async def tts_original(request: TTSRequest):
    # Normalize numbers in the text
    normalized_text = normalize_numbers(request.text)
    audio, sample_rate = generate_audio(normalized_text, emanuela_model_name)
    
    bytes_io = io.BytesIO()
    scipy.io.wavfile.write(bytes_io, sample_rate, (audio * 32767).astype(np.int16))
    bytes_io.seek(0)
    
    return StreamingResponse(bytes_io, media_type="audio/wav")


    # Add this new endpoint to your main.py
@router.post("/debug/number-conversion", description="""
Debug endpoint to test how numbers in Swahili text will be normalized before speech generation.

Example using curl:
```bash
curl -X POST "http://localhost:8000/tts/debug/number-conversion" \\
     -H "Content-Type: application/json" \\
     -d '{"text":"Nina umri wa miaka 25 na shilingi 100.50"}'
```

Example using Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/tts/debug/number-conversion",
    json={"text": "Nina umri wa miaka 25 na shilingi 100.50"}
)
print(response.json())
```

The API will:
1. Convert any numbers to their Swahili word equivalents
2. Return both the original and normalized text
""")
async def debug_number_conversion(request: TTSRequest):
    """
    Debug endpoint to test number normalization.
    Returns both original and normalized text for comparison.
    """
    original_text = request.text
    normalized_text = normalize_numbers(request.text)
    
    return {
        "original_text": original_text,
        "normalized_text": normalized_text,
    }
