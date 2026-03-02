"""Q&A Agent — answers questions grounded in document context."""
from __future__ import annotations
from backend.agents.base import BaseAgent

SYSTEM = """You are a precise document Q&A assistant. Answer questions ONLY using information from the provided document.

Rules:
- If the answer is in the document, provide it with a brief quote/reference
- If the answer is NOT in the document, say "This information is not in the document"
- Be concise and direct
- Use markdown for formatting when helpful
- Never hallucinate or use outside knowledge"""


class QAAgent(BaseAgent):
    name = "qa"
    description = "Answers questions grounded in document content"

    async def run(self, text: str, question: str, filename: str = "") -> dict:
        user = f"""Document: {filename}

---
{text[:14000]}
---

Question: {question}"""
        content = await self._call(SYSTEM, user, temperature=0.1, max_tokens=1024)
        return {"agent": self.name, "question": question, "result": content}
