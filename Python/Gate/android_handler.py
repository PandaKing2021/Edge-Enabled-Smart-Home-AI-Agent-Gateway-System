"""移动应用(Android)通信处理模块。

负责与 Android 移动应用的 TCP 通信，包括：
- 移动应用连接监听
- 用户登录/注册
- 阈值设置
- 设备数据推送
- AI Agent对话交互
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
    """移动应用通信处理器。

    封装移动应用相关的通信逻辑，持有数据库服务器套接字引用。

    Attributes:
        db_socket: 与数据库服务器的 TCP 套接字。
        config_dir: 配置文件目录。
        dialog_manager: 对话管理器实例。
        intent_planner: 意图解析器实例。
        task_executor: 任务执行器实例。
        device_controller: 设备控制器实例。
        preference_manager: 偏好管理器实例。
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
        """移动应用通信主监听线程。

        Args:
            gate_network_config: 网关网络配置。
            state: 网关共享状态对象。
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((gate_network_config.ip, gate_network_config.android_port))
        s.listen(LISTEN_BACKLOG)
        logger.info("移动应用通信端口已开启: %s:%d",
                     gate_network_config.ip, gate_network_config.android_port)

        while True:
            try:
                cs, addr = s.accept()
                logger.info("移动应用连接: %s", addr)
                thread = threading.Thread(
                    target=self._client_handler, args=(cs, state), daemon=True
                )
                thread.start()
            except OSError as error:
                logger.error("移动应用监听异常: %s", error)

    def _client_handler(self, cs: socket.socket, state: "GatewayState") -> None:
        """处理单个移动应用连接。

        Args:
            cs: 移动应用的 TCP 套接字。
            state: 网关共享状态对象。
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
            logger.error("解析移动应用数据失败: %s", error)
        except (ConnectionError, OSError) as error:
            logger.error("移动应用连接断开: %s", error)
        except Exception as error:
            logger.error("移动应用通信异常: %s", error)
        finally:
            cs.close()

    def _android_login(self, cs: socket.socket, curr_user: dict, state: "GatewayState") -> None:
        """处理用户登录。

        Args:
            cs: 移动应用的 TCP 套接字。
            curr_user: 用户信息字典，需包含 "account" 和 "password" 键。
            state: 网关共享状态对象。
        """
        try:
            user_config = load_user_config(config_dir=self.config_dir)
        except FileNotFoundError:
            user_config = UserConfig()

        if user_config.username == curr_user["account"] and user_config.password == curr_user["password"]:
            send_json(cs, {"status": 1})
            state.login_status = 1
            logger.info("用户 '%s' 登录成功", curr_user["account"])

            # 等待设备节点连接
            state.wait_for_sensor()

            # 启动收发线程
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
            logger.warning("用户 '%s' 登录失败", curr_user["account"])

    def _android_register(self, cs: socket.socket, given_user: dict) -> None:
        """处理用户注册。

        流程：将用户信息发送到数据库服务器 → 根据结果更新本地配置。

        Args:
            cs: 移动应用的 TCP 套接字。
            given_user: 用户信息字典，需包含 "account"、"password"、"device_Key" 键。
        """
        logger.info("用户正在注册: %s", given_user.get("account"))

        # 构造并发送注册请求到数据库服务器
        db_data_send = format_comm_data_string(
            "add_new_user",
            format_userdata_string(given_user["account"], given_user["password"], given_user["device_Key"]),
            1,
        )
        send_json(self.db_socket, db_data_send)
        logger.info("向数据库服务器发送: %s", db_data_send)

        # 接收数据库服务器响应
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
                logger.info("注册成功，用户信息已更新")
                send_json(cs, {"status": 1})
            elif status_code in (0, 2):
                logger.warning("注册失败: %s", data)
                send_json(cs, {"status": 0})
        except (ConnectionError, OSError) as error:
            logger.error("注册过程连接断开: %s", error)
            send_json(cs, {"status": 0})
        except Exception as error:
            logger.error("注册过程异常: %s", error)
            send_json(cs, {"status": 0})

    def _send_to_android(self, cs: socket.socket, state: "GatewayState") -> None:
        """向移动应用推送设备数据。

        使用 JSON 格式发送传感器数据。

        Args:
            cs: 移动应用的 TCP 套接字。
            state: 网关共享状态对象。
        """
        import time

        logger.info("移动应用发送子线程开启")

        try:
            while True:
                data = state.get_data_snapshot()
                send_json(cs, data)
                logger.info("向移动应用发送: %s", data)
                time.sleep(ANDROID_SEND_INTERVAL)

        except (ConnectionError, ConnectionAbortedError, OSError) as error:
            logger.error("移动应用发送连接断开: %s", error)

    def _get_from_android(self, cs: socket.socket, state: "GatewayState") -> None:
        """从移动应用接收控制指令。

        解析操作码并更新阈值数据：
        - light_th_open/close: 智能空调开关
        - change_temperature_threshold: 温度阈值
        - change_humidity_threshold: 湿度阈值
        - curtain_open/close: 窗帘控制
        - change_brightness_threshold: 光照度阈值

        Args:
            cs: 移动应用的 TCP 套接字。
            state: 网关共享状态对象。
        """
        import time

        logger.info("移动应用接收子线程开启")

        try:
            while True:
                recv_data = recv_json(cs)
                operation, operation_value, _ = decode_comm_data(recv_data)

                if operation == "light_th_open":
                    state.set_threshold(FIELD_TEMPERATURE, -1)
                    state.set_threshold(FIELD_HUMIDITY, -1)
                    logger.info("移动应用指令: 智能空调灯光开启")
                elif operation == "light_th_close":
                    state.set_threshold(FIELD_TEMPERATURE, 101)
                    state.set_threshold(FIELD_HUMIDITY, 101)
                    logger.info("移动应用指令: 智能空调灯光关闭")
                elif operation == "change_temperature_threshold":
                    state.set_threshold(FIELD_TEMPERATURE, operation_value)
                elif operation == "change_humidity_threshold":
                    state.set_threshold(FIELD_HUMIDITY, operation_value)
                elif operation == "curtain_close":
                    state.set_threshold(FIELD_BRIGHTNESS, 65535)
                    logger.info("移动应用指令: 窗帘关闭")
                elif operation == "curtain_open":
                    state.set_threshold(FIELD_BRIGHTNESS, -2)
                    logger.info("移动应用指令: 窗帘开启")
                elif operation == "change_brightness_threshold":
                    state.set_threshold(FIELD_BRIGHTNESS, operation_value)
                elif operation == "chat":
                    # 处理对话指令
                    self._handle_chat_operation(cs, state, operation_value)

                threshold = state.threshold_data
                logger.info(
                    "移动应用阈值更新: 温度=%s, 湿度=%s, 光照=%s",
                    threshold.get(FIELD_TEMPERATURE),
                    threshold.get(FIELD_HUMIDITY),
                    threshold.get(FIELD_BRIGHTNESS),
                )

        except (ConnectionError, ConnectionAbortedError, OSError) as error:
            logger.error("移动应用接收连接断开: %s", error)
        except (ValueError, json.JSONDecodeError) as error:
            logger.error("解析移动应用指令失败: %s", error)

    def _handle_chat_request(self, cs: socket.socket, user_info: dict, state: "GatewayState") -> None:
        """处理对话请求(独立入口)。

        Args:
            cs: 移动应用的 TCP 套接字。
            user_info: 用户信息字典。
            state: 网关共享状态对象。
        """
        try:
            # 检查AI Agent模块是否可用
            if not all([self.dialog_manager, self.intent_planner, self.task_executor]):
                send_json(cs, {
                    "status": "error",
                    "message": "AI Agent模块未初始化"
                })
                return

            # 创建或获取会话
            session_id = user_info.get("session_id")
            if not session_id:
                session_id = self.dialog_manager.create_session(user_id=user_info.get("account"))

            send_json(cs, {
                "status": "ready",
                "session_id": session_id,
                "message": "会话已创建"
            })

        except Exception as error:
            logger.error("处理对话请求失败: %s", error, exc_info=True)
            send_json(cs, {
                "status": "error",
                "message": f"处理失败: {str(error)}"
            })

    def _handle_chat_operation(self, cs: socket.socket, state: "GatewayState", user_input: str) -> None:
        """处理对话操作指令。

        Args:
            cs: 移动应用的 TCP 套接字。
            state: 网关共享状态对象。
            user_input: 用户输入的自然语言指令。
        """
        try:
            # 检查AI Agent模块是否可用
            if not all([self.dialog_manager, self.intent_planner, self.task_executor, self.device_controller]):
                send_json(cs, {
                    "type": "chat_response",
                    "status": "error",
                    "message": "AI Agent模块未初始化"
                })
                return

            logger.info("收到对话指令: %s", user_input)

            # 1. 获取当前设备状态
            device_state = self.device_controller.get_all_device_states()

            # 2. 调用意图解析器生成任务计划
            task_plan = self.intent_planner.quick_plan(user_input, device_state)

            # 3. 执行任务
            execution_result = self.task_executor.execute_task_plan(task_plan)

            # 4. 构建响应
            response = {
                "type": "chat_response",
                "status": "success" if execution_result["success"] else "error",
                "user_input": user_input,
                "reasoning": task_plan.get("reasoning", ""),
                "tasks": task_plan.get("tasks", []),
                "execution_result": execution_result,
                "message": execution_result.get("message", "执行完成")
            }

            send_json(cs, response)
            logger.info("对话响应已发送: %s", response["message"])

        except Exception as error:
            logger.error("处理对话操作失败: %s", error, exc_info=True)
            send_json(cs, {
                "type": "chat_response",
                "status": "error",
                "message": f"处理失败: {str(error)}"
            })
