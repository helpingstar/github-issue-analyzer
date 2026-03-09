import asyncio
import json
from pathlib import Path

from github_issue_analyzer.agent.codex import CodexAdapter
from github_issue_analyzer.models import AgentRequest


def build_request(tmp_path: Path) -> AgentRequest:
    return AgentRequest(
        owner_repo="helpingstar/example",
        issue_number=1,
        issue_title="Example issue",
        issue_body="Body",
        checkout_path=tmp_path,
        base_branch="main",
    )


def test_codex_adapter_passes_model_flag(monkeypatch, tmp_path: Path) -> None:
    captured_args: list[tuple[object, ...]] = []

    class FakeProcess:
        returncode = 0

        async def communicate(self) -> tuple[bytes, bytes]:
            return b"", b""

    async def fake_create_subprocess_exec(*args, **kwargs):
        captured_args.append(args)
        output_path = Path(args[args.index("-o") + 1])
        output_path.write_text(
            json.dumps(
                {
                    "status": "error",
                    "ready_for_estimate": False,
                    "missing_slots": [],
                    "question_specs": [],
                    "estimate": None,
                    "error_message": "forced",
                }
            ),
            encoding="utf-8",
        )
        return FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    adapter = CodexAdapter(command="codex", model="gpt-5.4")
    response = asyncio.run(
        adapter.analyze(
            build_request(tmp_path),
            clarification_timeout=300,
            estimate_timeout=300,
        )
    )

    assert response.status == "error"
    assert captured_args
    assert "-m" in captured_args[0]
    assert "gpt-5.4" in captured_args[0]


def test_codex_adapter_passes_reasoning_effort_flag(monkeypatch, tmp_path: Path) -> None:
    captured_args: list[tuple[object, ...]] = []

    class FakeProcess:
        returncode = 0

        async def communicate(self) -> tuple[bytes, bytes]:
            return b"", b""

    async def fake_create_subprocess_exec(*args, **kwargs):
        captured_args.append(args)
        output_path = Path(args[args.index("-o") + 1])
        output_path.write_text(
            json.dumps(
                {
                    "status": "error",
                    "ready_for_estimate": False,
                    "missing_slots": [],
                    "question_specs": [],
                    "estimate": None,
                    "error_message": "forced",
                }
            ),
            encoding="utf-8",
        )
        return FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    adapter = CodexAdapter(command="codex", model="gpt-5.4", reasoning_effort="medium")
    response = asyncio.run(
        adapter.analyze(
            build_request(tmp_path),
            clarification_timeout=300,
            estimate_timeout=300,
        )
    )

    assert response.status == "error"
    assert captured_args
    assert "-c" in captured_args[0]
    assert 'model_reasoning_effort="medium"' in captured_args[0]


def test_codex_adapter_omits_model_flag_when_unset(monkeypatch, tmp_path: Path) -> None:
    captured_args: list[tuple[object, ...]] = []

    class FakeProcess:
        returncode = 0

        async def communicate(self) -> tuple[bytes, bytes]:
            return b"", b""

    async def fake_create_subprocess_exec(*args, **kwargs):
        captured_args.append(args)
        output_path = Path(args[args.index("-o") + 1])
        output_path.write_text(
            json.dumps(
                {
                    "status": "error",
                    "ready_for_estimate": False,
                    "missing_slots": [],
                    "question_specs": [],
                    "estimate": None,
                    "error_message": "forced",
                }
            ),
            encoding="utf-8",
        )
        return FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    adapter = CodexAdapter(command="codex")
    response = asyncio.run(
        adapter.analyze(
            build_request(tmp_path),
            clarification_timeout=300,
            estimate_timeout=300,
        )
    )

    assert response.status == "error"
    assert captured_args
    assert "-m" not in captured_args[0]
