"""Base agent — shared interface for all DocAgent sub-agents."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from backend.llm import chat_completion
from backend.config import settings


class BaseAgent(ABC):
    """All agents share this interface."""

    name: str = "base"
    description: str = ""
    model: str = settings.model_fast  # gpt-oss-20b by default

    def __init__(self, model: str | None = None):
        if model:
            self.model = model

    async def run(self, **kwargs) -> dict[str, Any]:
        raise NotImplementedError

    async def _call(
        self,
        system: str,
        user: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        result = await chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return result["content"]
