"""IoT 智能网关主入口 - 测试版本。

添加测试模式，使数据库服务器连接可选。
"""

import logging
import socket
import sys
import threading
import os
from pathlib import Path

# 设置编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 将项目根目录和 Gate 目录添加到 sys.path，确保模块导入正确
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_GATE_DIR = Path(__file__).resolve().parent

if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
if str(_GATE_DIR) not in sys.path:
    sys.path.insert(0, str(_GATE_DIR))

import warnings
warnings.filterwarnings("ignore")

from MyComm import format_comm_data_string, decode_comm_data, format_userdata_string, decode_user_data
from common.config import (
    AliyunIotConfig,
    GateConfig,
    UserConfig,
    load_gate_config,
    load_user_config,
    write_user_config,
)
from common.models import GatewayState
from common.log_setup import setup_logging
from common.constants import (
    DEFAULT_SENSOR_DATA,
    DEFAULT_THRESHOLD_DATA,
    DOOR_GRANTED,
)
from common.protocol import send_json, recv_json

import database as db_module
import sensor_handler
import android_handler
import aliyun_handler

logger = logging.getLogger(__name__)

# 测试模式标志
TEST_MODE = '--test' in sys.argv or os.getenv('TEST_MODE', 'false').lower() == 'true'


def connect_db_server(config: GateConfig) -> socket.socket:
    """连接到远程数据库服务器（测试模式下可选）。

    Args:
        config: 网关完整配置。

    Returns:
        数据库服务器的 TCP 套接字，或 None（测试模式）。

    Raises:
        ConnectionError: 连接失败（非测试模式）。
    """
    if TEST_MODE:
        logger.warning("测试模式：跳过数据库服务器连接")
        return None

    db_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        db_socket.connect((config.db_server.ip, config.db_server.db_server_port))
        logger.info("与数据库服务器连接成功: %s:%d",
                     config.db_server.ip, config.db_server.db_server_port)
        return db_socket
    except OSError as error:
        logger.error("与数据库服务器连接失败: %s", error)
        raise


def check_user_config_with_server(db_socket: socket.socket, user_config: UserConfig) -> None:
    """通过数据库服务器校验本地用户配置。

    Args:
        db_socket: 数据库服务器的 TCP 套接字（测试模式下可为None）。
        user_config: 本地用户配置。
    """
    if TEST_MODE or db_socket is None:
        logger.warning("测试模式：跳过用户配置校验")
        return

    to_check_user = format_userdata_string(
        user_config.username, user_config.password, user_config.device_key
    )

    send_json(db_socket, format_comm_data_string("check_userconfig_illegal", to_check_user, 1))

    response = recv_json(db_socket)
    op, data, status_code = decode_comm_data(response)

    if status_code == 1:
        logger.info("本地用户配置正常: %s", user_config.username)
    elif status_code == 0:
        logger.warning("本地用户配置异常，正在检查修正...")
        try:
            corr_response = recv_json(db_socket)
            _, corr_data, corr_status = decode_comm_data(corr_response)

            if corr_status == 1:
                corr_user, corr_pwd, corr_key = decode_user_data(corr_data)
                write_user_config(
                    UserConfig(username=corr_user, password=corr_pwd, device_key=corr_key),
                    config_dir=_GATE_DIR,
                )
                logger.info("网关配置纠正成功，请重启网关")
            else:
                logger.error("用户未注册")
        except Exception as error:
            logger.error("配置修正过程异常: %s", error)
    elif status_code == 2:
        logger.error("数据库服务器异常，请检查连接")


def fetch_permitted_devices(db_socket: socket.socket, device_key: str) -> list:
    """从数据库服务器获取允许的设备列表（测试模式下返回默认列表）。

    Args:
        db_socket: 数据库服务器的 TCP 套接字（测试模式下可为None）。
        device_key: 设备密钥。

    Returns:
        允许的设备名称列表。
    """
    if TEST_MODE or db_socket is None:
        logger.warning("测试模式：使用默认设备列表")
        return ["A1_tem_hum", "A1_curtain", "A1_security"]

    send_json(db_socket, format_comm_data_string("check_device_id", device_key, 1))

    response = recv_json(db_socket)
    _, device_list, status_code = decode_comm_data(response)

    if status_code == 1:
        # 新格式：device_list 为 JSON 数组
        if isinstance(device_list, list):
            devices = [d for d in device_list if d]
        else:
            devices = [d for d in device_list.split("+") if d]
        logger.info("获取允许设备信息成功: %s", devices)
        return devices
    else:
        logger.error("获取允许设备信息失败: %s", device_list)
        return []


