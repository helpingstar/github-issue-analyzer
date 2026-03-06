from __future__ import annotations

from github_issue_analyzer.models import RepoConfig
from github_issue_analyzer.workflow.service import WorkflowService


class RefreshService:
    def __init__(self, workflow_service: WorkflowService) -> None:
        self.workflow_service = workflow_service

    async def run(self, repo: RepoConfig, issue_number: int) -> None:
        await self.workflow_service.process_issue(repo, issue_number, force_refresh=True)
