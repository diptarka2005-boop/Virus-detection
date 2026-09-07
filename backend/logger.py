"""Centralized file logging."""
import logging
from pathlib import Path

_LOGGER_NAME = "self_healing"


def get_logger(log_path: str | Path) -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(handler)
    return logger


def log_event(logger: logging.Logger, event: str, details: str = "") -> None:
    logger.info("%s%s", event, f" | {details}" if details else "")