def main():
    """网关主入口函数。"""
    # 初始化日志
    setup_logging(log_dir=_GATE_DIR)

    if TEST_MODE:
        print("="*60)
        print("WARNING: 测试模式已启用")
        print("   - 跳过数据库服务器连接")
        print("   - 使用默认设备列表")
        print("   - 跳过用户配置校验")
        print("="*60)

    # 加载配置
    config = load_gate_config(config_dir=_GATE_DIR)
    user_config = load_user_config(config_dir=_GATE_DIR)

    # 初始化共享状态
    state = GatewayState()
    state.data_from_source = dict(DEFAULT_SENSOR_DATA)
    state.update_data(DEFAULT_THRESHOLD_DATA)

    # 初始化本地数据库
    try:
        gate_db_conn = db_module.init_gate_database(config.gate_db)
        db_module._gate_db_conn = gate_db_conn
    except Exception as error:
        logger.critical("本地数据库初始化失败: %s", error)
        if not TEST_MODE:
            sys.exit(1)
        else:
            logger.warning("测试模式：继续运行，跳过本地数据库")

    # 连接数据库服务器
    db_socket = None
    try:
        db_socket = connect_db_server(config)
    except (ConnectionError, OSError, TimeoutError) as e:
        if TEST_MODE:
            logger.warning("测试模式：数据库服务器连接失败，继续运行: " + str(e))
        else:
            logger.critical("无法连接数据库服务器，网关退出")
            sys.exit(1)

    # 校验本地用户配置
    try:
        check_user_config_with_server(db_socket, user_config)
    except Exception as error:
        logger.error("用户配置校验失败: %s", error)

    # 获取允许设备列表
    permitted_devices = fetch_permitted_devices(db_socket, user_config.device_key)
    state.set_permitted_device(permitted_devices)

    # 阿里云 IoT 配置
    iot_config = AliyunIotConfig(
        product_key="k0gpoX7HaYl",
        device_name="all_devices",
        device_secret="96a38823b47d9d310ee2d31f17ac5170",
        region_id="cn-shanghai",
    )

    # 创建 Android 通信处理器
    # 注意：测试模式下，db_socket可能为None，AndroidHandler需要处理
    if db_socket is None:
        logger.warning("测试模式：Android处理器将无法与数据库服务器通信")
        # 创建一个虚拟的socket对象
        class MockSocket:
            def send(self, data): pass
        db_socket = MockSocket()

    android_ctrl = android_handler.AndroidHandler(db_socket, config_dir=_GATE_DIR)

    # 启动各通信线程
    threads = [
        threading.Thread(
            target=sensor_handler.sensor_handler,
            args=(config.gate_network, state),
            name="sensor-listener",
            daemon=True,
        ),
        threading.Thread(
            target=android_ctrl.android_handler,
            args=(config.gate_network, state),
            name="android-listener",
            daemon=True,
        ),
        threading.Thread(
            target=aliyun_handler.aliyun_upload_loop,
            args=(
                iot_config,
                state.get_data_snapshot,
                state.wait_for_sensor,
            ),
            name="aliyun-uploader",
            daemon=True,
        ),
    ]

    for t in threads:
        t.start()
        logger.info("线程 '%s' 已启动", t.name)

    logger.info("网关就绪")

    # 主线程等待子线程
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        logger.info("网关收到退出信号，正在关闭...")
        if gate_db_conn:
            gate_db_conn.close()
        if db_socket and hasattr(db_socket, 'close'):
            db_socket.close()
        sys.exit(0)


if __name__ == "__main__":
    main()
