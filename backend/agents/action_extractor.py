"""Action Extractor Agent — pulls action items, decisions, and deadlines."""
from __future__ import annotations
import json
from backend.agents.base import BaseAgent

SYSTEM = """You are an expert at extracting actionable information from documents.

Extract and return a JSON object with:
{
  "action_items": [
    {"task": "...", "owner": "...", "deadline": "...", "priority": "high|medium|low"}
  ],
  "decisions": ["..."],
  "deadlines": [{"item": "...", "date": "..."}],
  "risks": ["..."],
  "next_steps": ["..."]
}

If a field has no data, use an empty array. Return ONLY valid JSON, no markdown."""


class ActionExtractorAgent(BaseAgent):
    name = "action_extractor"
    description = "Extracts action items, decisions, and deadlines"

    async def run(self, text: str, filename: str = "") -> dict:
        user = f"Document: {filename}\n\n---\n{text[:12000]}"
        raw = await self._call(SYSTEM, user, temperature=0.1, max_tokens=1024)

        # Parse JSON, fallback to raw text
        try:
            # Strip markdown code fences if present
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            parsed = json.loads(clean.strip())
        except Exception:
            parsed = {"raw": raw, "parse_error": True}

        return {"agent": self.name, "result": parsed}
