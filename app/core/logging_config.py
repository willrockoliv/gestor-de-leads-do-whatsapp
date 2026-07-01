import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Structured JSON formatter for app logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        # Preserve common contextual fields when provided via logger extra.
        for key in ("tenant_id", "lead_id", "session_id", "request_id", "path", "method"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value

        # Preserve primitive extra fields for structured observability metrics.
        reserved = {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName", "processName",
            "process", "taskName", "message", "asctime",
        }
        for key, value in record.__dict__.items():
            if key in reserved or key.startswith("_"):
                continue
            if key in payload:
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                payload[key] = value

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(use_json: bool, level: str = "INFO") -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())

    # Reset default handlers so uvicorn/app logs share the same formatter.
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler()
    if use_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )

    root.addHandler(handler)
