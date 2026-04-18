"""IoT smart gateway main entry - test version.

Added test mode, making database server connection optional.
"""

import logging
import socket
import sys
import threading
import os
from pathlib import Path

# Set encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root directory and Gate directory to sys.path to ensure correct module imports
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

# Test mode flag
TEST_MODE = '--test' in sys.argv or os.getenv('TEST_MODE', 'false').lower() == 'true'


def connect_db_server(config: GateConfig) -> socket.socket:
    """Connect to remote database server (optional in test mode).

    Args:
        config: Complete gateway configuration.

    Returns:
        TCP socket to database server, or None (in test mode).

    Raises:
        ConnectionError: Connection failed (non-test mode).
    """
    if TEST_MODE:
        logger.warning("Test mode: Skipping database server connection")
        return None

    db_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        db_socket.connect((config.db_server.ip, config.db_server.db_server_port))
        logger.info("Connected to database server successfully: %s:%d",
                     config.db_server.ip, config.db_server.db_server_port)
        return db_socket
    except OSError as error:
        logger.error("Failed to connect to database server: %s", error)
        raise


def check_user_config_with_server(db_socket: socket.socket, user_config: UserConfig) -> None:
    """Verify local user configuration through database server.

    Args:
        db_socket: TCP socket to database server (can be None in test mode).
        user_config: Local user configuration.
    """
    if TEST_MODE or db_socket is None:
        logger.warning("Test mode: Skipping user configuration verification")
        return

    to_check_user = format_userdata_string(
        user_config.username, user_config.password, user_config.device_key
    )

    send_json(db_socket, format_comm_data_string("check_userconfig_illegal", to_check_user, 1))

    response = recv_json(db_socket)
    op, data, status_code = decode_comm_data(response)

    if status_code == 1:
        logger.info("Local user configuration is valid: %s", user_config.username)
    elif status_code == 0:
        logger.warning("Local user configuration is invalid, checking and correcting...")
        try:
            corr_response = recv_json(db_socket)
            _, corr_data, corr_status = decode_comm_data(corr_response)

            if corr_status == 1:
                corr_user, corr_pwd, corr_key = decode_user_data(corr_data)
                write_user_config(
                    UserConfig(username=corr_user, password=corr_pwd, device_key=corr_key),
                    config_dir=_GATE_DIR,
                )
                logger.info("Gateway configuration corrected successfully, please restart the gateway")
            else:
                logger.error("User is not registered")
        except Exception as error:
            logger.error("Exception during configuration correction: %s", error)
    elif status_code == 2:
        logger.error("Database server error, please check connection")


def fetch_permitted_devices(db_socket: socket.socket, device_key: str) -> list:
    """Get list of permitted devices from database server (returns default list in test mode).

    Args:
        db_socket: TCP socket to database server (can be None in test mode).
        device_key: Device key.

    Returns:
        List of permitted device names.
    """
    if TEST_MODE or db_socket is None:
        logger.warning("Test mode: Using default device list")
        return ["A1_tem_hum", "A1_curtain", "A1_security"]

    send_json(db_socket, format_comm_data_string("check_device_id", device_key, 1))

    response = recv_json(db_socket)
    _, device_list, status_code = decode_comm_data(response)

    if status_code == 1:
        # New format: device_list is a JSON array
        if isinstance(device_list, list):
            devices = [d for d in device_list if d]
        else:
            devices = [d for d in device_list.split("+") if d]
        logger.info("Successfully fetched permitted device information: %s", devices)
        return devices
    else:
        logger.error("Failed to fetch permitted device information: %s", device_list)
        return []


def main():
    """Gateway main entry function."""
    # Initialize logging
    setup_logging(log_dir=_GATE_DIR)

    if TEST_MODE:
        print("="*60)
        print("WARNING: Test mode is enabled")
        print("   - Skipping database server connection")
        print("   - Using default device list")
        print("   - Skipping user configuration verification")
        print("="*60)

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
        if not TEST_MODE:
            sys.exit(1)
        else:
            logger.warning("Test mode: Continuing to run, skipping local database")

    # Connect to database server
    db_socket = None
    try:
        db_socket = connect_db_server(config)
    except (ConnectionError, OSError, TimeoutError) as e:
        if TEST_MODE:
            logger.warning("Test mode: Database server connection failed, continuing to run: " + str(e))
        else:
            logger.critical("Unable to connect to database server, gateway exiting")
            sys.exit(1)

    # Verify local user configuration
    try:
        check_user_config_with_server(db_socket, user_config)
    except Exception as error:
        logger.error("User configuration verification failed: %s", error)

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

    # Create Android communication handler
    # Note: In test mode, db_socket may be None, AndroidHandler needs to handle this
    if db_socket is None:
        logger.warning("Test mode: Android handler will be unable to communicate with database server")
        # Create a mock socket object
        class MockSocket:
            def send(self, data): pass
        db_socket = MockSocket()

    # Initialize AI Agent components
    dialog_manager = None
    intent_planner = None
    task_executor = None
    device_controller = None
    preference_manager = None

    try:
        from ai_agent import DialogManager, IntentPlanner, TaskExecutor, DeviceController, PreferenceManager

        # Read API key from config
        ai_config_file = _GATE_DIR / "ai_agent_config.txt"
        api_key = None
        if ai_config_file.exists():
            with open(ai_config_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("API_KEY"):
                        key = line.split("=", 1)[1].strip()
                        if key and key != "YOUR_API_KEY":
                            api_key = key
                        break

        # Initialize DeviceController (always available - works with GatewayState)
        device_controller = DeviceController(state)
        logger.info("DeviceController initialized")

        # Initialize TaskExecutor (always available)
        task_executor = TaskExecutor(device_controller)
        logger.info("TaskExecutor initialized")

        # Initialize DialogManager (always available)
        dialog_manager = DialogManager()
        logger.info("DialogManager initialized")

        # Initialize PreferenceManager (always available)
        preference_manager = PreferenceManager()
        logger.info("PreferenceManager initialized")

        # Initialize IntentPlanner (requires API key for real LLM)
        if api_key:
            capability_retriever = CapabilityRetriever(
                str(_GATE_DIR / "device_capabilities.json")
            )
            intent_planner = IntentPlanner(
                api_key=api_key,
                capability_retriever=capability_retriever,
                preference_manager=preference_manager,
            )
            logger.info("IntentPlanner initialized with real LLM (GLM-4.7-Flash)")
        else:
            # Use simulated IntentPlanner
            intent_planner = None
            logger.warning("IntentPlanner not initialized (no API key). Chat commands will use simulated responses.")

    except ImportError as error:
        logger.warning("AI Agent module not available: %s", error)
    except Exception as error:
        logger.warning("AI Agent initialization failed: %s", error)

    android_ctrl = android_handler.AndroidHandler(
        db_socket,
        config_dir=_GATE_DIR,
        dialog_manager=dialog_manager,
        intent_planner=intent_planner,
        task_executor=task_executor,
        device_controller=device_controller,
        preference_manager=preference_manager,
    )

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
        if db_socket and hasattr(db_socket, 'close'):
            db_socket.close()
        sys.exit(0)


if __name__ == "__main__":
    main()
