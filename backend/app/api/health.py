from fastapi import APIRouter
from app.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ReadBack Medical Document Understanding & Fidelity Verification API",
        "app_env": settings.APP_ENV,
        "demo_mode": settings.DEMO_MODE,
        "ocr_provider": settings.OCR_PROVIDER,
        "multilingual_enabled": settings.ENABLE_MULTILINGUAL,
        "supported_languages": ["en", "kn", "hi", "ta"]
    }
