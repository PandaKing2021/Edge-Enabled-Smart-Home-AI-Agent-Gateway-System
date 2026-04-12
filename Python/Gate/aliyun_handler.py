"""阿里云 IoT 通信模块。

负责通过 MQTT 协议将传感器数据上传到阿里云 IoT 平台。
"""

import hashlib
import hmac as hmac_mod
import json
import logging
import time
from typing import Any, Dict, Optional

import paho.mqtt.client as mqtt

from common.constants import (
    ALIYUN_MQTT_PORT,
    ALIYUN_UPLOAD_INTERVAL,
    FIELD_BRIGHTNESS,
    FIELD_CURTAIN_STATUS,
    FIELD_HUMIDITY,
    FIELD_LIGHT_CU,
    FIELD_LIGHT_TH,
    FIELD_TEMPERATURE,
)
from common.config import AliyunIotConfig

logger = logging.getLogger(__name__)


def hmacsha1(key: str, msg: str) -> str:
    """计算 HMAC-SHA1 签名。

    Args:
        key: 密钥。
        msg: 消息内容。

    Returns:
        十六进制签名字符串。
    """
    return hmac_mod.new(key.encode("utf-8"), msg.encode("utf-8"), hashlib.sha1).hexdigest()


def create_mqtt_client(iot_config: AliyunIotConfig) -> Optional[mqtt.Client]:
    """创建阿里云 IoT MQTT 客户端。

    使用 HMAC-SHA1 鉴权方式生成客户端凭证。

    Args:
        iot_config: 阿里云 IoT 配置。

    Returns:
        配置好凭证的 MQTT 客户端，创建失败时返回 None。
    """
    timestamp = str(int(time.time()))
    client_id = f"paho.py|securemode=3,signmethod=hmacsha1,timestamp={timestamp}|"
    content_str = (
        f"clientIdpaho.py"
        f"deviceName{iot_config.device_name}"
        f"productKey{iot_config.product_key}"
        f"timestamp{timestamp}"
    )
    username = f"{iot_config.device_name}&{iot_config.product_key}"
    password = hmacsha1(iot_config.device_secret, content_str)

    try:
        client = mqtt.Client(client_id=client_id, clean_session=False)
        client.username_pw_set(username, password)
        return client
    except Exception as error:
        logger.error("创建 MQTT 客户端失败: %s", error)
        return None


def on_connect(client, userdata, flags, rc):
    """MQTT 连接回调。"""
    logger.info("阿里云 IoT 连接结果: %d", rc)


def on_message(client, userdata, msg):
    """MQTT 消息回调。"""
    logger.info("阿里云 IoT 收到消息: %s %s", msg.topic, msg.payload)


def aliyun_upload_loop(
    iot_config: AliyunIotConfig,
    get_data_fn,
    wait_for_sensor_fn,
) -> None:
    """阿里云数据上传主循环（运行在独立线程中）。

    阻塞等待设备节点连接后，定期将传感器数据上传到阿里云 IoT。

    Args:
        iot_config: 阿里云 IoT 配置。
        get_data_fn: 获取传感器数据快照的回调函数。
        wait_for_sensor_fn: 等待设备节点连接的回调函数。
    """
    host = f"{iot_config.product_key}.iot-as-mqtt.{iot_config.region_id}.aliyuncs.com"
    pub_topic = (
        f"/sys/{iot_config.product_key}/{iot_config.device_name}/thing/event/property/post"
    )

    client = create_mqtt_client(iot_config)
    if client is None:
        logger.error("无法创建 MQTT 客户端，阿里云上传线程退出")
        return

    client.on_connect = on_connect
    client.on_message = on_message

    logger.info("阿里云上传线程启动，等待设备节点连接...")
    wait_for_sensor_fn()
    logger.info("开始向阿里云服务器发送数据")

    timestamp = 0
    while True:
        timestamp += 1
        try:
            client.reconnect()
            data = get_data_fn()

            payload_json = {
                "id": timestamp,
                "params": {
                    "Light_TH": data.get(FIELD_LIGHT_TH, 0),
                    "Temperature": data.get(FIELD_TEMPERATURE, 0),
                    "Humidity": data.get(FIELD_HUMIDITY, 0),
                    "Light_CU": data.get(FIELD_LIGHT_CU, 0),
                    "Brightness": data.get(FIELD_BRIGHTNESS, 0),
                    "Curtain_status": data.get(FIELD_CURTAIN_STATUS, 1),
                },
                "method": "thing.event.property.post",
            }

            client.publish(pub_topic, payload=json.dumps(payload_json), qos=1)
            logger.info("向阿里云 IoT 发送: %s", payload_json)

        except Exception as error:
            logger.error("阿里云数据上传失败: %s", error)

        time.sleep(ALIYUN_UPLOAD_INTERVAL)
