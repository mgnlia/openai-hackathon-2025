"""Extract text from uploaded documents."""
from __future__ import annotations
import io
from pathlib import Path

async def extract_text(filename: str, content: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return _extract_pdf(content)
    elif ext in (".docx", ".doc"):
        return _extract_docx(content)
    else:
        return content.decode("utf-8", errors="replace")

def _extract_pdf(content: bytes) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(content))
        return "\n\n".join(p.extract_text() or "" for p in reader.pages)
    except Exception as e:
        return f"[PDF extraction error: {e}]"

def _extract_docx(content: bytes) -> str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        return f"[DOCX extraction error: {e}]"
