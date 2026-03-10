from __future__ import annotations

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import httpx


LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
LOG_FILENAME = "app.log"


def configure_logging(level: str = "INFO", log_root: Path | None = None) -> Path | None:
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    log_file: Path | None = None
    if log_root is not None:
        log_root.mkdir(parents=True, exist_ok=True)
        log_file = log_root / LOG_FILENAME
        handlers.append(
            TimedRotatingFileHandler(
                log_file,
                when="midnight",
                backupCount=7,
                encoding="utf-8",
                utc=True,
            )
        )

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=LOG_FORMAT,
        handlers=handlers,
        force=True,
    )
    logging.captureWarnings(True)
    return log_file


def log_exception_details(logger: logging.Logger, message: str, exc: BaseException) -> None:
    if isinstance(exc, httpx.HTTPStatusError):
        request = exc.request
        response = exc.response
        response_body = _response_body_excerpt(response)
        logger.exception(
            "%s (status=%s method=%s url=%s response=%s)",
            message,
            response.status_code,
            request.method,
            request.url,
            response_body,
        )
        return
    logger.exception(message)


def _response_body_excerpt(response: httpx.Response, limit: int = 500) -> str:
    text = response.text.strip()
    if not text:
        return "(empty)"
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."
