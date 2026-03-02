"""Summarizer Agent — produces structured document summaries."""
from __future__ import annotations
from backend.agents.base import BaseAgent

SYSTEM = """You are an expert document analyst. Given document text, produce a structured summary with:
1. **TL;DR** (2-3 sentences max)
2. **Key Points** (bullet list, 5-7 items)
3. **Main Topics** (comma-separated tags)
4. **Document Type** (report / contract / research / email / other)

Be concise, precise, and factual. Use markdown formatting."""


class SummarizerAgent(BaseAgent):
    name = "summarizer"
    description = "Produces structured summaries of documents"

    async def run(self, text: str, filename: str = "") -> dict:
        user = f"Document: {filename}\n\n---\n{text[:12000]}"
        content = await self._call(SYSTEM, user, temperature=0.2, max_tokens=1024)
        return {"agent": self.name, "result": content}
