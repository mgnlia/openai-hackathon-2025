"""Configuration — loaded from environment variables."""
from __future__ import annotations
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Keys
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Models
    model_fast: str = os.getenv("MODEL_FAST", "openai/gpt-oss-20b")
    model_powerful: str = os.getenv("MODEL_POWERFUL", "openai/gpt-oss-120b")

    # Server
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", "8000"))

    # Groq API info
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_responses_url: str = "https://api.groq.com/openai/v1/responses"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
