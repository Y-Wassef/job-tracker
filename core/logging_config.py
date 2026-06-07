import logging
import sys
from pathlib import Path

LOG_DIR = Path("logs")

def setup_logging(level: int = logging.INFO):
    """Setup logging configuration with console and file output"""
    LOG_DIR.mkdir(exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # File handler
    log_file = LOG_DIR / f"job-tracker.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

    return root_logger

