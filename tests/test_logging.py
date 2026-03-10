import logging
from pathlib import Path

import httpx
import pytest

from github_issue_analyzer import cli
from github_issue_analyzer.logging import LOG_FILENAME, configure_logging


def _flush_handlers() -> None:
    for handler in logging.getLogger().handlers:
        handler.flush()


def _read_log_file(log_root: Path) -> str:
    return (log_root / LOG_FILENAME).read_text(encoding="utf-8")


def test_configure_logging_writes_to_rotating_log_file(tmp_path: Path) -> None:
    log_file = configure_logging("INFO", tmp_path)

    logging.getLogger("github_issue_analyzer.test").info("hello file logging")
    _flush_handlers()

    assert log_file == tmp_path / LOG_FILENAME
    assert "hello file logging" in _read_log_file(tmp_path)


def test_run_with_exception_logging_records_http_error_details(tmp_path: Path) -> None:
    configure_logging("INFO", tmp_path)
    request = httpx.Request("GET", "https://api.github.com/repos/helpingstar/example/issues")
    response = httpx.Response(502, request=request, text="Bad Gateway")

    def fail() -> None:
        raise httpx.HTTPStatusError("upstream failed", request=request, response=response)

    with pytest.raises(httpx.HTTPStatusError):
        cli._run_with_exception_logging("worker", fail)

    _flush_handlers()
    content = _read_log_file(tmp_path)
    assert "worker command failed" in content
    assert "status=502" in content
    assert "method=GET" in content
    assert "Bad Gateway" in content
    assert "Traceback" in content
