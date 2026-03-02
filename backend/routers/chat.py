"""Chat router — completion and streaming endpoints."""
from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.llm import chat_completion
from backend.config import settings

router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # user | assistant | system
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None  # defaults to gpt-oss-20b
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False


class ChatResponse(BaseModel):
    content: str
    model: str
    provider: str
    usage: dict


@router.post("/chat")
async def chat(req: ChatRequest):
    """Non-streaming chat completion via gpt-oss-20b (or 120b)."""
    messages = [m.model_dump() for m in req.messages]
    model = req.model or settings.model_fast

    if req.stream:
        return await _stream_response(messages, model, req.temperature, req.max_tokens)

    try:
        result = await chat_completion(
            messages=messages,
            model=model,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
        return ChatResponse(
            content=result["content"],
            model=result["model"],
            provider=result["provider"],
            usage=result["usage"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _stream_response(messages, model, temperature, max_tokens):
    """Return an SSE streaming response."""
    async def generator():
        try:
            stream = await chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            async for token in stream:
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generator(), media_type="text/event-stream")
