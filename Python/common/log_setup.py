"""网关日志初始化模块。"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(log_file: str = "gateLogs.log", log_dir: Optional[Path] = None) -> logging.Logger:
    """初始化网关日志系统。

    同时输出到文件和控制台，使用标准格式。

    Args:
        log_file: 日志文件名。
        log_dir: 日志文件目录，默认为当前目录。

    Returns:
        根 logger 实例。
    """
    if log_dir is None:
        log_dir = Path.cwd()

    log_path = log_dir / log_file
    formatter = logging.Formatter(
        "[%(asctime)s][%(levelname)s][%(name)s][%(filename)s:%(lineno)d] %(message)s"
    )

    # 文件 handler
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # 配置根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger
