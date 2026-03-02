"""
Built-in tool definitions for DocAgent.

Groq natively supports: Browser Search, Code Execution, Web Search for gpt-oss models.
These definitions also serve as local fallbacks / explicit function-calling schemas.
"""
from __future__ import annotations
import json
import httpx
from backend.tools.registry import ToolRegistry, ToolDefinition


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

async def web_search_impl(query: str, max_results: int = 5) -> str:
    """Search the web via DuckDuckGo Instant Answer API (no key required)."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            )
            data = r.json()
            results = []
            if data.get("AbstractText"):
                results.append(f"Summary: {data['AbstractText']}")
            for topic in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append(f"- {topic['Text']}")
            return "\n".join(results) if results else f"No results found for: {query}"
    except Exception as e:
        return f"Search error: {e}"


async def read_url_impl(url: str) -> str:
    """Fetch and return the text content of a URL."""
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            r = await client.get(url, headers={"User-Agent": "DocAgent/1.0"})
            r.raise_for_status()
            # Strip HTML tags crudely
            import re
            text = re.sub(r"<[^>]+>", " ", r.text)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:4000]  # Limit to 4K chars
    except Exception as e:
        return f"URL fetch error: {e}"


async def calculate_impl(expression: str) -> str:
    """Safely evaluate a mathematical expression."""
    import ast, operator
    allowed_ops = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.USub: operator.neg,
        ast.Mod: operator.mod,
    }
    def _eval(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            op = allowed_ops.get(type(node.op))
            if not op:
                raise ValueError(f"Unsupported operator: {node.op}")
            return op(_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            op = allowed_ops.get(type(node.op))
            return op(_eval(node.operand))
        raise ValueError(f"Unsupported expression: {node}")
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval(tree.body)
        return str(result)
    except Exception as e:
        return f"Calculation error: {e}"


async def extract_entities_impl(text: str) -> str:
    """Extract named entities from text using simple pattern matching."""
    import re
    entities: dict[str, list[str]] = {
        "emails": re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text),
        "urls": re.findall(r"https?://[^\s<>\"]+", text),
        "dates": re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b", text),
        "amounts": re.findall(r"\$[\d,]+(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:USD|EUR|GBP|million|billion)\b", text),
        "phone_numbers": re.findall(r"\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b", text),
    }
    return json.dumps({k: list(set(v)) for k, v in entities.items() if v}, indent=2)


async def summarize_key_numbers_impl(text: str) -> str:
    """Extract and summarize all numerical data from text."""
    import re
    numbers = re.findall(r"(?:[$€£]?\d+(?:[.,]\d+)*(?:\s*(?:million|billion|thousand|%|percent))?)", text)
    unique = list(dict.fromkeys(numbers))[:30]
    return json.dumps({"numbers_found": unique, "count": len(unique)})


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

def _make_tool(fn, name: str, description: str, parameters: dict) -> ToolDefinition:
    return ToolDefinition(fn=fn, name=name, description=description, parameters=parameters)


ALL_TOOLS_LIST: list[ToolDefinition] = [
    _make_tool(
        web_search_impl, "web_search",
        "Search the web for current information on any topic",
        {"type": "object", "properties": {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {"type": "integer", "description": "Max results (default 5)", "default": 5},
        }, "required": ["query"]},
    ),
    _make_tool(
        read_url_impl, "read_url",
        "Fetch and read the text content of a web page URL",
        {"type": "object", "properties": {
            "url": {"type": "string", "description": "URL to fetch"},
        }, "required": ["url"]},
    ),
    _make_tool(
        calculate_impl, "calculate",
        "Evaluate a mathematical expression (supports +, -, *, /, **, %)",
        {"type": "object", "properties": {
            "expression": {"type": "string", "description": "Math expression, e.g. '(100 * 1.15) / 12'"},
        }, "required": ["expression"]},
    ),
    _make_tool(
        extract_entities_impl, "extract_entities",
        "Extract emails, URLs, dates, amounts, and phone numbers from text",
        {"type": "object", "properties": {
            "text": {"type": "string", "description": "Text to extract entities from"},
        }, "required": ["text"]},
    ),
    _make_tool(
        summarize_key_numbers_impl, "summarize_numbers",
        "Extract and list all numerical values and amounts from text",
        {"type": "object", "properties": {
            "text": {"type": "string", "description": "Text to extract numbers from"},
        }, "required": ["text"]},
    ),
]

# Build default registry
ALL_TOOLS = ToolRegistry()
for t in ALL_TOOLS_LIST:
    ALL_TOOLS.register(t)
