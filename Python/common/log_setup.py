"""Gateway log initialization module."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(log_file: str = "gateLogs.log", log_dir: Optional[Path] = None) -> logging.Logger:
    """Initialize gateway log system.

    Output to both file and console, using standard format.

    Args:
        log_file: Log file name.
        log_dir: Log file directory, defaults to current directory.

    Returns:
        Root logger instance.
    """
    if log_dir is None:
        log_dir = Path.cwd()

    log_path = log_dir / log_file
    formatter = logging.Formatter(
        "[%(asctime)s][%(levelname)s][%(name)s][%(filename)s:%(lineno)d] %(message)s"
    )

    # File handler
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger
