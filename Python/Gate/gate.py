"""IoT 智能网关主入口。

初始化配置、数据库、共享状态，并启动各通信模块的线程。
"""

import logging
import socket
import sys
import threading
from pathlib import Path

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
from ai_agent import (
    DialogManager,
    IntentPlanner,
    CapabilityRetriever,
    TaskExecutor,
    DeviceController,
    PreferenceManager,
)

logger = logging.getLogger(__name__)


def connect_db_server(config: GateConfig) -> socket.socket:
    """连接到远程数据库服务器。

    Args:
        config: 网关完整配置。

    Returns:
        数据库服务器的 TCP 套接字。

    Raises:
        ConnectionError: 连接失败。
    """
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

    如果本地配置被非法修改，会尝试自动纠正。

    Args:
        db_socket: 数据库服务器的 TCP 套接字。
        user_config: 本地用户配置。
    """
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
    """从数据库服务器获取允许的设备列表。

    Args:
        db_socket: 数据库服务器的 TCP 套接字。
        device_key: 设备密钥。

    Returns:
        允许的设备名称列表。
    """
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
        sys.exit(1)

    # 连接数据库服务器
    try:
        db_socket = connect_db_server(config)
    except ConnectionError:
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

    # 初始化 AI Agent 模块
    logger.info("初始化 AI Agent 模块...")
    ai_agent_components = None

    try:
        # 读取AI Agent配置
        ai_config_path = _GATE_DIR / "ai_agent_config.txt"
        ai_config = {}
        if ai_config_path.exists():
            with open(ai_config_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        ai_config[key.strip()] = value.strip()

        # 检查API Key是否配置
        api_key = ai_config.get("API_KEY", "YOUR_API_KEY_HERE")
        if api_key == "YOUR_API_KEY_HERE":
            logger.warning("AI Agent API Key 未配置,请编辑 ai_agent_config.txt 设置 API_KEY")
        else:
            # 初始化AI Agent组件
            dialog_manager = DialogManager(
                max_context_turns=int(ai_config.get("MAX_CONTEXT_TURNS", 5)),
                session_timeout=int(ai_config.get("SESSION_TIMEOUT", 3600)),
            )

            capability_retriever = CapabilityRetriever(
                capabilities_file=str(_GATE_DIR / ai_config.get(
                    "CAPABILITIES_FILE", "device_capabilities.json"
                ))
            )

            intent_planner = IntentPlanner(
                api_key=api_key,
                base_url=ai_config.get("BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
                model_name=ai_config.get("MODEL_NAME", "GLM-4.7-Flash"),
                temperature=float(ai_config.get("TEMPERATURE", 0.7)),
                capability_retriever=capability_retriever,
                preference_manager=None,  # 稍后初始化
            )

            device_controller = DeviceController(state=state)

            task_executor = TaskExecutor(
                device_controller=device_controller,
                enable_rollback=ai_config.get("ENABLE_ROLLBACK", "True").lower() == "true",
                max_retry=int(ai_config.get("MAX_RETRY", 3)),
                task_timeout=int(ai_config.get("TASK_TIMEOUT", 30)),
            )

            preference_manager = PreferenceManager(
                db_connection=gate_db_conn,
                table_name=ai_config.get("PREFERENCE_DB_TABLE", "user_preferences"),
            )

            # 更新intent_planner的preference_manager引用
            intent_planner.preference_manager = preference_manager

            ai_agent_components = {
                "dialog_manager": dialog_manager,
                "intent_planner": intent_planner,
                "task_executor": task_executor,
                "device_controller": device_controller,
                "preference_manager": preference_manager,
            }

            logger.info("AI Agent 模块初始化成功")

    except Exception as error:
        logger.error("AI Agent 模块初始化失败: %s", error, exc_info=True)
        logger.warning("AI Agent 功能将不可用")

    # 创建 Android 通信处理器
    if ai_agent_components:
        android_ctrl = android_handler.AndroidHandler(
            db_socket,
            config_dir=_GATE_DIR,
            dialog_manager=ai_agent_components["dialog_manager"],
            intent_planner=ai_agent_components["intent_planner"],
            task_executor=ai_agent_components["task_executor"],
            device_controller=ai_agent_components["device_controller"],
            preference_manager=ai_agent_components["preference_manager"],
        )
    else:
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
        db_socket.close()
        sys.exit(0)


if __name__ == "__main__":
    main()
