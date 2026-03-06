from __future__ import annotations

import asyncio
import base64
import logging
import subprocess
from pathlib import Path


logger = logging.getLogger(__name__)


class CheckoutManager:
    async def ensure_checkout(
        self,
        owner_repo: str,
        checkout_path: Path,
        default_branch: str,
        token: str,
    ) -> None:
        if checkout_path.exists() and (checkout_path / ".git").exists():
            await self.sync_checkout(owner_repo, checkout_path, default_branch, token)
            return

        checkout_path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(
            self._run_git,
            [
                "git",
                "-c",
                self._extra_header(token),
                "clone",
                "--branch",
                default_branch,
                "--single-branch",
                f"https://github.com/{owner_repo}.git",
                str(checkout_path),
            ],
        )

    async def sync_checkout(
        self,
        owner_repo: str,
        checkout_path: Path,
        default_branch: str,
        token: str,
    ) -> None:
        if not checkout_path.exists():
            await self.ensure_checkout(owner_repo, checkout_path, default_branch, token)
            return

        await asyncio.to_thread(
            self._run_git,
            [
                "git",
                "-C",
                str(checkout_path),
                "-c",
                self._extra_header(token),
                "fetch",
                "origin",
                default_branch,
                "--prune",
            ],
        )
        await asyncio.to_thread(
            self._run_git,
            [
                "git",
                "-C",
                str(checkout_path),
                "checkout",
                "-B",
                default_branch,
                f"origin/{default_branch}",
            ],
        )
        await asyncio.to_thread(
            self._run_git,
            [
                "git",
                "-C",
                str(checkout_path),
                "reset",
                "--hard",
                f"origin/{default_branch}",
            ],
        )

    async def current_head(self, checkout_path: Path) -> str:
        output = await asyncio.to_thread(
            self._run_git_capture,
            ["git", "-C", str(checkout_path), "rev-parse", "HEAD"],
        )
        return output.strip()

    async def changed_files_since(self, checkout_path: Path, base_commit: str) -> list[str]:
        output = await asyncio.to_thread(
            self._run_git_capture,
            ["git", "-C", str(checkout_path), "diff", "--name-only", f"{base_commit}..HEAD"],
        )
        return [line.strip() for line in output.splitlines() if line.strip()]

    def _extra_header(self, token: str) -> str:
        auth = base64.b64encode(f"x-access-token:{token}".encode("utf-8")).decode("ascii")
        return f"http.extraheader=AUTHORIZATION: basic {auth}"

    def _run_git(self, command: list[str]) -> None:
        logger.debug("running git command", extra={"argv0": command[0], "args": command[1:4]})
        subprocess.run(command, check=True, capture_output=True, text=True)

    def _run_git_capture(self, command: list[str]) -> str:
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
        return completed.stdout
