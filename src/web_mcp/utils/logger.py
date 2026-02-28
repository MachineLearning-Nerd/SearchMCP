import json
import logging
import sys
from collections.abc import MutableMapping
from datetime import UTC, datetime
from logging import LogRecord
from typing import Any


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs logs in a structured format."""

    def __init__(self, json_format: bool = False):
        self.json_format = json_format
        super().__init__()

    def format(self, record: LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        extra_fields = {
            k: v
            for k, v in record.__dict__.items()
            if k
            not in {
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "message",
                "asctime",
            }
        }
        if extra_fields:
            log_data["extra"] = extra_fields

        if self.json_format:
            return json.dumps(log_data, default=str)
        else:
            return f"[{log_data['timestamp']}] {log_data['level']:8} | {log_data['module']:20} | {log_data['message']}"


def setup_logging(
    level: str = "INFO", json_format: bool = False, name: str = "web_mcp"
) -> logging.Logger:
    """
    Configure structured logging for the Web MCP server.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: If True, output logs in JSON format for production
        name: Logger name, defaults to 'web_mcp'

    Returns:
        Configured logger instance
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if logger.handlers:
        logger.handlers.clear()

    # MCP stdio protocol uses stdout for JSON-RPC frames. Keep logs on stderr.
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(log_level)

    formatter = StructuredFormatter(json_format=json_format)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def get_logger(name: str = "web_mcp") -> logging.Logger:
    """
    Get an existing logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter[logging.Logger]):
    """Adapter that adds extra context to log records."""

    def process(
        self, msg: str, kwargs: MutableMapping[str, Any]
    ) -> tuple[str, MutableMapping[str, Any]]:
        extra = kwargs.get("extra", {})
        extra.update(self.extra or {})
        kwargs["extra"] = extra
        return msg, kwargs
