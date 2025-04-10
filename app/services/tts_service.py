# app/services/tts_service.py
from transformers import pipeline, AutoTokenizer, VitsModel
import torch
import numpy as np
from functools import lru_cache
from ..config import settings
import re
import time
import logging
from typing import List, Tuple

logger = logging.getLogger("swahili-voice-api")

@lru_cache()
def load_model(model_name):
    logger.info(f"Loading model: {model_name}")
    start_time = time.time()
    
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
    
    load_time = time.time() - start_time
    logger.info(f"Model {model_name} loaded in {load_time:.4f} seconds")
    
    return model, tokenizer, device

def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using regex patterns specific to Swahili."""
    start_time = time.time()
    text = text.strip()
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    result = [s.strip() for s in sentences if s.strip()]
    
    process_time = time.time() - start_time
    logger.debug(f"Split text into {len(result)} sentences in {process_time:.4f} seconds")
    
    return result

def is_swahili(text: str) -> bool:
    """
    Dummy function that always returns True.
    The language detection feature has been removed as it was not working properly.
    """
    return True

def generate_audio(text: str, model_name: str) -> Tuple[np.ndarray, int]:
    """Generate audio for text, handling it sentence by sentence."""
    logger.info(f"Generating audio for text of length {len(text)} using model {model_name}")
    start_time = time.time()
    
    # Load model
    model_load_start = time.time()
    model, tokenizer, device = load_model(model_name)
    model_load_time = time.time() - model_load_start
    logger.debug(f"Model loading took {model_load_time:.4f} seconds")
    
    # Split into sentences
    sentence_split_start = time.time()
    sentences = split_into_sentences(text)
    sentence_split_time = time.time() - sentence_split_start
    logger.debug(f"Sentence splitting took {sentence_split_time:.4f} seconds")
    
    # Process each sentence
    audio_segments = []
    for i, sentence in enumerate(sentences):
        if not sentence.strip():
            continue
        
        sentence_start = time.time()
        inputs = tokenizer(sentence, return_tensors="pt").to(device)
        
        tokenization_time = time.time() - sentence_start
        logger.debug(f"Tokenization for sentence {i+1}/{len(sentences)} took {tokenization_time:.4f} seconds")
        
        inference_start = time.time()
        with torch.no_grad():
            output = model(**inputs).waveform
        inference_time = time.time() - inference_start
        logger.debug(f"Inference for sentence {i+1}/{len(sentences)} took {inference_time:.4f} seconds")
        
        audio_segment = output.squeeze().cpu().numpy()
        audio_segments.append(audio_segment)
        
        sentence_time = time.time() - sentence_start
        logger.debug(f"Processing sentence {i+1}/{len(sentences)} took {sentence_time:.4f} seconds")
    
    # Concatenate audio segments
    concatenation_start = time.time()
    final_audio = np.concatenate(audio_segments)
    concatenation_time = time.time() - concatenation_start
    logger.debug(f"Audio concatenation took {concatenation_time:.4f} seconds")
    
    total_time = time.time() - start_time
    logger.info(f"Total audio generation took {total_time:.4f} seconds for {len(sentences)} sentences")
    
    return final_audio, model.config.sampling_rate