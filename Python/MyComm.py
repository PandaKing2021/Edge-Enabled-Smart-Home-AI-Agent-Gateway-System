"""IoT 网关通信协议编解码模块。

所有 TCP 通信统一使用 JSON 格式，消息以 ``\\n`` (LF) 分隔。

协议结构（命令/响应类）::

    {"op": "操作码", "data": <载荷>, "status": <状态码>}

旧协议 ``"op|data|status"`` 已被 JSON 格式完全替代。
用户数据旧格式 ``"user+pwd+key"`` 已被 JSON 对象 ``{"username":...,"password":...,"device_key":...}`` 替代。

本模块保留四个核心函数签名和返回值格式，以便兼容上层调用。
"""

from common.protocol import (
    pack_command,
    unpack_command,
    pack_user_data,
    unpack_user_data,
)


def format_comm_data_string(operation: str, data, status_code) -> dict:
    """构造命令 JSON 对象（兼容旧接口名称）。

    将操作码、数据码、状态码打包为 ``{"op":..., "data":..., "status":...}`` JSON 对象。

    Args:
        operation: 操作码（如 ``"add_new_user"``、``"check_userconfig_illegal"``）。
        data: 载荷数据。
        status_code: 状态码。

    Returns:
        命令字典（可直接用 ``json.dumps()`` 序列化）。
    """
    return pack_command(operation, data, status_code)


def format_userdata_string(username: str, password: str, device_key: str) -> dict:
    """构造用户信息 JSON 对象（兼容旧接口名称）。

    Args:
        username: 用户名。
        password: 密码。
        device_key: 设备密钥。

    Returns:
        用户信息字典。
    """
    return pack_user_data(username, password, device_key)


def decode_comm_data(message) -> tuple:
    """解包命令 JSON 对象（兼容旧接口名称）。

    Args:
        message: 命令字典或已解析的 JSON 对象。

    Returns:
        元组 ``(operation, data, status_code)``。

    Raises:
        ValueError: 数据格式错误。
    """
    return unpack_command(message)


def decode_user_data(data) -> tuple:
    """解包用户信息 JSON 对象（兼容旧接口名称）。

    Args:
        data: 用户信息字典。

    Returns:
        元组 ``(username, password, device_key)``。

    Raises:
        ValueError: 数据格式错误。
    """
    return unpack_user_data(data)
