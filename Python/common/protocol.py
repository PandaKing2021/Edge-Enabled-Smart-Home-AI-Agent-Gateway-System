"""IoT 网关系统 JSON 通信协议工具模块。

所有 TCP 通信统一使用 JSON 格式，消息以 ``\\n`` (LF) 作为分隔符。

消息格式（命令/响应类）::

    {"op": "操作码", "data": <载荷>, "status": <状态码>}

消息格式（数据流推送类）::

    {"field1": value1, "field2": value2, ...}

提供标准化的 Socket 收发函数，替代原始的 ``send()`` / ``recv()`` 调用。
"""

import json
import logging
import socket
from typing import Any, Dict, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# 消息终止符
MSG_TERMINATOR = b"\n"

# 默认接收缓冲区大小
DEFAULT_RECV_BUF = 4096


# ---------------------------------------------------------------------------
# 低层 Socket 收发
# ---------------------------------------------------------------------------

def send_line(sock: socket.socket, message: str) -> None:
    """向 Socket 发送一行文本（自动追加 ``\\n`` 终止符）。

    使用 ``sendall()`` 确保所有字节被发送。

    Args:
        sock: TCP 套接字。
        message: 要发送的文本消息（不应包含 ``\\n``）。

    Raises:
        ConnectionError: 连接已断开。
    """
    data = message.encode("utf-8") + MSG_TERMINATOR
    try:
        sock.sendall(data)
    except OSError as exc:
        raise ConnectionError(f"发送失败: {exc}") from exc


def recv_line(sock: socket.socket, bufsize: int = DEFAULT_RECV_BUF) -> str:
    """从 Socket 读取一行文本（以 ``\\n`` 为终止符）。

    持续读取直到遇到 ``\\n``，自动处理 TCP 粘包/半包。

    Args:
        sock: TCP 套接字。
        bufsize: 每次接收的最大字节数。

    Returns:
        去除终止符后的文本字符串。

    Raises:
        ConnectionError: 连接已断开（对端关闭）。
    """
    chunks: list[bytes] = []
    while True:
        try:
            chunk = sock.recv(bufsize)
        except OSError as exc:
            raise ConnectionError(f"接收失败: {exc}") from exc

        if not chunk:
            raise ConnectionError("对端已关闭连接")

        chunks.append(chunk)
        # 检查是否收到完整的一行
        combined = b"".join(chunks)
        if MSG_TERMINATOR in combined:
            line = combined[: combined.index(MSG_TERMINATOR)]
            return line.decode("utf-8")


# ---------------------------------------------------------------------------
# JSON 编解码
# ---------------------------------------------------------------------------

def send_json(sock: socket.socket, obj: Any) -> None:
    """将 Python 对象序列化为 JSON 并发送一行。

    Args:
        sock: TCP 套接字。
        obj: 可 JSON 序列化的 Python 对象。
    """
    send_line(sock, json.dumps(obj, ensure_ascii=False))


def recv_json(sock: socket.socket, bufsize: int = DEFAULT_RECV_BUF) -> Any:
    """接收一行文本并反序列化为 Python 对象。

    Args:
        sock: TCP 套接字。
        bufsize: 每次接收的最大字节数。

    Returns:
        反序列化后的 Python 对象（通常是 dict 或 list）。

    Raises:
        json.JSONDecodeError: 数据不是合法 JSON。
        ConnectionError: 连接已断开。
    """
    line = recv_line(sock, bufsize)
    try:
        return json.loads(line)
    except json.JSONDecodeError as exc:
        logger.error("JSON 解析失败: %s (原始数据: %s)", exc, line[:200])
        raise


# ---------------------------------------------------------------------------
# 命令/响应协议封包与解包
# ---------------------------------------------------------------------------

def pack_command(op: str, data: Any = None, status: int = 1) -> Dict[str, Any]:
    """构造标准命令 JSON 对象。

    Args:
        op: 操作码（如 ``"login"``、``"check_device_id"``）。
        data: 载荷数据（任意可序列化类型）。
        status: 状态码（默认 1）。

    Returns:
        命令字典。
    """
    return {"op": op, "data": data, "status": status}


def unpack_command(message: Dict[str, Any]) -> Tuple[str, Any, Any]:
    """解包标准命令 JSON 对象。

    Args:
        message: 命令字典。

    Returns:
        元组 ``(op, data, status)``。

    Raises:
        ValueError: 消息缺少必要字段。
    """
    if not isinstance(message, dict):
        raise ValueError(f"命令格式错误，期望 dict，实际 {type(message).__name__}")

    op = message.get("op")
    data = message.get("data")
    status = message.get("status")

    if op is None:
        raise ValueError(f"命令缺少 'op' 字段: {message}")

    return op, data, status


def pack_user_data(username: str, password: str, device_key: str) -> Dict[str, str]:
    """构造用户信息 JSON 对象（替代旧的 ``user+pwd+key`` 格式）。

    Args:
        username: 用户名。
        password: 密码。
        device_key: 设备密钥。

    Returns:
        用户信息字典。
    """
    return {"username": username, "password": password, "device_key": device_key}


def unpack_user_data(data: Any) -> Tuple[str, str, str]:
    """解包用户信息 JSON 对象。

    Args:
        data: 用户信息字典。

    Returns:
        元组 ``(username, password, device_key)``。

    Raises:
        ValueError: 数据格式错误。
    """
    if not isinstance(data, dict):
        raise ValueError(f"用户数据格式错误，期望 dict，实际 {type(data).__name__}")

    username = data.get("username", "")
    password = data.get("password", "")
    device_key = data.get("device_key", "")

    if not username:
        raise ValueError(f"用户数据缺少 'username' 字段: {data}")

    return username, password, device_key
