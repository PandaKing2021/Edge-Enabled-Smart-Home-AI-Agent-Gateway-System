"""设备节点通信处理模块。

负责与 IoT 设备节点（传感器）的 TCP 通信，包括：
- 设备节点连接监听
- 设备身份验证
- 传感器数据接收与处理
- 控制指令下发
- 门禁安全监听
"""

import json
import logging
import socket
import threading
from typing import TYPE_CHECKING

from common.constants import (
    BUFFER_SIZE_MEDIUM,
    DOOR_DENIED,
    DOOR_GRANTED,
    FIELD_BRIGHTNESS,
    FIELD_CURTAIN_STATUS,
    FIELD_DEVICE_KEY,
    FIELD_DOOR_STATUS,
    FIELD_HUMIDITY,
    FIELD_LIGHT_CU,
    FIELD_LIGHT_TH,
    FIELD_TEMPERATURE,
    LISTEN_BACKLOG,
    SENSOR_RECV_INTERVAL,
    SENSOR_SEND_INTERVAL,
)
from common.protocol import send_json, recv_json, send_line, recv_line

if TYPE_CHECKING:
    from common.models import GatewayState

logger = logging.getLogger(__name__)


def get_from_sensor(cs: socket.socket, state: "GatewayState") -> None:
    """从设备节点接收传感器数据（运行在独立线程中）。

    接收 JSON 格式的设备数据，更新网关状态，执行智能决策逻辑，
    并将数据存入本地数据库。

    Args:
        cs: 设备节点的 TCP 套接字。
        state: 网关共享状态对象。
    """
    import time
    import database as db_module

    logger.info("网关接收线程启动")

    try:
        while True:
            data_recv = recv_json(cs, BUFFER_SIZE_MEDIUM)

            # 解析设备节点数据
            if not isinstance(data_recv, dict):
                logger.warning("设备数据格式错误（期望 dict）: %s", type(data_recv).__name__)
                time.sleep(SENSOR_RECV_INTERVAL)
                continue

            state.update_data(data_recv)

            snapshot = state.get_data_snapshot()
            logger.info(
                "从设备节点接收: 空调=%s, 温度=%s, 湿度=%s, 光感灯=%s, 光照=%s, 窗帘=%s",
                snapshot.get(FIELD_LIGHT_TH),
                snapshot.get(FIELD_TEMPERATURE),
                snapshot.get(FIELD_HUMIDITY),
                snapshot.get(FIELD_LIGHT_CU),
                snapshot.get(FIELD_BRIGHTNESS),
                snapshot.get(FIELD_CURTAIN_STATUS),
            )

            # 数据存入本地数据库
            db_module.save_sensor_data(db_module._gate_db_conn, snapshot)

            # 网关智能决策
            _process_smart_decision(state, snapshot)

            time.sleep(SENSOR_RECV_INTERVAL)

    except (ConnectionError, OSError) as error:
        logger.error("设备节点接收数据连接断开: %s", error)
    except json.JSONDecodeError as error:
        logger.error("设备节点数据 JSON 解析失败: %s", error)
    except Exception as error:
        logger.error("设备节点接收数据异常: %s", error)


def send_to_sensor(cs: socket.socket, state: "GatewayState") -> None:
    """向设备节点发送控制指令（运行在独立线程中）。

    使用 JSON 格式发送设备状态数据。

    Args:
        cs: 设备节点的 TCP 套接字。
        state: 网关共享状态对象。
    """
    import time

    logger.info("网关发送线程启动")

    try:
        while True:
            data_send = state.get_data_snapshot()
            send_json(cs, data_send)
            logger.info("向设备节点发送: %s", data_send)
            time.sleep(SENSOR_SEND_INTERVAL)

    except (ConnectionError, OSError) as error:
        logger.error("设备节点发送数据连接断开: %s", error)


def sensor_client_handler(cs: socket.socket, state: "GatewayState") -> None:
    """处理单个设备节点的连接。

    流程：接收设备ID → 门禁验证 → 设备身份验证 → 启动收发线程。

    Args:
        cs: 设备节点的 TCP 套接字。
        state: 网关共享状态对象。
    """
    import time

    try:
        # 获取设备节点ID
        device_id = recv_line(cs).strip()

        # 门禁安全验证
        if state.door_permission == DOOR_DENIED:
            listen_door_security(device_id, cs, state)

        if device_id != "0":
            if state.is_device_permitted(device_id) and state.door_permission == DOOR_GRANTED:
                logger.info("设备节点 '%s' 已连入网关", device_id)
                state.source_start_flag = 1
                send_line(cs, "start")

                recv_thread = threading.Thread(
                    target=get_from_sensor, args=(cs, state), daemon=True
                )
                send_thread = threading.Thread(
                    target=send_to_sensor, args=(cs, state), daemon=True
                )
                recv_thread.start()
                send_thread.start()
                recv_thread.join()
                send_thread.join()

            else:
                if not state.is_device_permitted(device_id):
                    logger.warning("设备节点 '%s' 不属于本用户，拒绝连接", device_id)
                elif state.door_permission == DOOR_DENIED:
                    logger.warning("门禁未激活，设备节点 '%s' 进入失败", device_id)
        else:
            logger.warning("设备节点拒绝连接")

    except (ConnectionError, OSError) as error:
        logger.error("设备节点处理连接断开: %s", error)
    except Exception as error:
        logger.error("设备节点处理异常: %s", error)
    finally:
        cs.close()


