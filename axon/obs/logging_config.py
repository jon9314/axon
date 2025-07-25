import json
import logging
import sys
from typing import Any

from rich.logging import RichHandler


def setup_logging(level: int = logging.INFO, log_json: bool = False) -> None:
    """Configure logging for console or JSON output."""
    handler: logging.Handler
    if log_json or not sys.stderr.isatty():
        handler = logging.StreamHandler()

        class JsonFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                data: dict[str, Any] = {
                    "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
                    "level": record.levelname,
                    "name": record.name,
                    "message": record.getMessage(),
                }
                extra = getattr(record, "extra", None)
                if isinstance(extra, dict):
                    data.update(extra)
                if record.exc_info:
                    data["exc_info"] = self.formatException(record.exc_info)
                return json.dumps(data)

        handler.setFormatter(JsonFormatter())
    else:
        handler = RichHandler(rich_tracebacks=True)
        handler.setFormatter(logging.Formatter("%(message)s"))

    logging.basicConfig(level=level, handlers=[handler], force=True)
