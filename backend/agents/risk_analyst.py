"""Risk Analyst Agent — identifies risks, red flags, and concerns in documents."""
from __future__ import annotations
from backend.agents.base import BaseAgent
from backend.config import settings

SYSTEM = """You are a senior risk analyst reviewing documents for concerns.

Analyze the document and identify:
1. **🔴 High Risks** — critical issues requiring immediate attention
2. **🟡 Medium Risks** — concerns to monitor or address
3. **🟢 Low Risks** — minor issues or observations
4. **✅ Positive Signals** — strengths and opportunities

For each risk, briefly explain: what it is, why it matters, and suggested mitigation.
Use markdown formatting. Be specific and evidence-based."""


class RiskAnalystAgent(BaseAgent):
    name = "risk_analyst"
    description = "Identifies risks, red flags, and opportunities"
    model = settings.model_powerful  # Use 120b for deeper analysis

    async def run(self, text: str, filename: str = "", domain: str = "general") -> dict:
        user = f"Document: {filename}\nDomain: {domain}\n\n---\n{text[:14000]}"
        content = await self._call(SYSTEM, user, temperature=0.2, max_tokens=1500)
        return {"agent": self.name, "result": content}
