# app/config.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    HF_TOKEN: str = os.getenv("HF_TOKEN")
    MONGODB_URL: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DB_NAME: str = "swahili_tts"
    MODEL_CACHE_DIR: str = "./model_cache"

settings = Settings()