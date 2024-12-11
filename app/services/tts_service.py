# app/services/tts_service.py
from transformers import pipeline, AutoTokenizer, VitsModel
import torch
import numpy as np
from langdetect import detect, LangDetectException
from functools import lru_cache
from ..config import settings

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

def is_swahili(text: str) -> bool:
    try:
        return detect(text) == 'sw'
    except LangDetectException:
        return False

def generate_audio(text: str, model_name):
    model, tokenizer, device = load_model(model_name)
    inputs = tokenizer(text, return_tensors="pt").to(device)
    with torch.no_grad():
        output = model(**inputs).waveform
    output_np = output.squeeze().cpu().numpy()
    return output_np, model.config.sampling_rate
