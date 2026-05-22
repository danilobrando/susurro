"""Central logging setup — all modules use `logger = logging.getLogger(__name__)`."""

from __future__ import annotations

import logging
import sys

from . import config


def setup(level: int = logging.INFO) -> None:
    """Configure root logger. Idempotent — safe to call multiple times."""
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handlers: list[logging.Handler] = [
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
    ]
    # Console output only when running attached to a TTY — keeps .app launches quiet.
    if sys.stdout.isatty():
        handlers.append(logging.StreamHandler())
    logging.basicConfig(level=level, format=fmt, handlers=handlers, force=True)
