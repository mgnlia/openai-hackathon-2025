"""Health check — also tests gpt-oss model access."""
from fastapi import APIRouter
from backend.llm import test_model_access
from backend.config import settings

router = APIRouter()


@router.get("/")
async def root():
    return {"service": "OpenAI Hackathon API", "version": "0.1.0", "docs": "/docs"}


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/health/model")
async def model_health():
    """Test live access to gpt-oss-20b via Groq."""
    result = await test_model_access()
    return {
        "model_fast": settings.model_fast,
        "model_powerful": settings.model_powerful,
        "groq_configured": bool(settings.groq_api_key),
        "openai_configured": bool(settings.openai_api_key),
        "test_result": result,
    }
