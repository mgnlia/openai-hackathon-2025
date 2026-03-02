"""Models router — list available gpt-oss models."""
from fastapi import APIRouter
from backend.config import settings

router = APIRouter()

AVAILABLE_MODELS = [
    {"id": "openai/gpt-oss-20b", "name": "GPT-OSS 20B", "provider": "groq",
     "context_window": 131072, "description": "Fast MoE model for agentic workflows"},
    {"id": "openai/gpt-oss-120b", "name": "GPT-OSS 120B", "provider": "groq",
     "context_window": 131072, "description": "Powerful reasoning model"},
]

@router.get("/models")
async def list_models():
    return {"models": AVAILABLE_MODELS, "default_fast": settings.model_fast, "default_powerful": settings.model_powerful}
