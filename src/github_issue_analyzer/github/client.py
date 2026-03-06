from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import quote

import httpx

from github_issue_analyzer.branding import BOT_NAME
from github_issue_analyzer.github.auth import GitHubAppAuth


class GitHubClient:
    def __init__(self, auth: GitHubAppAuth, api_base_url: str) -> None:
        self.auth = auth
        self.api_base_url = api_base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.api_base_url,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": BOT_NAME,
            },
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        owner: str,
        repo: str,
        path: str,
        *,
        installation_id: int | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | list[Any] | None = None,
    ) -> httpx.Response:
        if installation_id is None:
            installation_id = await self.auth.get_installation_id(owner, repo)
        token = await self.auth.get_installation_token(installation_id)
        headers = {"Authorization": f"Bearer {token}"}
        response = await self._client.request(
            method,
            path,
            headers=headers,
            params=params,
            json=json,
        )
        response.raise_for_status()
        return response

    async def get_repo(self, owner: str, repo: str, installation_id: int | None = None) -> dict[str, Any]:
        response = await self._request("GET", owner, repo, f"/repos/{owner}/{repo}", installation_id=installation_id)
        return response.json()

    async def list_updated_issues(
        self,
        owner: str,
        repo: str,
        *,
        installation_id: int | None = None,
        since: datetime | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "state": "all",
            "sort": "updated",
            "direction": "desc",
            "per_page": 100,
        }
        if since is not None:
            params["since"] = since.isoformat().replace("+00:00", "Z")
        response = await self._request(
            "GET",
            owner,
            repo,
            f"/repos/{owner}/{repo}/issues",
            installation_id=installation_id,
            params=params,
        )
        issues = response.json()
        return [issue for issue in issues if "pull_request" not in issue]

    async def get_issue(
        self, owner: str, repo: str, issue_number: int, installation_id: int | None = None
    ) -> dict[str, Any]:
        response = await self._request(
            "GET",
            owner,
            repo,
            f"/repos/{owner}/{repo}/issues/{issue_number}",
            installation_id=installation_id,
        )
        return response.json()

    async def list_issue_comments(
        self, owner: str, repo: str, issue_number: int, installation_id: int | None = None
    ) -> list[dict[str, Any]]:
        response = await self._request(
            "GET",
            owner,
            repo,
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            installation_id=installation_id,
            params={"per_page": 100, "sort": "created", "direction": "asc"},
        )
        return response.json()

    async def get_issue_comment(
        self, owner: str, repo: str, comment_id: int, installation_id: int | None = None
    ) -> dict[str, Any]:
        response = await self._request(
            "GET",
            owner,
            repo,
            f"/repos/{owner}/{repo}/issues/comments/{comment_id}",
            installation_id=installation_id,
        )
        return response.json()

    async def create_issue_comment(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        body: str,
        installation_id: int | None = None,
    ) -> dict[str, Any]:
        response = await self._request(
            "POST",
            owner,
            repo,
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            installation_id=installation_id,
            json={"body": body},
        )
        return response.json()

    async def update_issue_comment(
        self,
        owner: str,
        repo: str,
        comment_id: int,
        body: str,
        installation_id: int | None = None,
    ) -> dict[str, Any]:
        response = await self._request(
            "PATCH",
            owner,
            repo,
            f"/repos/{owner}/{repo}/issues/comments/{comment_id}",
            installation_id=installation_id,
            json={"body": body},
        )
        return response.json()

    async def list_repo_labels(
        self, owner: str, repo: str, installation_id: int | None = None
    ) -> list[dict[str, Any]]:
        response = await self._request(
            "GET",
            owner,
            repo,
            f"/repos/{owner}/{repo}/labels",
            installation_id=installation_id,
            params={"per_page": 100},
        )
        return response.json()

    async def create_label(
        self,
        owner: str,
        repo: str,
        name: str,
        color: str,
        description: str,
        installation_id: int | None = None,
    ) -> dict[str, Any]:
        response = await self._request(
            "POST",
            owner,
            repo,
            f"/repos/{owner}/{repo}/labels",
            installation_id=installation_id,
            json={"name": name, "color": color, "description": description},
        )
        return response.json()

    async def add_labels_to_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        labels: list[str],
        installation_id: int | None = None,
    ) -> None:
        await self._request(
            "POST",
            owner,
            repo,
            f"/repos/{owner}/{repo}/issues/{issue_number}/labels",
            installation_id=installation_id,
            json={"labels": labels},
        )

    async def remove_label_from_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        label_name: str,
        installation_id: int | None = None,
    ) -> None:
        encoded = quote(label_name, safe="")
        response = await self._request(
            "DELETE",
            owner,
            repo,
            f"/repos/{owner}/{repo}/issues/{issue_number}/labels/{encoded}",
            installation_id=installation_id,
        )
        if response.status_code not in (200, 204):
            response.raise_for_status()
