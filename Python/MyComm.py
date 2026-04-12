"""IoT gateway communication protocol codec module.

All TCP communication uniformly uses JSON format, messages are separated by ``\\n`` (LF).

Protocol structure (command/response class)::

    {"op": "operation code", "data": <payload>, "status": <status code>}

Old protocol ``"op|data|status"`` has been completely replaced by JSON format.
User data old format ``"user+pwd+key"`` has been replaced by JSON object ``{"username":...,"password":...,"device_key":...}``.

This module retains four core function signatures and return value formats for compatibility with upper-level calls.
"""

from common.protocol import (
    pack_command,
    unpack_command,
    pack_user_data,
    unpack_user_data,
)


def format_comm_data_string(operation: str, data, status_code) -> dict:
    """Construct command JSON object (compatible with old interface name).

    Pack operation code, data code, status code into ``{"op":..., "data":..., "status":...}`` JSON object.

    Args:
        operation: Operation code (e.g., ``"add_new_user"``, ``"check_userconfig_illegal"``).
        data: Payload data.
        status_code: Status code.

    Returns:
        Command dictionary (can be directly serialized with ``json.dumps()``).
    """
    return pack_command(operation, data, status_code)


def format_userdata_string(username: str, password: str, device_key: str) -> dict:
    """Construct user information JSON object (compatible with old interface name).

    Args:
        username: Username.
        password: Password.
        device_key: Device key.

    Returns:
        User information dictionary.
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
    """Unpack user information JSON object (compatible with old interface name).

    Args:
        data: User information dictionary.

    Returns:
        Tuple ``(username, password, device_key)``.

    Raises:
        ValueError: Data format error.
    """
    return unpack_user_data(data)
