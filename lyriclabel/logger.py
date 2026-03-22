"""Centralised logger for LyricLabel.

All modules should import and use ``get_logger()`` instead of calling
``print()`` directly.  Log files are written to ``logs/lyriclabel.log``
(relative to the project root) with automatic rotation.
"""

import logging
import logging.handlers
import os

_ROOT_LOGGER_NAME = "lyriclabel"
_LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
_LOG_FILE = os.path.join(_LOG_DIR, "lyriclabel.log")

# 5 MB per file, keep the last 3 rotated archives
_MAX_BYTES = 5 * 1024 * 1024
_BACKUP_COUNT = 3


def _configure_root_logger() -> None:
    """Attach handlers to the root 'lyriclabel' logger (once only)."""
    root = logging.getLogger(_ROOT_LOGGER_NAME)
    if root.handlers:
        return  # Already configured

    root.setLevel(logging.DEBUG)

    # ------------------------------------------------------------------
    # Rotating file handler
    # ------------------------------------------------------------------
    os.makedirs(_LOG_DIR, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        _LOG_FILE, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    root.addHandler(file_handler)

    # ------------------------------------------------------------------
    # Console (stream) handler
    # ------------------------------------------------------------------
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    root.addHandler(console_handler)


def get_logger(name: str = _ROOT_LOGGER_NAME) -> logging.Logger:
    """Return a logger for *name* under the 'lyriclabel' hierarchy.

    Handlers are attached only to the root 'lyriclabel' logger; child
    loggers (e.g. 'lyriclabel.meta_fetcher') inherit them via propagation
    so messages are never duplicated.

    Calling this function multiple times for the same *name* is safe.
    """
    _configure_root_logger()

    # Ensure the requested name is within the lyriclabel namespace
    if name != _ROOT_LOGGER_NAME and not name.startswith(_ROOT_LOGGER_NAME + "."):
        name = f"{_ROOT_LOGGER_NAME}.{name}"

    logger = logging.getLogger(name)
    # Child loggers must NOT have their own handlers — they propagate up
    logger.propagate = True
    return logger

