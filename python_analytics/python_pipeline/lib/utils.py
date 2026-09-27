"""
helpers shared across scripts
بسيطه عشان ما تصير framework
"""

import logging
from pathlib import Path


def get_logger(name):
    # logger جاهز بنفس الشكل في كل الملفات
    logger = logging.getLogger(name)

    # dont add handler twice
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    return logger


def ensure_dir(path):
    # نسوي المجلد اذا مو موجود
    Path(path).mkdir(parents=True, exist_ok=True)