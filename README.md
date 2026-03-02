# 🤖 DocAgent — OpenAI Open Model Hackathon 2025

**Local-first AI document analyst** powered by **gpt-oss-20b** and **gpt-oss-120b** via Groq.

> **Category**: Local Agent | **Hackathon**: [OpenAI Open Model Hackathon](https://openai.devpost.com/) | **Deadline**: Sep 11, 2025

---

## What It Does

Upload any PDF, DOCX, or TXT document → three specialized AI agents analyze it in parallel:

| Agent | Model | Output |
|-------|-------|--------|
| 📄 Summarizer | gpt-oss-20b | TL;DR, key points, document type |
| ✅ Action Extractor | gpt-oss-20b | Tasks, owners, deadlines, decisions |
| ⚠️ Risk Analyst | gpt-oss-120b | High/medium/low risks, opportunities |

Plus **grounded Q&A** — ask anything about the document, get cited answers.

---

## Architecture

```
Frontend (Next.js 14)
    │  SSE stream + REST
    ▼
Backend (FastAPI)
    ├── /api/documents/*   — upload, analyze, Q&A
    ├── /api/agent/run     — agentic tool loop
    ├── /api/tools/*       — tool registry + direct calls
    └── /api/demo          — scripted demo flow (SSE)
         │
    ┌────┴──────────────────────┐
    │     Tool Registry          │
    │  web_search · read_url     │
    │  calculate · extract_entities │
    └────────────────────────────┘
         │
    ┌────┴──────────────────────┐
    │  Groq API                  │
    │  Chat Completions          │  ← gpt-oss-20b (fast, ~1000 tps)
    │  Responses API             │  ← gpt-oss-120b (powerful reasoning)
    │  Built-in: Browser Search  │
    │  Built-in: Code Execution  │
    └────────────────────────────┘
```

---

## Key Technical Features

### Multi-Agent Pipeline
Three agents run in **parallel** via `asyncio.gather()`. Results stream back via **SSE** as each agent completes.

### Tool Registry (Generic)
Plug-and-play tool system — register any Python function as an LLM-callable tool:
```python
from backend.tools.registry import ToolDefinition, ToolRegistry

def my_tool(query: str) -> str: ...

registry = ToolRegistry()
registry.register(ToolDefinition(my_tool, name="my_tool", ...))
result = await registry.run_tool_loop(client, model, messages)
```

### Groq Responses API
Confirmed supported for gpt-oss models — single API call with built-in Browser Search:
```python
from backend.llm import responses_api_call

result = await responses_api_call(
    input_text="Summarize this contract",
    model="openai/gpt-oss-20b",
    builtin_tools=["web_search", "browser_search"],
)
```

### Demo Mode
Scripted SSE walkthrough for video recording:
```bash
curl http://localhost:8000/api/demo          # full 5-scene demo stream
curl http://localhost:8000/api/demo/script   # JSON script with narration
```

---

## Quick Start

```bash
# 1. Clone and set up
git clone https://github.com/mgnlia/openai-hackathon-2025
cd openai-hackathon-2025
cp .env.example .env
# Add GROQ_API_KEY (free at console.groq.com)

# 2. Backend
uv sync
uv run uvicorn backend.main:app --reload
# → http://localhost:8000/docs

# 3. Frontend
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/documents/upload` | Upload PDF/DOCX/TXT |
| `POST` | `/api/documents/analyze` | Full analysis (batch) |
| `GET`  | `/api/documents/analyze/stream` | Analysis via SSE |
| `POST` | `/api/documents/qa` | Grounded Q&A |
| `GET`  | `/api/tools` | List registered tools |
| `POST` | `/api/tools/call` | Execute a tool directly |
| `POST` | `/api/agent/run` | Agentic tool loop |
| `GET`  | `/api/demo` | Scripted demo (SSE) |
| `GET`  | `/api/demo/script` | Demo script JSON |

---

## Models

| Model | Speed | Context | Best For |
|-------|-------|---------|----------|
| `openai/gpt-oss-20b` | ~1000 tps | 131K | Fast analysis, Q&A, tool use |
| `openai/gpt-oss-120b` | ~200 tps | 131K | Deep risk analysis, complex reasoning |

Both hosted on **Groq** — no local GPU required (swap to Ollama for true offline mode).

---

## Groq Capabilities for gpt-oss

- ✅ Chat Completions API
- ✅ Responses API  
- ✅ Tool Use / Function Calling
- ✅ Browser Search (built-in)
- ✅ Code Execution (built-in)
- ✅ JSON Schema Mode
- ✅ Streaming
- ✅ 131K context window

---

## Tech Stack

- **Backend**: Python 3.11, FastAPI, Groq SDK, OpenAI SDK
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Document parsing**: pypdf, python-docx
- **Deploy**: Railway (backend) + Vercel (frontend)
- **Package manager**: uv
