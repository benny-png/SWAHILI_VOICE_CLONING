from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    HF_TOKEN: str
    MONGODB_URL: str 
    DB_NAME: str = "swahili_tts"
    MODEL_CACHE_DIR: str = "./model_cache"

    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 240

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool 
    MAIL_SSL_TLS: bool 
    USE_CREDENTIALS: bool 

    FRONTEND_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"

settings = Settings()
