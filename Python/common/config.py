"""Gateway configuration management module.

Provides configuration file reading, validation, and loading functionality, using dataclass to define configuration structure.
Configuration file format maintains compatibility with the original project (line-by-line reading, no section header).
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class GateNetworkConfig:
    """Gateway network configuration."""
    ip: str = ""
    source_port: int = 0
    android_port: int = 0


@dataclass
class DbServerConfig:
    """Database server connection configuration."""
    ip: str = ""
    db_server_port: int = 0


@dataclass
class GateDbConfig:
    """Gateway local database configuration."""
    user: str = ""
    password: str = ""
    database: str = ""


@dataclass
class UserConfig:
    """Local authorized user configuration."""
    username: str = ""
    password: str = ""
    device_key: str = ""


@dataclass
class ServerNetworkConfig:
    """Database server network configuration."""
    ip: str = ""
    listen_port: int = 0


@dataclass
class AliyunIotConfig:
    """Aliyun IoT connection configuration."""
    product_key: str = ""
    device_name: str = ""
    device_secret: str = ""
    region_id: str = ""


@dataclass
class GateConfig:
    """Complete gateway configuration, aggregating all sub-configurations."""
    gate_network: GateNetworkConfig = None  # type: ignore[assignment]
    db_server: DbServerConfig = None  # type: ignore[assignment]
    gate_db: GateDbConfig = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.gate_network is None:
            self.gate_network = GateNetworkConfig()
        if self.db_server is None:
            self.db_server = DbServerConfig()
        if self.gate_db is None:
            self.gate_db = GateDbConfig()


def _read_config_lines(filepath: Path) -> list[str]:
    """Read non-empty lines from configuration file, removing trailing newlines.

    Args:
        filepath: Configuration file path.

    Returns:
        List of non-empty lines.

    Raises:
        FileNotFoundError: Configuration file does not exist.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Configuration file does not exist: {filepath}")

    lines: list[str] = []
    with open(filepath, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if line:
                lines.append(line)
    return lines


def load_gate_config(config_dir: Optional[Path] = None) -> GateConfig:
    """Load gateway configuration from GateConfig.txt.

    File format (8 lines):
        Gateway IP / Database server IP / Device node port / Android port /
        Database server port / MySQL username / MySQL password / Database name

    Args:
        config_dir: Directory where configuration file is located, defaults to current directory.

    Returns:
        GateConfig configuration object.

    Raises:
        ValueError: Insufficient configuration items or format error.
    """
    if config_dir is None:
        config_dir = Path.cwd()

    filepath = config_dir / "GateConfig.txt"
    lines = _read_config_lines(filepath)

    if len(lines) < 8:
        raise ValueError(f"GateConfig.txt has insufficient configuration items, need 8 lines, actual {len(lines)} lines")

    config = GateConfig(
        gate_network=GateNetworkConfig(
            ip=lines[0],
            source_port=int(lines[2]),
            android_port=int(lines[3]),
        ),
        db_server=DbServerConfig(
            ip=lines[1],
            db_server_port=int(lines[4]),
        ),
        gate_db=GateDbConfig(
            user=lines[5],
            password=lines[6],
            database=lines[7],
        ),
    )

    logger.info("Gateway configuration loaded successfully: Gateway IP=%s, Device port=%d, Android port=%d",
                config.gate_network.ip, config.gate_network.source_port,
                config.gate_network.android_port)
    return config


def load_user_config(config_dir: Optional[Path] = None) -> UserConfig:
    """Load local user configuration from UserConfig.txt.

    File format (3 lines): Username / Password / Device key

    Args:
        config_dir: Directory where configuration file is located, defaults to current directory.

    Returns:
        UserConfig configuration object.

    Raises:
        ValueError: Insufficient configuration items.
    """
    if config_dir is None:
        config_dir = Path.cwd()

    filepath = config_dir / "UserConfig.txt"
    lines = _read_config_lines(filepath)

    if len(lines) < 3:
        raise ValueError(f"UserConfig.txt has insufficient configuration items, need 3 lines, actual {len(lines)} lines")

    config = UserConfig(username=lines[0], password=lines[1], device_key=lines[2])
    logger.info("User configuration loaded successfully: Username=%s", config.username)
    return config


def write_user_config(config: UserConfig, config_dir: Optional[Path] = None) -> None:
    """Write user configuration to UserConfig.txt.

    Args:
        config: User configuration object.
        config_dir: Directory where configuration file is located, defaults to current directory.
    """
    if config_dir is None:
        config_dir = Path.cwd()

    filepath = config_dir / "UserConfig.txt"
    content = f"{config.username}\n{config.password}\n{config.device_key}\n"
    filepath.write_text(content, encoding="utf-8")
    logger.info("User configuration written to: %s", filepath)


def load_server_config(config_dir: Optional[Path] = None) -> ServerNetworkConfig:
    """Load database server configuration from serverConfig.txt.

    File format (2 lines): Server IP / Listen port

    Args:
        config_dir: Directory where configuration file is located, defaults to current directory.

    Returns:
        ServerNetworkConfig configuration object.

    Raises:
        ValueError: Insufficient configuration items.
    """
    if config_dir is None:
        config_dir = Path.cwd()

    filepath = config_dir / "serverConfig.txt"
    lines = _read_config_lines(filepath)

    if len(lines) < 2:
        raise ValueError(f"serverConfig.txt has insufficient configuration items, need 2 lines, actual {len(lines)} lines")

    config = ServerNetworkConfig(ip=lines[0], listen_port=int(lines[1]))
    logger.info("Database server configuration loaded successfully: IP=%s, Port=%d", config.ip, config.listen_port)
    return config
