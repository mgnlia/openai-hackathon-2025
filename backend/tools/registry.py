"""
Tool Registry — register Python functions as LLM-callable tools.

Usage:
    @tool(name="search_web", description="Search the web for information")
    async def search_web(query: str) -> str:
        ...

    registry = ToolRegistry()
    registry.register(search_web)
    schema = registry.to_openai_schema()   # pass to chat completion
    result = await registry.execute("search_web", {"query": "..."})
"""
from __future__ import annotations
import asyncio
import inspect
import json
import logging
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)


class ToolDefinition:
    """Wraps a callable with its LLM-facing schema."""

    def __init__(
        self,
        fn: Callable,
        name: str,
        description: str,
        parameters: dict,
    ):
        self.fn = fn
        self.name = name
        self.description = description
        self.parameters = parameters
        self.is_async = asyncio.iscoroutinefunction(fn)

    def to_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    async def execute(self, arguments: dict) -> Any:
        if self.is_async:
            return await self.fn(**arguments)
        return self.fn(**arguments)


class ToolRegistry:
    """Central registry of all available tools."""

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool_def: ToolDefinition) -> None:
        self._tools[tool_def.name] = tool_def
        logger.debug(f"Registered tool: {tool_def.name}")

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def to_openai_schema(self, names: list[str] | None = None) -> list[dict]:
        """Return OpenAI-format tool schemas, optionally filtered by name."""
        tools = self._tools.values()
        if names:
            tools = [t for t in tools if t.name in names]
        return [t.to_openai_schema() for t in tools]

    async def execute(self, name: str, arguments: dict | str) -> dict:
        """Execute a tool by name, return structured result."""
        tool_def = self._tools.get(name)
        if not tool_def:
            return {"error": f"Unknown tool: {name}", "tool": name}

        # arguments may arrive as JSON string from LLM
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                return {"error": "Invalid JSON arguments", "tool": name}

        try:
            result = await tool_def.execute(arguments)
            return {"tool": name, "result": result, "ok": True}
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return {"tool": name, "error": str(e), "ok": False}

    async def run_tool_loop(
        self,
        client,
        model: str,
        messages: list[dict],
        tool_names: list[str] | None = None,
        max_iterations: int = 5,
        temperature: float = 0.2,
    ) -> dict:
        """
        Agentic tool loop — keeps calling the LLM until it stops requesting tools
        or hits max_iterations. Compatible with OpenAI/Groq chat completions.
        """
        tools_schema = self.to_openai_schema(tool_names)
        current_messages = list(messages)
        iterations = 0

        while iterations < max_iterations:
            iterations += 1
            response = await client.chat.completions.create(
                model=model,
                messages=current_messages,
                tools=tools_schema if tools_schema else None,
                tool_choice="auto" if tools_schema else None,
                temperature=temperature,
            )

            choice = response.choices[0]
            msg = choice.message
            current_messages.append(msg.model_dump(exclude_none=True))

            # No tool calls — we have the final answer
            if not msg.tool_calls:
                return {
                    "content": msg.content,
                    "iterations": iterations,
                    "messages": current_messages,
                }

            # Execute all requested tool calls in parallel
            tool_results = await asyncio.gather(*[
                self.execute(tc.function.name, tc.function.arguments)
                for tc in msg.tool_calls
            ])

            # Append tool results to messages
            for tc, result in zip(msg.tool_calls, tool_results):
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result.get("result", result)),
                })

        # Max iterations hit — return last message content
        last = current_messages[-1]
        return {
            "content": last.get("content", "Max tool iterations reached."),
            "iterations": iterations,
            "messages": current_messages,
            "truncated": True,
        }

    def list(self) -> list[dict]:
        return [
            {"name": t.name, "description": t.description}
            for t in self._tools.values()
        ]


def tool(name: str, description: str, parameters: dict | None = None):
    """Decorator to register a function as a tool."""
    def decorator(fn: Callable) -> ToolDefinition:
        params = parameters or _infer_parameters(fn)
        return ToolDefinition(fn=fn, name=name, description=description, parameters=params)
    return decorator


def _infer_parameters(fn: Callable) -> dict:
    """Basic parameter inference from function signature + annotations."""
    sig = inspect.signature(fn)
    props = {}
    required = []
    type_map = {str: "string", int: "integer", float: "number", bool: "boolean"}

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue
        ann = param.annotation
        json_type = type_map.get(ann, "string")
        props[param_name] = {"type": json_type}
        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    return {"type": "object", "properties": props, "required": required}