def sensor_handler(gate_config, state: "GatewayState") -> None:
    """设备节点通信主监听线程。

    在指定端口上监听设备节点的 TCP 连接。

    Args:
        gate_config: 网关网络配置。
        state: 网关共享状态对象。
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((gate_config.ip, gate_config.source_port))
    s.listen(LISTEN_BACKLOG)
    logger.info("设备节点通信端口已开启: %s:%d", gate_config.ip, gate_config.source_port)

    try:
        while True:
            cs, addr = s.accept()
            logger.info("设备节点连接: %s", addr)
            thread = threading.Thread(
                target=sensor_client_handler, args=(cs, state), daemon=True
            )
            thread.start()

    except OSError as error:
        logger.error("设备节点监听异常: %s", error)


def listen_door_security(device_id: str, cs: socket.socket, state: "GatewayState") -> None:
    """阻塞式门禁状态监听。

    如果接入的是门禁设备，等待门禁验证通过；
    如果是非门禁设备，阻塞等待门禁通过。

    Args:
        device_id: 设备标识。
        cs: 设备节点的 TCP 套接字。
        state: 网关共享状态对象。
    """
    import time

    if "security" in device_id:
        logger.info("发现门禁设备接入")
        while True:
            try:
                recv_data = recv_json(cs)
                security_status = recv_data.get(FIELD_DOOR_STATUS, 0)

                if int(security_status) == DOOR_GRANTED:
                    logger.info("用户门禁通过")
                    state.door_permission = DOOR_GRANTED
                    state.update_data(recv_data)
                    break
                else:
                    logger.info("用户门禁未通过")
                    time.sleep(1)
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning("门禁数据解析失败: %s", e)
                time.sleep(1)
            except (ConnectionError, OSError):
                logger.error("门禁设备连接断开")
                break
    else:
        logger.info("发现非门禁设备接入，等待门禁通过")
        # 使用 Event 替代忙等待
        if not state.wait_for_sensor(timeout=None):
            logger.warning("等待门禁超时")


def _process_smart_decision(state: "GatewayState", snapshot: dict) -> None:
    """网关智能决策逻辑。

    根据传感器数据和阈值自动控制设备：
    - 温湿度超过阈值 → 开启空调（Light_TH=1），否则关闭
    - 光照度超过阈值 → 关闭光感灯并打开窗帘，否则反向操作

    Args:
        state: 网关共享状态对象。
        snapshot: 当前传感器数据快照。
    """
    threshold = state.threshold_data
    status_updates = {}

    # 温湿度决策
    temp = float(snapshot.get(FIELD_TEMPERATURE, 0))
    humidity = float(snapshot.get(FIELD_HUMIDITY, 0))
    temp_threshold = float(threshold.get(FIELD_TEMPERATURE, 0))
    humidity_threshold = float(threshold.get(FIELD_HUMIDITY, 0))
    current_light_th = int(snapshot.get(FIELD_LIGHT_TH, 0))

    if temp >= temp_threshold and humidity >= humidity_threshold:
        if current_light_th == 0:
            status_updates[FIELD_LIGHT_TH] = 1
    else:
        if current_light_th == 1:
            status_updates[FIELD_LIGHT_TH] = 0

    # 光照度决策
    brightness = float(snapshot.get(FIELD_BRIGHTNESS, 0))
    brightness_threshold = float(threshold.get(FIELD_BRIGHTNESS, 0))
    current_light_cu = int(snapshot.get(FIELD_LIGHT_CU, 0))
    current_curtain = int(snapshot.get(FIELD_CURTAIN_STATUS, 1))

    if brightness >= brightness_threshold:
        if current_light_cu == 1 and current_curtain == 0:
            status_updates[FIELD_LIGHT_CU] = 0
            status_updates[FIELD_CURTAIN_STATUS] = 1
    else:
        if current_light_cu == 0 and current_curtain == 1:
            status_updates[FIELD_LIGHT_CU] = 1
            status_updates[FIELD_CURTAIN_STATUS] = 0

    if status_updates:
        state.update_status(status_updates)
        state.update_data(status_updates)
