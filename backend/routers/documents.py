"""Documents router — upload, analyze, Q&A."""
from __future__ import annotations
import json
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.document.extractor import extract_text
from backend.agents.orchestrator import DocOrchestrator

router = APIRouter()
orchestrator = DocOrchestrator()

# In-memory store (replace with Redis/DB for production)
_docs: dict[str, dict] = {}

class QARequest(BaseModel):
    doc_id: str
    question: str

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    domain: str = Form(default="general"),
):
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 10MB)")
    text = await extract_text(file.filename or "document", content)
    if not text.strip():
        raise HTTPException(400, "Could not extract text from document")
    doc_id = f"doc_{len(_docs)+1}_{file.filename}"
    _docs[doc_id] = {"filename": file.filename, "text": text, "domain": domain, "size": len(content)}
    return {"doc_id": doc_id, "filename": file.filename, "chars": len(text), "domain": domain}

@router.post("/documents/analyze")
async def analyze_document(doc_id: str, domain: str = "general"):
    doc = _docs.get(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    result = await orchestrator.analyze(text=doc["text"], filename=doc["filename"], domain=domain)
    return result

@router.get("/documents/analyze/stream")
async def analyze_stream(doc_id: str, domain: str = "general"):
    doc = _docs.get(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return StreamingResponse(
        orchestrator.stream_analyze(text=doc["text"], filename=doc["filename"], domain=domain),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

@router.post("/documents/qa")
async def question_answer(req: QARequest):
    doc = _docs.get(req.doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    result = await orchestrator.answer(text=doc["text"], question=req.question, filename=doc["filename"])
    return result

@router.get("/documents/list")
async def list_documents():
    return [{"doc_id": k, "filename": v["filename"], "chars": len(v["text"]), "domain": v["domain"]} for k, v in _docs.items()]
