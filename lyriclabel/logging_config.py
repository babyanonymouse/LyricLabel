import atexit
import json
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

_LOGGER_NAMESPACE = "lyriclabel"
_DEFAULT_LOG_FILENAME = "lyriclabel.log"
_MAX_BYTES = 5 * 1024 * 1024
_BACKUP_COUNT = 5
_STANDARD_RECORD_KEYS = set(logging.makeLogRecord({}).__dict__.keys())


class JsonFormatter(logging.Formatter):
    """Minimal JSON-lines formatter for file-based audit logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        for key, value in record.__dict__.items():
            if key in _STANDARD_RECORD_KEYS or key.startswith("_"):
                continue
            payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _default_log_dir() -> Path:
    state_home = os.getenv("XDG_STATE_HOME")
    if state_home:
        return Path(state_home) / "lyriclabel" / "logs"
    return Path.home() / ".local" / "state" / "lyriclabel" / "logs"


def _resolve_log_path(log_file: str | None) -> Path:
    if log_file:
        return Path(log_file).expanduser().resolve()
    return _default_log_dir() / _DEFAULT_LOG_FILENAME


def get_logger(name: str) -> logging.Logger:
    if not name.startswith(_LOGGER_NAMESPACE):
        name = f"{_LOGGER_NAMESPACE}.{name}"
    return logging.getLogger(name)


def configure_logging(
    *,
    quiet: bool = False,
    log_file: str | None = None,
    file_level: int = logging.DEBUG,
) -> Path:
    log_path = _resolve_log_path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger(_LOGGER_NAMESPACE)
    root.setLevel(logging.DEBUG)
    root.propagate = False

    # Reset handlers so repeated setup in tests/interactive sessions stays deterministic.
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
        delay=True,
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S"))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING if quiet else logging.INFO)
    console_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    atexit.register(logging.shutdown)
    root.debug("logging configured", extra={"log_path": str(log_path)})
    return log_path
