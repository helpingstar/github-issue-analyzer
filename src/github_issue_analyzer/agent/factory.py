from __future__ import annotations

from github_issue_analyzer.agent.base import AgentAdapter
from github_issue_analyzer.agent.codex import CodexAdapter


def build_agent_adapter(backend: str) -> AgentAdapter:
    normalized = backend.lower()
    if normalized == "codex":
        return CodexAdapter()
    raise RuntimeError(f"Unsupported agent backend: {backend}")
