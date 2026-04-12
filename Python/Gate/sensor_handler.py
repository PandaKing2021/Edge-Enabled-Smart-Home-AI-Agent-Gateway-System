"""Device node communication handler module.

Responsible for TCP communication with IoT device nodes (sensors), including:
- Device node connection listening
- Device authentication
- Sensor data reception and processing
- Control command dispatch
- Door access security monitoring
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
    """Receive sensor data from device node (runs in independent thread).

    Receives device data in JSON format, updates gateway state, executes smart
    decision logic, and stores data in local database.

    Args:
        cs: TCP socket of device node.
        state: Gateway shared state object.
    """
    import time
    import database as db_module

    logger.info("Gateway receive thread started")

    try:
        while True:
            data_recv = recv_json(cs, BUFFER_SIZE_MEDIUM)

            # Parse device node data
            if not isinstance(data_recv, dict):
                logger.warning("Device data format error (expected dict): %s", type(data_recv).__name__)
                time.sleep(SENSOR_RECV_INTERVAL)
                continue

            state.update_data(data_recv)

            snapshot = state.get_data_snapshot()
            logger.info(
                "Received from device node: AC=%s, Temp=%s, Hum=%s, LightCU=%s, Brightness=%s, Curtain=%s",
                snapshot.get(FIELD_LIGHT_TH),
                snapshot.get(FIELD_TEMPERATURE),
                snapshot.get(FIELD_HUMIDITY),
                snapshot.get(FIELD_LIGHT_CU),
                snapshot.get(FIELD_BRIGHTNESS),
                snapshot.get(FIELD_CURTAIN_STATUS),
            )

            # Save data to local database
            db_module.save_sensor_data(db_module._gate_db_conn, snapshot)

            # Gateway smart decision
            _process_smart_decision(state, snapshot)

            time.sleep(SENSOR_RECV_INTERVAL)

    except (ConnectionError, OSError) as error:
        logger.error("Device node receive connection disconnected: %s", error)
    except json.JSONDecodeError as error:
        logger.error("Device node data JSON parsing failed: %s", error)
    except Exception as error:
        logger.error("Device node receive data exception: %s", error)


def send_to_sensor(cs: socket.socket, state: "GatewayState") -> None:
    """Send control commands to device node (runs in independent thread).

    Sends device status data in JSON format.

    Args:
        cs: TCP socket of device node.
        state: Gateway shared state object.
    """
    import time

    logger.info("Gateway send thread started")

    try:
        while True:
            data_send = state.get_data_snapshot()
            send_json(cs, data_send)
            logger.info("Sent to device node: %s", data_send)
            time.sleep(SENSOR_SEND_INTERVAL)

    except (ConnectionError, OSError) as error:
        logger.error("Device node send connection disconnected: %s", error)


def sensor_client_handler(cs: socket.socket, state: "GatewayState") -> None:
    """Handle connection of a single device node.

    Process: receive device ID → door access verification → device authentication → start send/receive threads.

    Args:
        cs: TCP socket of device node.
        state: Gateway shared state object.
    """
    import time

    try:
        # Get device node ID
        device_id = recv_line(cs).strip()

        # Door access security verification
        if state.door_permission == DOOR_DENIED:
            listen_door_security(device_id, cs, state)

        if device_id != "0":
            if state.is_device_permitted(device_id) and state.door_permission == DOOR_GRANTED:
                logger.info("Device node '%s' connected to gateway", device_id)
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
                    logger.warning("Device node '%s' not authorized for this user, connection denied", device_id)
                elif state.door_permission == DOOR_DENIED:
                    logger.warning("Door access not activated, device node '%s' connection failed", device_id)
        else:
            logger.warning("Device node connection denied")

    except (ConnectionError, OSError) as error:
        logger.error("Device node connection handling disconnected: %s", error)
    except Exception as error:
        logger.error("Device node handling exception: %s", error)
    finally:
        cs.close()


def sensor_handler(gate_config, state: "GatewayState") -> None:
    """Device node communication main listening thread.

    Listens for TCP connections from device nodes on specified port.

    Args:
        gate_config: Gateway network configuration.
        state: Gateway shared state object.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((gate_config.ip, gate_config.source_port))
    s.listen(LISTEN_BACKLOG)
    logger.info("Device node communication port opened: %s:%d", gate_config.ip, gate_config.source_port)

    try:
        while True:
            cs, addr = s.accept()
            logger.info("Device node connection: %s", addr)
            thread = threading.Thread(
                target=sensor_client_handler, args=(cs, state), daemon=True
            )
            thread.start()

    except OSError as error:
        logger.error("Device node listening exception: %s", error)


def listen_door_security(device_id: str, cs: socket.socket, state: "GatewayState") -> None:
    """Blocking door access status listening.

    If the connecting device is a door access device, wait for door access verification to pass;
    If it's a non-door access device, block and wait for door access to pass.

    Args:
        device_id: Device identifier.
        cs: TCP socket of device node.
        state: Gateway shared state object.
    """
    import time

    if "security" in device_id:
        logger.info("Door access device detected")
        while True:
            try:
                recv_data = recv_json(cs)
                security_status = recv_data.get(FIELD_DOOR_STATUS, 0)

                if int(security_status) == DOOR_GRANTED:
                    logger.info("User door access granted")
                    state.door_permission = DOOR_GRANTED
                    state.update_data(recv_data)
                    break
                else:
                    logger.info("User door access denied")
                    time.sleep(1)
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning("Door access data parsing failed: %s", e)
                time.sleep(1)
            except (ConnectionError, OSError):
                logger.error("Door access device connection disconnected")
                break
    else:
        logger.info("Non-door access device detected, waiting for door access")
        # Use Event instead of busy waiting
        if not state.wait_for_sensor(timeout=None):
            logger.warning("Waiting for door access timeout")


def _process_smart_decision(state: "GatewayState", snapshot: dict) -> None:
    """Gateway smart decision logic.

    Automatically control devices based on sensor data and thresholds:
    - Temperature/humidity exceeds threshold → turn on AC (Light_TH=1), otherwise turn off
    - Brightness exceeds threshold → turn off light sensor and open curtain, otherwise reverse

    Args:
        state: Gateway shared state object.
        snapshot: Current sensor data snapshot.
    """
    threshold = state.threshold_data
    status_updates = {}

    # Temperature/humidity decision
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

    # Brightness decision
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
