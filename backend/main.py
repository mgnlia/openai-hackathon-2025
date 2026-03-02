"""DocAgent — FastAPI backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import health, chat, models
from backend.routers.documents import router as documents_router

app = FastAPI(
    title="DocAgent API",
    description="Local-first AI document analyst powered by gpt-oss-20b via Groq",
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

@app.get("/")
async def root():
    return {
        "name": "DocAgent",
        "description": "Local-first AI document analyst powered by gpt-oss-20b",
        "models": ["openai/gpt-oss-20b", "openai/gpt-oss-120b"],
        "docs": "/docs",
    }
