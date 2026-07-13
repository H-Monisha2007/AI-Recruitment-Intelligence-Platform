"""
Structured logging configuration using Python's standard logging + JSON formatter.
Produces rotating daily log files: logs/app.log and logs/audit.log
"""
from __future__ import annotations
import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime, timezone
from contextvars import ContextVar

from app.core.config import settings

# Context variable for request-id (set by middleware)
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class JSONFormatter(logging.Formatter):
    """Render log records as single-line JSON for structured log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
            "module": record.module,
            "line": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)


def setup_logging() -> None:
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handlers: list[logging.Handler] = []

    # ── Console ───────────────────────────────────────────────────────────
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(JSONFormatter())
    handlers.append(console)

    # ── Rotating app log ──────────────────────────────────────────────────
    app_handler = logging.handlers.TimedRotatingFileHandler(
        filename=os.path.join(settings.LOG_DIR, "app.log"),
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    app_handler.setFormatter(JSONFormatter())
    handlers.append(app_handler)

    # ── Audit log (INFO+ only) ────────────────────────────────────────────
    audit_handler = logging.handlers.TimedRotatingFileHandler(
        filename=os.path.join(settings.LOG_DIR, "audit.log"),
        when="midnight",
        backupCount=90,
        encoding="utf-8",
    )
    audit_handler.setFormatter(JSONFormatter())
    audit_handler.addFilter(logging.Filter("audit"))
    handlers.append(audit_handler)

    logging.basicConfig(level=level, handlers=handlers, force=True)
    # Silence noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


audit_logger = logging.getLogger("audit")