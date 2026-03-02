"""
LLM client — Groq primary, OpenAI fallback.

Groq Responses API: supported for gpt-oss models (confirmed July 2025).
Groq built-in tools for gpt-oss: Browser Search, Code Execution, Web Search.
"""
from __future__ import annotations
import os
from groq import AsyncGroq
from openai import AsyncOpenAI
from backend.config import settings


def get_groq_client() -> AsyncGroq:
    api_key = settings.groq_api_key
    if not api_key:
        raise ValueError("GROQ_API_KEY not set")
    return AsyncGroq(api_key=api_key)


def get_openai_client() -> AsyncOpenAI:
    api_key = settings.openai_api_key
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    return AsyncOpenAI(api_key=api_key)


def get_groq_as_openai() -> AsyncOpenAI:
    """Use Groq via OpenAI-compatible SDK — enables Responses API syntax."""
    return AsyncOpenAI(
        api_key=settings.groq_api_key or "dummy",
        base_url="https://api.groq.com/openai/v1",
    )


async def chat_completion(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
    tools: list[dict] | None = None,
    stream: bool = False,
) -> dict:
    """Standard chat completion via Groq (falls back to OpenAI if no Groq key)."""
    model = model or settings.model_fast

    if settings.groq_api_key:
        client = get_groq_client()
        kwargs = dict(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await client.chat.completions.create(**kwargs)
        msg = response.choices[0].message
        return {
            "content": msg.content or "",
            "tool_calls": [tc.model_dump() for tc in (msg.tool_calls or [])],
            "model": model,
            "usage": response.usage.model_dump() if response.usage else {},
        }

    elif settings.openai_api_key:
        client = get_openai_client()
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return {
            "content": response.choices[0].message.content or "",
            "tool_calls": [],
            "model": model,
            "usage": response.usage.model_dump() if response.usage else {},
        }

    raise RuntimeError("No LLM API key configured. Set GROQ_API_KEY or OPENAI_API_KEY.")


# ---------------------------------------------------------------------------
# Groq Responses API wrapper (confirmed supported for gpt-oss)
# ---------------------------------------------------------------------------

GROQ_BUILTIN_TOOLS = {
    "web_search": {"type": "web_search"},
    "browser_search": {"type": "browser_search"},   # gpt-oss specific
    "code_execution": {"type": "code_execution"},
}


async def responses_api_call(
    input_text: str,
    model: str | None = None,
    builtin_tools: list[str] | None = None,
    instructions: str | None = None,
) -> dict:
    """
    Call Groq's Responses API endpoint (OpenAI Responses API compatible).
    Supports gpt-oss built-in tools: web_search, browser_search, code_execution.

    Note: Groq's Responses API is available at /openai/v1/responses
    """
    import httpx
    model = model or settings.model_fast
    api_key = settings.groq_api_key
    if not api_key:
        raise ValueError("GROQ_API_KEY required for Responses API")

    tools = []
    if builtin_tools:
        for t in builtin_tools:
            if t in GROQ_BUILTIN_TOOLS:
                tools.append(GROQ_BUILTIN_TOOLS[t])

    payload: dict = {"model": model, "input": input_text}
    if tools:
        payload["tools"] = tools
    if instructions:
        payload["instructions"] = instructions

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.groq.com/openai/v1/responses",
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        r.raise_for_status()
        data = r.json()

    # Extract text output
    output_text = ""
    for item in data.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    output_text += c.get("text", "")

    return {
        "content": output_text,
        "raw": data,
        "model": model,
        "api": "responses",
    }
