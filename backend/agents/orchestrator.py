"""Orchestrator — runs all DocAgent sub-agents in parallel and merges results."""
from __future__ import annotations
import asyncio
import time
from typing import AsyncIterator
import json

from backend.agents.summarizer import SummarizerAgent
from backend.agents.action_extractor import ActionExtractorAgent
from backend.agents.risk_analyst import RiskAnalystAgent
from backend.agents.qa_agent import QAAgent


class DocOrchestrator:
    """Coordinates all agents for full document analysis."""

    def __init__(self):
        self.summarizer = SummarizerAgent()
        self.action_extractor = ActionExtractorAgent()
        self.risk_analyst = RiskAnalystAgent()
        self.qa = QAAgent()

    async def analyze(self, text: str, filename: str = "", domain: str = "general") -> dict:
        """Run summarizer + action extractor + risk analyst in parallel."""
        start = time.time()

        results = await asyncio.gather(
            self.summarizer.run(text=text, filename=filename),
            self.action_extractor.run(text=text, filename=filename),
            self.risk_analyst.run(text=text, filename=filename, domain=domain),
            return_exceptions=True,
        )

        output = {
            "filename": filename,
            "domain": domain,
            "elapsed_s": round(time.time() - start, 2),
            "agents": {},
        }

        for result in results:
            if isinstance(result, Exception):
                output["agents"]["error"] = str(result)
            else:
                output["agents"][result["agent"]] = result["result"]

        return output

    async def answer(self, text: str, question: str, filename: str = "") -> dict:
        """Answer a specific question about the document."""
        return await self.qa.run(text=text, question=question, filename=filename)

    async def stream_analyze(self, text: str, filename: str = "", domain: str = "general") -> AsyncIterator[str]:
        """Stream analysis results as SSE events, agent by agent."""
        agents = [
            ("summarizer", self.summarizer.run(text=text, filename=filename)),
            ("action_extractor", self.action_extractor.run(text=text, filename=filename)),
            ("risk_analyst", self.risk_analyst.run(text=text, filename=filename, domain=domain)),
        ]

        for agent_name, coro in agents:
            yield f"data: {json.dumps({'type': 'agent_start', 'agent': agent_name})}\n\n"
            try:
                result = await coro
                yield f"data: {json.dumps({'type': 'agent_done', 'agent': agent_name, 'result': result['result']})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'agent_error', 'agent': agent_name, 'error': str(e)})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"
