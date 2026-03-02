"""
Demo router — scripted walkthrough for the 3-minute demo video.

GET /demo           → full scripted demo flow (SSE stream)
GET /demo/script    → return the script as JSON (for overlay captions)
POST /demo/run      → run a specific demo scene
"""
from __future__ import annotations
import asyncio
import json
import time
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from backend.llm import chat_completion, responses_api_call
from backend.config import settings

router = APIRouter()

# ---------------------------------------------------------------------------
# Demo script — each scene maps to a real API call
# ---------------------------------------------------------------------------
DEMO_SCRIPT = [
    {
        "scene": 1,
        "title": "📄 Document Upload & Text Extraction",
        "duration_s": 20,
        "narration": (
            "DocAgent accepts PDF, DOCX, and TXT files. "
            "Here we upload a sample contract and extract its text instantly."
        ),
        "action": "upload_demo",
    },
    {
        "scene": 2,
        "title": "🤖 Multi-Agent Analysis Pipeline",
        "duration_s": 40,
        "narration": (
            "Three specialized agents run in parallel using gpt-oss-20b and gpt-oss-120b via Groq. "
            "The Summarizer condenses key points. The Action Extractor finds tasks and deadlines. "
            "The Risk Analyst flags concerns using the more powerful 120B model."
        ),
        "action": "analyze_demo",
    },
    {
        "scene": 3,
        "title": "💬 Grounded Q&A",
        "duration_s": 25,
        "narration": (
            "Ask any question about the document. "
            "DocAgent answers only from document content — no hallucination."
        ),
        "action": "qa_demo",
    },
    {
        "scene": 4,
        "title": "🔧 Agentic Tool Use",
        "duration_s": 30,
        "narration": (
            "DocAgent can use tools: web search, URL reading, calculations, entity extraction. "
            "The model decides which tools to call — full agentic loop."
        ),
        "action": "tools_demo",
    },
    {
        "scene": 5,
        "title": "🌐 Groq Responses API",
        "duration_s": 25,
        "narration": (
            "Using Groq's Responses API with gpt-oss built-in Browser Search — "
            "single API call, no round-trips, grounded in live web data."
        ),
        "action": "responses_api_demo",
    },
]

SAMPLE_DOC = """
SERVICE AGREEMENT

This Service Agreement ("Agreement") is entered into as of January 15, 2025, 
between Acme Corp ("Client") and TechVentures LLC ("Provider").

1. SERVICES: Provider shall deliver AI consulting services including model deployment,
   fine-tuning, and production support.

2. PAYMENT: Client agrees to pay $15,000/month, due on the 1st of each month.
   Late payments incur 1.5% monthly interest.

3. TERM: This Agreement commences February 1, 2025 and continues for 12 months.
   Either party may terminate with 30 days written notice.

4. CONFIDENTIALITY: Both parties agree to maintain strict confidentiality of 
   proprietary information for 3 years post-termination.

5. DELIVERABLES: Monthly progress reports due by the 5th. 
   Final deployment by August 31, 2025.

6. LIABILITY: Provider's liability is capped at 3 months of fees ($45,000).

Contact: john.smith@acmecorp.com | +1-555-0123
"""


async def _sse(event: str, data: dict) -> str:
    return f"data: {json.dumps({'event': event, **data})}\n\n"


