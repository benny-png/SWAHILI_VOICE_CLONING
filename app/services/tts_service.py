# app/services/tts_service.py
from transformers import pipeline, AutoTokenizer, VitsModel
import torch
import numpy as np
from langdetect import detect, LangDetectException
from functools import lru_cache
from ..config import settings
import re
import numpy as np
from typing import List, Tuple

@lru_cache()
def load_model(model_name):
    device = "cpu"
    model = VitsModel.from_pretrained(
        model_name, 
        token=settings.HF_TOKEN,
        cache_dir=settings.MODEL_CACHE_DIR
    ).to(device)
    tokenizer = AutoTokenizer.from_pretrained(
        model_name, 
        token=settings.HF_TOKEN,
        cache_dir=settings.MODEL_CACHE_DIR
    )
    return model, tokenizer, device

def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using regex patterns specific to Swahili."""
    # Clean the text first
    text = text.strip()
    
    # Split on common sentence endings (., !, ?)
    # but avoid splitting on common abbreviations
    # and handle multiple punctuation marks
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    
    # Further clean and filter sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences

def is_swahili(text: str) -> bool:
    try:
        return detect(text) == 'sw'
    except LangDetectException:
        return False

def add_pause_between_sentences(audio: np.ndarray, sample_rate: int, pause_duration: float = 0.5) -> np.ndarray:
    """Add a pause between sentences."""
    pause_length = int(sample_rate * pause_duration)
    pause = np.zeros(pause_length)
    return np.concatenate([audio, pause])

def generate_audio(text: str, model_name: str) -> Tuple[np.ndarray, int]:
    """Generate audio for text, handling it sentence by sentence."""
    model, tokenizer, device = load_model(model_name)
    
    # Split text into sentences
    sentences = split_into_sentences(text)
    
    # Process each sentence and collect audio
    audio_segments = []
    for sentence in sentences:
        # Skip empty sentences
        if not sentence.strip():
            continue
            
        # Generate audio for sentence
        inputs = tokenizer(sentence, return_tensors="pt").to(device)
        with torch.no_grad():
            output = model(**inputs).waveform
        
        # Convert to numpy and add to segments
        audio_segment = output.squeeze().cpu().numpy()
        
        # Add pause after sentence (except for the last sentence)
        audio_segments.append(audio_segment)
        if sentence != sentences[-1]:
            audio_segments.append(np.zeros(int(model.config.sampling_rate * 0.02)))  # 0.5s pause
    
    # Combine all segments
    final_audio = np.concatenate(audio_segments)
    
    return final_audio, model.config.sampling_rate

# Example usage in FastAPI endpoint
"""
@app.post("/tts/benny")
async def tts_finetuned(request: TTSRequest):
    if not is_swahili(request.text):
        raise HTTPException(status_code=400, detail="The provided text is not in Swahili.")
    
    audio, sample_rate = generate_audio(request.text, finetuned_model_name)
    
    # Convert to WAV format
    bytes_io = io.BytesIO()
    scipy.io.wavfile.write(bytes_io, sample_rate, (audio * 32767).astype(np.int16))
    bytes_io.seek(0)
    
    return StreamingResponse(bytes_io, media_type="audio/wav")
"""