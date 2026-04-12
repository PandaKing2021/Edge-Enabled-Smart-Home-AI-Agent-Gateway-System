"""网关配置管理模块。

提供配置文件的读取、校验和加载功能，使用 dataclass 定义配置结构。
配置文件格式保持与原始项目兼容（逐行读取，无 section header）。
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class GateNetworkConfig:
    """网关网络配置。"""
    ip: str = ""
    source_port: int = 0
    android_port: int = 0


@dataclass
class DbServerConfig:
    """数据库服务器连接配置。"""
    ip: str = ""
    db_server_port: int = 0


@dataclass
class GateDbConfig:
    """网关本地数据库配置。"""
    user: str = ""
    password: str = ""
    database: str = ""


@dataclass
class UserConfig:
    """本地授权用户配置。"""
    username: str = ""
    password: str = ""
    device_key: str = ""


@dataclass
class ServerNetworkConfig:
    """数据库服务器网络配置。"""
    ip: str = ""
    listen_port: int = 0


@dataclass
class AliyunIotConfig:
    """阿里云 IoT 连接配置。"""
    product_key: str = ""
    device_name: str = ""
    device_secret: str = ""
    region_id: str = ""


@dataclass
class GateConfig:
    """网关完整配置，聚合所有子配置。"""
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
    """读取配置文件的非空行，去除行尾换行符。

    Args:
        filepath: 配置文件路径。

    Returns:
        非空行列表。

    Raises:
        FileNotFoundError: 配置文件不存在。
    """
    if not filepath.exists():
        raise FileNotFoundError(f"配置文件不存在: {filepath}")

    lines: list[str] = []
    with open(filepath, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if line:
                lines.append(line)
    return lines


def load_gate_config(config_dir: Optional[Path] = None) -> GateConfig:
    """从 GateConfig.txt 加载网关配置。

    文件格式（8行）：
        网关IP / 数据库服务器IP / 设备节点端口 / Android端口 /
        数据库服务器端口 / MySQL用户名 / MySQL密码 / 数据库名

    Args:
        config_dir: 配置文件所在目录，默认为当前目录。

    Returns:
        GateConfig 配置对象。

    Raises:
        ValueError: 配置项不足或格式错误。
    """
    if config_dir is None:
        config_dir = Path.cwd()

    filepath = config_dir / "GateConfig.txt"
    lines = _read_config_lines(filepath)

    if len(lines) < 8:
        raise ValueError(f"GateConfig.txt 配置项不足，需要8行，实际{len(lines)}行")

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

    logger.info("网关配置加载成功: 网关IP=%s, 设备端口=%d, Android端口=%d",
                config.gate_network.ip, config.gate_network.source_port,
                config.gate_network.android_port)
    return config


def load_user_config(config_dir: Optional[Path] = None) -> UserConfig:
    """从 UserConfig.txt 加载本地用户配置。

    文件格式（3行）：用户名 / 密码 / 设备密钥

    Args:
        config_dir: 配置文件所在目录，默认为当前目录。

    Returns:
        UserConfig 配置对象。

    Raises:
        ValueError: 配置项不足。
    """
    if config_dir is None:
        config_dir = Path.cwd()

    filepath = config_dir / "UserConfig.txt"
    lines = _read_config_lines(filepath)

    if len(lines) < 3:
        raise ValueError(f"UserConfig.txt 配置项不足，需要3行，实际{len(lines)}行")

    config = UserConfig(username=lines[0], password=lines[1], device_key=lines[2])
    logger.info("用户配置加载成功: 用户名=%s", config.username)
    return config


def write_user_config(config: UserConfig, config_dir: Optional[Path] = None) -> None:
    """将用户配置写入 UserConfig.txt。

    Args:
        config: 用户配置对象。
        config_dir: 配置文件所在目录，默认为当前目录。
    """
    if config_dir is None:
        config_dir = Path.cwd()

    filepath = config_dir / "UserConfig.txt"
    content = f"{config.username}\n{config.password}\n{config.device_key}\n"
    filepath.write_text(content, encoding="utf-8")
    logger.info("用户配置已写入: %s", filepath)


def load_server_config(config_dir: Optional[Path] = None) -> ServerNetworkConfig:
    """从 serverConfig.txt 加载数据库服务器配置。

    文件格式（2行）：服务器IP / 监听端口

    Args:
        config_dir: 配置文件所在目录，默认为当前目录。

    Returns:
        ServerNetworkConfig 配置对象。

    Raises:
        ValueError: 配置项不足。
    """
    if config_dir is None:
        config_dir = Path.cwd()

    filepath = config_dir / "serverConfig.txt"
    lines = _read_config_lines(filepath)

    if len(lines) < 2:
        raise ValueError(f"serverConfig.txt 配置项不足，需要2行，实际{len(lines)}行")

    config = ServerNetworkConfig(ip=lines[0], listen_port=int(lines[1]))
    logger.info("数据库服务器配置加载成功: IP=%s, 端口=%d", config.ip, config.listen_port)
    return config
