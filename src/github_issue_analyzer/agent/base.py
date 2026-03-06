from __future__ import annotations

from abc import ABC, abstractmethod

from github_issue_analyzer.models import AgentRequest, AgentResponse


class AgentAdapter(ABC):
    @abstractmethod
    async def analyze(
        self, request: AgentRequest, *, clarification_timeout: int, estimate_timeout: int
    ) -> AgentResponse:
        raise NotImplementedError
