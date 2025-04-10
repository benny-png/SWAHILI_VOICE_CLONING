# app/services/tts_service.py
from transformers import pipeline, AutoTokenizer, VitsModel
import torch
import numpy as np
from functools import lru_cache
from ..config import settings
import re
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
    text = text.strip()
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in sentences if s.strip()]

def is_swahili(text: str) -> bool:
    """
    Dummy function that always returns True.
    The language detection feature has been removed as it was not working properly.
    """
    return True

def generate_audio(text: str, model_name: str) -> Tuple[np.ndarray, int]:
    """Generate audio for text, handling it sentence by sentence."""
    model, tokenizer, device = load_model(model_name)
    sentences = split_into_sentences(text)
    
    audio_segments = []
    for sentence in sentences:
        if not sentence.strip():
            continue
            
        inputs = tokenizer(sentence, return_tensors="pt").to(device)
        with torch.no_grad():
            output = model(**inputs).waveform
        audio_segment = output.squeeze().cpu().numpy()
        audio_segments.append(audio_segment)
    
    final_audio = np.concatenate(audio_segments)
    return final_audio, model.config.sampling_rate