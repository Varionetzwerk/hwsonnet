"""Centralized logging configuration for HWSonnet."""

import logging
import sys
from pathlib import Path


def setup_logger(name: str = "hwsonnet", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    log_dir = Path.home() / ".local" / "share" / "hwsonnet"
    log_dir.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(log_dir / "hwsonnet.log")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


logger = setup_logger()
