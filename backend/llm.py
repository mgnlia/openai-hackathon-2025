"""LLM client — Groq primary (gpt-oss-20b/120b), OpenAI fallback."""
from __future__ import annotations

import os
from typing import AsyncIterator

from groq import AsyncGroq
from openai import AsyncOpenAI

from backend.config import settings


def get_groq_client() -> AsyncGroq:
    return AsyncGroq(api_key=settings.groq_api_key or os.environ.get("GROQ_API_KEY", ""))


def get_openai_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=settings.openai_api_key or os.environ.get("OPENAI_API_KEY", ""))


async def chat_completion(
    messages: list[dict],
    model: str | None = None,
    stream: bool = False,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> dict | AsyncIterator:
    """
    Call gpt-oss-20b (or 120b) via Groq.
    Falls back to OpenAI if GROQ_API_KEY is not set.
    """
    model = model or settings.model_fast

    if settings.groq_api_key:
        client = get_groq_client()
        if stream:
            return await _groq_stream(client, messages, model, temperature, max_tokens)
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return {
            "content": response.choices[0].message.content,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            "provider": "groq",
        }

    # OpenAI fallback (gpt-4o if gpt-oss not available via OpenAI yet)
    client = get_openai_client()
    fallback_model = "gpt-4o-mini"
    response = await client.chat.completions.create(
        model=fallback_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return {
        "content": response.choices[0].message.content,
        "model": response.model,
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        },
        "provider": "openai_fallback",
    }


async def _groq_stream(
    client: AsyncGroq,
    messages: list[dict],
    model: str,
    temperature: float,
    max_tokens: int,
) -> AsyncIterator[str]:
    """Stream tokens from Groq."""
    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content


async def test_model_access() -> dict:
    """Test that we can reach gpt-oss-20b. Called at startup/health check."""
    try:
        result = await chat_completion(
            messages=[{"role": "user", "content": "Say 'OK' in one word."}],
            model=settings.model_fast,
            max_tokens=10,
        )
        return {
            "status": "ok",
            "model": result.get("model"),
            "provider": result.get("provider"),
            "response": result.get("content", "").strip(),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
