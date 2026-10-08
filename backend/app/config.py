import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_ENV: str = "development"
    DEMO_MODE: bool = True
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OCR_PROVIDER: str = "paddleocr"
    TESSERACT_CMD: Optional[str] = None
    DATABASE_URL: str = "sqlite:///./readback.db"
    CONFIDENCE_THRESHOLD: float = 0.80
    ENABLE_MULTILINGUAL: bool = True
    UPLOAD_DIR: str = "./uploads"
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
