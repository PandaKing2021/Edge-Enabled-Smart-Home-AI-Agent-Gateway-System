"""IoT smart gateway main entry point.

Initialize configuration, database, shared state, and start communication module threads.
"""

import logging
import socket
import sys
import threading
from pathlib import Path

# Add project root directory and Gate directory to sys.path to ensure correct module import
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
    """Connect to remote database server.

    Args:
        config: Gateway complete configuration.

    Returns:
        Database server TCP socket.

    Raises:
        ConnectionError: Connection failed.
    """
    db_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        db_socket.connect((config.db_server.ip, config.db_server.db_server_port))
        logger.info("Successfully connected to database server: %s:%d",
                     config.db_server.ip, config.db_server.db_server_port)
        return db_socket
    except OSError as error:
        logger.error("Failed to connect to database server: %s", error)
        raise


def check_user_config_with_server(db_socket: socket.socket, user_config: UserConfig) -> None:
    """Validate local user configuration through database server.

    If local configuration is illegally modified, will attempt automatic correction.

    Args:
        db_socket: Database server TCP socket.
        user_config: Local user configuration.
    """
    to_check_user = format_userdata_string(
        user_config.username, user_config.password, user_config.device_key
    )

    send_json(db_socket, format_comm_data_string("check_userconfig_illegal", to_check_user, 1))

    response = recv_json(db_socket)
    op, data, status_code = decode_comm_data(response)

    if status_code == 1:
        logger.info("Local user configuration valid: %s", user_config.username)
    elif status_code == 0:
        logger.warning("Local user configuration abnormal, checking for correction...")
        try:
            corr_response = recv_json(db_socket)
            _, corr_data, corr_status = decode_comm_data(corr_response)

            if corr_status == 1:
                corr_user, corr_pwd, corr_key = decode_user_data(corr_data)
                write_user_config(
                    UserConfig(username=corr_user, password=corr_pwd, device_key=corr_key),
                    config_dir=_GATE_DIR,
                )
                logger.info("Gateway configuration corrected successfully, please restart gateway")
            else:
                logger.error("User not registered")
        except Exception as error:
            logger.error("Configuration correction process exception: %s", error)
    elif status_code == 2:
        logger.error("Database server exception, please check connection")


def fetch_permitted_devices(db_socket: socket.socket, device_key: str) -> list:
    """Get permitted device list from database server.

    Args:
        db_socket: Database server TCP socket.
        device_key: Device key.

    Returns:
        Permitted device name list.
    """
    send_json(db_socket, format_comm_data_string("check_device_id", device_key, 1))

    response = recv_json(db_socket)
    _, device_list, status_code = decode_comm_data(response)

    if status_code == 1:
        # New format: device_list is a JSON array
        if isinstance(device_list, list):
            devices = [d for d in device_list if d]
        else:
            devices = [d for d in device_list.split("+") if d]
        logger.info("Successfully retrieved permitted devices: %s", devices)
        return devices
    else:
        logger.error("Failed to retrieve permitted devices: %s", device_list)
        return []


def main():
    """Gateway main entry function."""
    # Initialize logging
    setup_logging(log_dir=_GATE_DIR)

    # Load configuration
    config = load_gate_config(config_dir=_GATE_DIR)
    user_config = load_user_config(config_dir=_GATE_DIR)

    # Initialize shared state
    state = GatewayState()
    state.data_from_source = dict(DEFAULT_SENSOR_DATA)
    state.update_data(DEFAULT_THRESHOLD_DATA)

    # Initialize local database
    try:
        gate_db_conn = db_module.init_gate_database(config.gate_db)
        db_module._gate_db_conn = gate_db_conn
    except Exception as error:
        logger.critical("Local database initialization failed: %s", error)
        sys.exit(1)

    # Connect to database server
    try:
        db_socket = connect_db_server(config)
    except ConnectionError:
        logger.critical("Unable to connect to database server, gateway exiting")
        sys.exit(1)

    # Validate local user configuration
    try:
        check_user_config_with_server(db_socket, user_config)
    except Exception as error:
        logger.error("User configuration validation failed: %s", error)

    # Get permitted device list
    permitted_devices = fetch_permitted_devices(db_socket, user_config.device_key)
    state.set_permitted_device(permitted_devices)

    # Aliyun IoT configuration
    iot_config = AliyunIotConfig(
        product_key="k0gpoX7HaYl",
        device_name="all_devices",
        device_secret="96a38823b47d9d310ee2d31f17ac5170",
        region_id="cn-shanghai",
    )

    # Initialize AI Agent module
    logger.info("Initializing AI Agent module...")
    ai_agent_components = None

    try:
        # Read AI Agent configuration
        ai_config_path = _GATE_DIR / "ai_agent_config.txt"
        ai_config = {}
        if ai_config_path.exists():
            with open(ai_config_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        ai_config[key.strip()] = value.strip()

        # Check if API Key is configured
        api_key = ai_config.get("API_KEY", "YOUR_API_KEY_HERE")
        if api_key == "YOUR_API_KEY_HERE":
            logger.warning("AI Agent API Key not configured, please edit ai_agent_config.txt to set API_KEY")
        else:
            # Initialize AI Agent components
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
                preference_manager=None,  # Initialize later
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

            # Update intent_planner's preference_manager reference
            intent_planner.preference_manager = preference_manager

            ai_agent_components = {
                "dialog_manager": dialog_manager,
                "intent_planner": intent_planner,
                "task_executor": task_executor,
                "device_controller": device_controller,
                "preference_manager": preference_manager,
            }

            logger.info("AI Agent module initialized successfully")

    except Exception as error:
        logger.error("AI Agent module initialization failed: %s", error, exc_info=True)
        logger.warning("AI Agent functionality will not be available")

    # Create Android communication handler
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

    # Start communication threads
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
        logger.info("Thread '%s' started", t.name)

    logger.info("Gateway ready")

    # Main thread waits for child threads
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        logger.info("Gateway received exit signal, shutting down...")
        if gate_db_conn:
            gate_db_conn.close()
        db_socket.close()
        sys.exit(0)


if __name__ == "__main__":
    main()
