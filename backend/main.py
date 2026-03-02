"""DocAgent — FastAPI backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import health, chat, models
from backend.routers.documents import router as documents_router
from backend.routers.tools import router as tools_router
from backend.routers.demo import router as demo_router

app = FastAPI(
    title="DocAgent API",
    description="Local-first AI document analyst powered by gpt-oss-20b + gpt-oss-120b via Groq",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(models.router, prefix="/api", tags=["models"])
app.include_router(documents_router, prefix="/api", tags=["documents"])
app.include_router(tools_router, prefix="/api", tags=["tools"])
app.include_router(demo_router, prefix="/api", tags=["demo"])


@app.get("/")
async def root():
    return {
        "name": "DocAgent",
        "description": "Local-first AI document analyst powered by gpt-oss-20b + gpt-oss-120b",
        "models": ["openai/gpt-oss-20b", "openai/gpt-oss-120b"],
        "provider": "Groq (Chat Completions + Responses API)",
        "endpoints": {
            "docs": "/docs",
            "health": "/health/model",
            "upload": "POST /api/documents/upload",
            "analyze": "GET /api/documents/analyze/stream",
            "qa": "POST /api/documents/qa",
            "agent": "POST /api/agent/run",
            "tools": "GET /api/tools",
            "demo": "GET /api/demo",
            "demo_script": "GET /api/demo/script",
        },
    }
