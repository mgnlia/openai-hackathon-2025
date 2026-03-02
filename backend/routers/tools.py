"""Tools router — agentic tool-use endpoint + tool registry introspection."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.tools import ALL_TOOLS
from backend.llm import get_groq_client, responses_api_call, chat_completion
from backend.config import settings

router = APIRouter()


class AgentRequest(BaseModel):
    message: str
    tool_names: list[str] | None = None   # None = all tools
    model: str | None = None
    max_iterations: int = 5
    use_responses_api: bool = False        # Use Groq Responses API instead


class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: dict


@router.get("/tools")
async def list_tools():
    """List all registered tools."""
    return {"tools": ALL_TOOLS.list()}


@router.post("/tools/call")
async def call_tool(req: ToolCallRequest):
    """Execute a single tool directly."""
    result = await ALL_TOOLS.execute(req.tool_name, req.arguments)
    if not result.get("ok", True) and "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.post("/agent/run")
async def run_agent(req: AgentRequest):
    """
    Run the agentic tool loop — model decides which tools to call.

    If use_responses_api=True, uses Groq's Responses API with built-in tools
    (web_search, browser_search, code_execution) — no round-trip needed.
    """
    model = req.model or settings.model_fast

    # Option A: Groq Responses API (built-in tools, single call)
    if req.use_responses_api:
        builtin = req.tool_names or ["web_search", "browser_search"]
        result = await responses_api_call(
            input_text=req.message,
            model=model,
            builtin_tools=builtin,
            instructions="You are DocAgent, a helpful AI assistant. Use tools when needed.",
        )
        return {
            "content": result["content"],
            "api": "responses",
            "model": model,
        }

    # Option B: Chat completions + local tool loop
    client = get_groq_client()
    messages = [
        {
            "role": "system",
            "content": (
                "You are DocAgent, a helpful AI assistant with access to tools. "
                "Use tools when you need current information or calculations. "
                "Always provide a clear final answer."
            ),
        },
        {"role": "user", "content": req.message},
    ]

    result = await ALL_TOOLS.run_tool_loop(
        client=client,
        model=model,
        messages=messages,
        tool_names=req.tool_names,
        max_iterations=req.max_iterations,
    )
    return {
        "content": result["content"],
        "iterations": result["iterations"],
        "truncated": result.get("truncated", False),
        "api": "chat_completions",
        "model": model,
    }
