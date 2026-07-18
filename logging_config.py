import logging
import os
import sys
import time

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S %z"


def configure_logging() -> None:
    """Configure root logging once at application startup.

    Level is controlled by the LOG_LEVEL env var (default INFO). Timestamps use
    the local time zone (TZ env var, e.g. Asia/Jakarta).
    """
    # Apply the TZ env var to the process so log timestamps use it (Unix only).
    if hasattr(time, "tzset"):
        os.environ.setdefault("TZ", "Asia/Jakarta")
        time.tzset()

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        stream=sys.stdout,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
