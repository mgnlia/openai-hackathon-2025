# OpenAI Open Model Hackathon 2025

FastAPI backend + Next.js frontend powered by **gpt-oss-20b** and **gpt-oss-120b** via Groq.

## Quick Start

```bash
# Backend
cp .env.example .env
# Add your GROQ_API_KEY
uv sync
uv run uvicorn backend.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Models
- `openai/gpt-oss-20b` — fast, ~1000 tps, 131K context, $0.075/1M input
- `openai/gpt-oss-120b` — powerful reasoning, 131K context

## API Endpoints
- `GET /health/model` — test model access live
- `POST /api/chat` — chat completion (supports streaming)
- `GET /api/models` — list available models

## Architecture
- **Backend**: FastAPI + Groq SDK (gpt-oss primary, OpenAI fallback)
- **Frontend**: Next.js 14 + Tailwind CSS
- **Deploy**: Railway (backend) + Vercel (frontend)
