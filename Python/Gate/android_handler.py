"""Mobile app (Android) communication handler module.

Responsible for TCP communication with Android mobile app, including:
- Mobile app connection listening
- User login/registration
- Threshold setting
- Device data push
- AI Agent dialogue interaction
"""

import json
import logging
import socket
import threading
from typing import TYPE_CHECKING, Optional

from MyComm import format_comm_data_string, format_userdata_string, decode_comm_data
from common.constants import (
    DOOR_DENIED,
    FIELD_BRIGHTNESS,
    FIELD_HUMIDITY,
    FIELD_TEMPERATURE,
    LISTEN_BACKLOG,
    ANDROID_RECV_INTERVAL,
    ANDROID_SEND_INTERVAL,
)
from common.config import UserConfig, write_user_config, load_user_config
from common.protocol import send_json, recv_json, send_line, recv_line

if TYPE_CHECKING:
    from common.models import GatewayState
    from ai_agent import DialogManager, IntentPlanner, TaskExecutor, DeviceController, PreferenceManager

logger = logging.getLogger(__name__)


class AndroidHandler:
    """Mobile app communication handler.

    Encapsulates mobile app-related communication logic, holds database server socket reference.

    Attributes:
        db_socket: TCP socket with database server.
        config_dir: Configuration file directory.
        dialog_manager: Dialog manager instance.
        intent_planner: Intent parser instance.
        task_executor: Task executor instance.
        device_controller: Device controller instance.
        preference_manager: Preference manager instance.
    """

    def __init__(
        self,
        db_socket: socket.socket,
        config_dir,
        dialog_manager: Optional["DialogManager"] = None,
        intent_planner: Optional["IntentPlanner"] = None,
        task_executor: Optional["TaskExecutor"] = None,
        device_controller: Optional["DeviceController"] = None,
        preference_manager: Optional["PreferenceManager"] = None,
    ) -> None:
        self.db_socket = db_socket
        self.config_dir = config_dir
        self.dialog_manager = dialog_manager
        self.intent_planner = intent_planner
        self.task_executor = task_executor
        self.device_controller = device_controller
        self.preference_manager = preference_manager

    def android_handler(self, gate_network_config, state: "GatewayState") -> None:
        """Mobile app communication main listening thread.

        Args:
            gate_network_config: Gateway network configuration.
            state: Gateway shared state object.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((gate_network_config.ip, gate_network_config.android_port))
        s.listen(LISTEN_BACKLOG)
        logger.info("Mobile app communication port opened: %s:%d",
                     gate_network_config.ip, gate_network_config.android_port)

        while True:
            try:
                cs, addr = s.accept()
                logger.info("Mobile app connection: %s", addr)
                thread = threading.Thread(
                    target=self._client_handler, args=(cs, state), daemon=True
                )
                thread.start()
            except OSError as error:
                logger.error("Mobile app listening exception: %s", error)

    def _client_handler(self, cs: socket.socket, state: "GatewayState") -> None:
        """Handle single mobile app connection.

        Args:
            cs: TCP socket of mobile app.
            state: Gateway shared state object.
        """
        try:
            recv_data = recv_json(cs)
            android_state, curr_user_json, status_code = decode_comm_data(recv_data)
            curr_user = curr_user_json if isinstance(curr_user_json, dict) else json.loads(curr_user_json)

            if android_state == "login":
                self._android_login(cs, curr_user, state)
            elif android_state == "register":
                self._android_register(cs, curr_user)
            elif android_state == "chat":
                self._handle_chat_request(cs, curr_user, state)

        except (json.JSONDecodeError, ValueError) as error:
            logger.error("Failed to parse mobile app data: %s", error)
        except (ConnectionError, OSError) as error:
            logger.error("Mobile app connection disconnected: %s", error)
        except Exception as error:
            logger.error("Mobile app communication exception: %s", error)
        finally:
            cs.close()

    def _android_login(self, cs: socket.socket, curr_user: dict, state: "GatewayState") -> None:
        """Handle user login.

        Args:
            cs: TCP socket of mobile app.
            curr_user: User info dictionary, must contain "account" and "password" keys.
            state: Gateway shared state object.
        """
        try:
            user_config = load_user_config(config_dir=self.config_dir)
        except FileNotFoundError:
            user_config = UserConfig()

        if user_config.username == curr_user["account"] and user_config.password == curr_user["password"]:
            send_json(cs, {"status": 1})
            state.login_status = 1
            logger.info("User '%s' logged in successfully", curr_user["account"])

            # Wait for device node connection
            state.wait_for_sensor()

            # Start send/receive threads
            recv_thread = threading.Thread(
                target=self._get_from_android, args=(cs, state), daemon=True
            )
            send_thread = threading.Thread(
                target=self._send_to_android, args=(cs, state), daemon=True
            )
            recv_thread.start()
            send_thread.start()
            recv_thread.join()
            send_thread.join()
        else:
            send_json(cs, {"status": 0})
            state.login_status = 0
            logger.warning("User '%s' login failed", curr_user["account"])

    def _android_register(self, cs: socket.socket, given_user: dict) -> None:
        """Handle user registration.

        Process: send user info to database server → update local configuration based on result.

        Args:
            cs: TCP socket of mobile app.
            given_user: User info dictionary, must contain "account", "password", "device_Key" keys.
        """
        logger.info("User registering: %s", given_user.get("account"))

        # Construct and send registration request to database server
        db_data_send = format_comm_data_string(
            "add_new_user",
            format_userdata_string(given_user["account"], given_user["password"], given_user["device_Key"]),
            1,
        )
        send_json(self.db_socket, db_data_send)
        logger.info("Sent to database server: %s", db_data_send)

        # Receive database server response
        try:
            db_data_recv = recv_json(self.db_socket)
            _, data, status_code = decode_comm_data(db_data_recv)

            if status_code == 1:
                write_user_config(
                    UserConfig(
                        username=given_user["account"],
                        password=given_user["password"],
                        device_key=given_user["device_Key"],
                    ),
                    config_dir=self.config_dir,
                )
                logger.info("Registration successful, user info updated")
                send_json(cs, {"status": 1})
            elif status_code in (0, 2):
                logger.warning("Registration failed: %s", data)
                send_json(cs, {"status": 0})
        except (ConnectionError, OSError) as error:
            logger.error("Registration process connection disconnected: %s", error)
            send_json(cs, {"status": 0})
        except Exception as error:
            logger.error("Registration process exception: %s", error)
            send_json(cs, {"status": 0})

    def _send_to_android(self, cs: socket.socket, state: "GatewayState") -> None:
        """Push device data to mobile app.

        Sends sensor data in JSON format.

        Args:
            cs: TCP socket of mobile app.
            state: Gateway shared state object.
        """
        import time

        logger.info("Mobile app send sub-thread started")

        try:
            while True:
                data = state.get_data_snapshot()
                send_json(cs, data)
                logger.info("Sent to mobile app: %s", data)
                time.sleep(ANDROID_SEND_INTERVAL)

        except (ConnectionError, ConnectionAbortedError, OSError) as error:
            logger.error("Mobile app send connection disconnected: %s", error)

    def _get_from_android(self, cs: socket.socket, state: "GatewayState") -> None:
        """Receive control commands from mobile app.

        Parse operation codes and update threshold data:
        - light_th_open/close: Smart AC switch
        - change_temperature_threshold: Temperature threshold
        - change_humidity_threshold: Humidity threshold
        - curtain_open/close: Curtain control
        - change_brightness_threshold: Brightness threshold

        Args:
            cs: TCP socket of mobile app.
            state: Gateway shared state object.
        """
        import time

        logger.info("Mobile app receive sub-thread started")

        try:
            while True:
                recv_data = recv_json(cs)
                operation, operation_value, _ = decode_comm_data(recv_data)

                if operation == "light_th_open":
                    state.set_threshold(FIELD_TEMPERATURE, -1)
                    state.set_threshold(FIELD_HUMIDITY, -1)
                    logger.info("Mobile app command: Smart AC light on")
                elif operation == "light_th_close":
                    state.set_threshold(FIELD_TEMPERATURE, 101)
                    state.set_threshold(FIELD_HUMIDITY, 101)
                    logger.info("Mobile app command: Smart AC light off")
                elif operation == "change_temperature_threshold":
                    state.set_threshold(FIELD_TEMPERATURE, operation_value)
                elif operation == "change_humidity_threshold":
                    state.set_threshold(FIELD_HUMIDITY, operation_value)
                elif operation == "curtain_close":
                    state.set_threshold(FIELD_BRIGHTNESS, 65535)
                    logger.info("Mobile app command: Curtain close")
                elif operation == "curtain_open":
                    state.set_threshold(FIELD_BRIGHTNESS, -2)
                    logger.info("Mobile app command: Curtain open")
                elif operation == "change_brightness_threshold":
                    state.set_threshold(FIELD_BRIGHTNESS, operation_value)
                elif operation == "chat":
                    # Handle chat command
                    self._handle_chat_operation(cs, state, operation_value)

                threshold = state.threshold_data
                logger.info(
                    "Mobile app threshold update: Temp=%s, Hum=%s, Brightness=%s",
                    threshold.get(FIELD_TEMPERATURE),
                    threshold.get(FIELD_HUMIDITY),
                    threshold.get(FIELD_BRIGHTNESS),
                )

        except (ConnectionError, ConnectionAbortedError, OSError) as error:
            logger.error("Mobile app receive connection disconnected: %s", error)
        except (ValueError, json.JSONDecodeError) as error:
            logger.error("Failed to parse mobile app command: %s", error)

    def _handle_chat_request(self, cs: socket.socket, user_info: dict, state: "GatewayState") -> None:
        """Handle chat request (independent entry point).

        Args:
            cs: TCP socket of mobile app.
            user_info: User info dictionary.
            state: Gateway shared state object.
        """
        try:
            # Check if AI Agent module is available
            if not all([self.dialog_manager, self.intent_planner, self.task_executor]):
                send_json(cs, {
                    "status": "error",
                    "message": "AI Agent module not initialized"
                })
                return

            # Create or get session
            session_id = user_info.get("session_id")
            if not session_id:
                session_id = self.dialog_manager.create_session(user_id=user_info.get("account"))

            send_json(cs, {
                "status": "ready",
                "session_id": session_id,
                "message": "Session created"
            })

        except Exception as error:
            logger.error("Failed to handle chat request: %s", error, exc_info=True)
            send_json(cs, {
                "status": "error",
                "message": f"Processing failed: {str(error)}"
            })

    def _handle_chat_operation(self, cs: socket.socket, state: "GatewayState", user_input: str) -> None:
        """Handle chat operation command.

        Args:
            cs: TCP socket of mobile app.
            state: Gateway shared state object.
            user_input: User input natural language command.
        """
        try:
            # Check if core components are available
            if not all([self.task_executor, self.device_controller]):
                send_json(cs, {
                    "type": "chat_response",
                    "status": "error",
                    "message": "AI Agent module not initialized"
                })
                return

            logger.info("Received chat command: %s", user_input)

            # 1. Get current device status
            device_state = self.device_controller.get_all_device_states()

            # 2. Call intent planner to generate task plan
            if self.intent_planner:
                # Use real LLM
                task_plan = self.intent_planner.quick_plan(user_input, device_state)
            else:
                # Use simulated intent parsing (keyword-based matching)
                task_plan = self._simulated_intent_parse(user_input, device_state)

            # 3. Execute tasks
            execution_result = self.task_executor.execute_task_plan(task_plan)

            # 4. Build response
            response = {
                "type": "chat_response",
                "status": "success" if execution_result["success"] else "error",
                "user_input": user_input,
                "reasoning": task_plan.get("reasoning", ""),
                "tasks": task_plan.get("tasks", []),
                "execution_result": execution_result,
                "message": execution_result.get("message", "Execution completed"),
                "cache_hit": task_plan.get("cache_hit", False),
                "cache_type": task_plan.get("cache_type", ""),
            }

            send_json(cs, response)
            logger.info("Chat response sent: %s", response["message"])

        except Exception as error:
            logger.error("Failed to handle chat operation: %s", error, exc_info=True)
            send_json(cs, {
                "type": "chat_response",
                "status": "error",
                "message": f"Processing failed: {str(error)}"
            })

    def _simulated_intent_parse(self, user_input: str, device_state: dict) -> dict:
        """Simulated intent parsing using keyword matching (fallback when LLM is unavailable).

        Args:
            user_input: User input natural language command.
            device_state: Current device status dictionary.

        Returns:
            Dict: Task plan with reasoning and tasks.
        """
        user_input_lower = user_input.lower()
        tasks = []
        reasoning = f"[模拟推理] 用户指令: '{user_input}'"

        # Keyword matching for common commands
        if any(kw in user_input_lower for kw in ["困", "睡", "休息", "晚安"]):
            reasoning += " -> 检测到睡眠场景"
            tasks.append({"device": "Light_TH", "action": "set_temperature", "value": 24})
            tasks.append({"device": "Curtain_status", "action": "close"})

        elif any(kw in user_input_lower for kw in ["空调", "温度"]) and any(kw in user_input_lower for kw in ["开", "打开", "启动"]):
            reasoning += " -> 检测到打开空调意图"
            tasks.append({"device": "Light_TH", "action": "turn_on"})

        elif any(kw in user_input_lower for kw in ["空调"]) and any(kw in user_input_lower for kw in ["关", "关闭", "停止"]):
            reasoning += " -> 检测到关闭空调意图"
            tasks.append({"device": "Light_TH", "action": "turn_off"})

        elif any(kw in user_input_lower for kw in ["温度", "度"]):
            import re
            temp_match = re.search(r'(\d+)\s*度', user_input)
            if temp_match:
                temp = int(temp_match.group(1))
                reasoning += f" -> 检测到设置温度意图: {temp}°C"
                tasks.append({"device": "Light_TH", "action": "set_temperature", "value": temp})
            else:
                reasoning += " -> 温度值未识别"
                tasks.append({"device": "Light_TH", "action": "turn_on"})

        elif any(kw in user_input_lower for kw in ["窗帘"]) and any(kw in user_input_lower for kw in ["开", "打开"]):
            reasoning += " -> 检测到打开窗帘意图"
            tasks.append({"device": "Curtain_status", "action": "open"})

        elif any(kw in user_input_lower for kw in ["窗帘"]) and any(kw in user_input_lower for kw in ["关", "关闭"]):
            reasoning += " -> 检测到关闭窗帘意图"
            tasks.append({"device": "Curtain_status", "action": "close"})

        elif any(kw in user_input_lower for kw in ["关闭所有", "全部关闭", "关闭全部"]):
            reasoning += " -> 检测到关闭所有设备意图"
            tasks.append({"device": "Light_TH", "action": "turn_off"})
            tasks.append({"device": "Curtain_status", "action": "close"})

        else:
            reasoning += " -> 未识别具体意图，默认打开空调"
            tasks.append({"device": "Light_TH", "action": "turn_on"})

        return {"reasoning": reasoning, "tasks": tasks}
