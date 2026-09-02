# ---
# purpose: configure a rotating file logger under the data dir plus console output
# exports: setup(), get_logger()
# depends: paths.py
# ---
from __future__ import annotations

import logging
import logging.handlers

from . import paths

_LOGGER_NAME = "obm"


def setup(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:
        return logger
    logger.setLevel(level)

    paths.ensure_data_dir()
    log_path = paths.data_dir() / "obm.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    console_handler = logging.StreamHandler()

    fmt = logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
    file_handler.setFormatter(fmt)
    console_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


def get_logger(name: str = _LOGGER_NAME) -> logging.Logger:
    return logging.getLogger(name)
