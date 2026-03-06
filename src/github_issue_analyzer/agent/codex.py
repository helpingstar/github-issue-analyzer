from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

from pydantic import TypeAdapter

from github_issue_analyzer.agent.base import AgentAdapter
from github_issue_analyzer.models import AgentRequest, AgentResponse


class CodexAdapter(AgentAdapter):
    def __init__(self, command: str = "codex") -> None:
        self.command = command

    async def analyze(
        self, request: AgentRequest, *, clarification_timeout: int, estimate_timeout: int
    ) -> AgentResponse:
        timeout = estimate_timeout
        prompt = self._build_prompt(request)
        schema = TypeAdapter(AgentResponse).json_schema()

        for attempt in range(2):
            try:
                return await self._run(prompt=prompt, schema=schema, cwd=request.checkout_path, timeout=timeout)
            except (asyncio.TimeoutError, json.JSONDecodeError, ValueError):
                if attempt == 1:
                    raise
        raise RuntimeError("unreachable")

    async def _run(self, *, prompt: str, schema: dict, cwd: Path, timeout: int) -> AgentResponse:
        with tempfile.TemporaryDirectory(prefix="gia-codex-") as temp_dir:
            schema_path = Path(temp_dir) / "schema.json"
            output_path = Path(temp_dir) / "result.json"
            schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

            process = await asyncio.create_subprocess_exec(
                self.command,
                "exec",
                "-C",
                str(cwd),
                "-s",
                "read-only",
                "--output-schema",
                str(schema_path),
                "-o",
                str(output_path),
                prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                raise

            if process.returncode != 0:
                raise ValueError("codex exec failed")

            if not output_path.exists():
                raise ValueError("codex output file missing")

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            return AgentResponse.model_validate(payload)

    def _build_prompt(self, request: AgentRequest) -> str:
        accepted_comments = "\n".join(
            f"- {comment.author_login}: {comment.body}" for comment in request.accepted_comments
        )
        clarification_answers = "\n".join(
            f"- {line}" for line in request.clarification_answers
        )
        return f"""
You are the backend analysis agent for GitHub Issue Analyzer.

Read the local repository in a strictly read-only way.
Do not modify files.
Do not run builds or tests.
You may inspect files and use git read commands.

Repository: {request.owner_repo}
Issue number: {request.issue_number}
Base branch: {request.base_branch}

Issue title:
{request.issue_title}

Issue body:
{request.issue_body}

Accepted comments:
{accepted_comments or "(none)"}

Clarification answers:
{clarification_answers or "(none)"}

Return JSON only and follow the provided schema exactly.
""".strip()