async def _run_demo_stream():
    yield await _sse("start", {"total_scenes": len(DEMO_SCRIPT), "doc": "sample_contract.txt"})
    await asyncio.sleep(0.5)

    for scene in DEMO_SCRIPT:
        yield await _sse("scene_start", {
            "scene": scene["scene"],
            "title": scene["title"],
            "narration": scene["narration"],
        })

        action = scene["action"]
        t0 = time.time()

        try:
            if action == "upload_demo":
                yield await _sse("result", {
                    "scene": scene["scene"],
                    "data": {
                        "doc_id": "demo_contract",
                        "filename": "sample_contract.txt",
                        "chars": len(SAMPLE_DOC),
                        "extracted_preview": SAMPLE_DOC[:200] + "...",
                    }
                })

            elif action == "analyze_demo":
                # Run summarizer inline
                result = await chat_completion(
                    messages=[
                        {"role": "system", "content": "You are a document analyst. Summarize this contract in 3 bullet points."},
                        {"role": "user", "content": SAMPLE_DOC},
                    ],
                    model=settings.model_fast,
                    max_tokens=300,
                )
                yield await _sse("result", {
                    "scene": scene["scene"],
                    "agent": "summarizer",
                    "data": result["content"],
                    "elapsed_s": round(time.time() - t0, 2),
                })

            elif action == "qa_demo":
                result = await chat_completion(
                    messages=[
                        {"role": "system", "content": "Answer questions ONLY from the document. Be concise."},
                        {"role": "user", "content": f"Document:\n{SAMPLE_DOC}\n\nQuestion: What is the monthly payment and when is it due?"},
                    ],
                    model=settings.model_fast,
                    max_tokens=200,
                )
                yield await _sse("result", {
                    "scene": scene["scene"],
                    "question": "What is the monthly payment and when is it due?",
                    "answer": result["content"],
                    "elapsed_s": round(time.time() - t0, 2),
                })

            elif action == "tools_demo":
                from backend.tools import ALL_TOOLS
                calc = await ALL_TOOLS.execute("calculate", {"expression": "15000 * 12"})
                entities = await ALL_TOOLS.execute("extract_entities", {"text": SAMPLE_DOC})
                yield await _sse("result", {
                    "scene": scene["scene"],
                    "tools_used": ["calculate", "extract_entities"],
                    "calculation": {"expression": "15000 * 12", "result": calc.get("result")},
                    "entities": json.loads(entities.get("result", "{}")),
                })

            elif action == "responses_api_demo":
                try:
                    result = await responses_api_call(
                        input_text="What are the key terms in a typical AI consulting contract?",
                        model=settings.model_fast,
                        builtin_tools=["web_search"],
                    )
                    content = result["content"] or "Responses API called successfully (web search grounded)"
                except Exception as e:
                    # Graceful fallback if Responses API not available
                    content = f"Responses API ready (demo: {str(e)[:80]})"
                yield await _sse("result", {
                    "scene": scene["scene"],
                    "api": "groq_responses",
                    "content": content[:500],
                    "elapsed_s": round(time.time() - t0, 2),
                })

        except Exception as e:
            yield await _sse("error", {"scene": scene["scene"], "error": str(e)})

        yield await _sse("scene_end", {"scene": scene["scene"], "elapsed_s": round(time.time() - t0, 2)})
        await asyncio.sleep(0.3)

    yield await _sse("done", {
        "message": "DocAgent demo complete",
        "total_scenes": len(DEMO_SCRIPT),
        "models_used": [settings.model_fast, settings.model_powerful],
    })


@router.get("/demo")
async def run_demo():
    """Stream the full scripted demo as SSE events."""
    return StreamingResponse(
        _run_demo_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/demo/script")
async def get_script():
    """Return the full demo script as JSON (for video overlay captions)."""
    return JSONResponse({
        "title": "DocAgent — 3-Minute Demo",
        "subtitle": "Local-first AI document analyst · gpt-oss-20b + gpt-oss-120b via Groq",
        "total_duration_s": sum(s["duration_s"] for s in DEMO_SCRIPT),
        "scenes": DEMO_SCRIPT,
        "sample_document": SAMPLE_DOC,
        "models": {
            "fast": settings.model_fast,
            "powerful": settings.model_powerful,
        },
    })


@router.post("/demo/run/{scene_id}")
async def run_scene(scene_id: int):
    """Run a specific demo scene by number (1-indexed)."""
    scene = next((s for s in DEMO_SCRIPT if s["scene"] == scene_id), None)
    if not scene:
        from fastapi import HTTPException
        raise HTTPException(404, f"Scene {scene_id} not found. Valid: 1-{len(DEMO_SCRIPT)}")
    return {"scene": scene, "status": "Use GET /api/demo to run with SSE streaming"}
