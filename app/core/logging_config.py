import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, "risk_service.log")


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Rotating log handler
    handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5  # 5MB/file, keep 5 backups
    )

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    # Also log to console
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    return logger
