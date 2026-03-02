"""Configuration — model providers and settings."""
from __future__ import annotations
import os
from pydantic import BaseModel


class Settings(BaseModel):
    # Groq (primary — hosts gpt-oss models)
    groq_api_key: str = ""
    # OpenAI (fallback)
    openai_api_key: str = ""

    # Default models
    model_fast: str = "openai/gpt-oss-20b"
    model_powerful: str = "openai/gpt-oss-120b"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            model_fast=os.getenv("MODEL_FAST", "openai/gpt-oss-20b"),
            model_powerful=os.getenv("MODEL_POWERFUL", "openai/gpt-oss-120b"),
        )


settings = Settings.from_env()
