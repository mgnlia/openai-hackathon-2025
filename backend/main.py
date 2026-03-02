"""OpenAI Hackathon — FastAPI backend with gpt-oss-20b/120b via Groq."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from backend.routers import chat, models, health  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    print("🚀 OpenAI Hackathon API starting — gpt-oss models ready")
    yield
    print("👋 Shutting down")


app = FastAPI(
    title="OpenAI Hackathon API",
    description="gpt-oss-20b and gpt-oss-120b powered application via Groq",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(models.router, prefix="/api", tags=["models"])
