"""IoT gateway system JSON communication protocol utility module.

All TCP communication uniformly uses JSON format, messages separated by ``\\n`` (LF).

Message format (command/response type)::

    {"op": "operation_code", "data": <payload>, "status": <status_code>}

Message format (data stream push type)::

    {"field1": value1, "field2": value2, ...}

Provides standardized Socket send/receive functions, replacing original ``send()`` / ``recv()`` calls.
"""

import json
import logging
import socket
from typing import Any, Dict, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Message terminator
MSG_TERMINATOR = b"\n"

# Default receive buffer size
DEFAULT_RECV_BUF = 4096


# ---------------------------------------------------------------------------
# Low-level Socket send/receive
# ---------------------------------------------------------------------------

def send_line(sock: socket.socket, message: str) -> None:
    """Send a line of text to Socket (automatically append ``\\n`` terminator).

    Use ``sendall()`` to ensure all bytes are sent.

    Args:
        sock: TCP socket.
        message: Text message to send (should not contain ``\\n``).

    Raises:
        ConnectionError: Connection has been disconnected.
    """
    data = message.encode("utf-8") + MSG_TERMINATOR
    try:
        sock.sendall(data)
    except OSError as exc:
        raise ConnectionError(f"Send failed: {exc}") from exc


def recv_line(sock: socket.socket, bufsize: int = DEFAULT_RECV_BUF) -> str:
    """Read a line of text from Socket (terminated by ``\\n``).

    Continuously read until ``\\n`` is encountered, automatically handling TCP sticky/partial packets.

    Args:
        sock: TCP socket.
        bufsize: Maximum number of bytes to receive each time.

    Returns:
        Text string with terminator removed.

    Raises:
        ConnectionError: Connection has been disconnected (remote closed).
    """
    chunks: list[bytes] = []
    while True:
        try:
            chunk = sock.recv(bufsize)
        except OSError as exc:
            raise ConnectionError(f"Receive failed: {exc}") from exc

        if not chunk:
            raise ConnectionError("Remote has closed connection")

        chunks.append(chunk)
        # Check if a complete line has been received
        combined = b"".join(chunks)
        if MSG_TERMINATOR in combined:
            line = combined[: combined.index(MSG_TERMINATOR)]
            return line.decode("utf-8")


# ---------------------------------------------------------------------------
# JSON encoding/decoding
# ---------------------------------------------------------------------------

def send_json(sock: socket.socket, obj: Any) -> None:
    """Serialize Python object to JSON and send as a line.

    Args:
        sock: TCP socket.
        obj: Python object that can be JSON serialized.
    """
    send_line(sock, json.dumps(obj, ensure_ascii=False))


def recv_json(sock: socket.socket, bufsize: int = DEFAULT_RECV_BUF) -> Any:
    """Receive a line of text and deserialize to Python object.

    Args:
        sock: TCP socket.
        bufsize: Maximum number of bytes to receive each time.

    Returns:
        Deserialized Python object (usually dict or list).

    Raises:
        json.JSONDecodeError: Data is not valid JSON.
        ConnectionError: Connection has been disconnected.
    """
    line = recv_line(sock, bufsize)
    try:
        return json.loads(line)
    except json.JSONDecodeError as exc:
        logger.error("JSON parsing failed: %s (original data: %s)", exc, line[:200])
        raise


# ---------------------------------------------------------------------------
# Command/response protocol packing and unpacking
# ---------------------------------------------------------------------------

def pack_command(op: str, data: Any = None, status: int = 1) -> Dict[str, Any]:
    """Construct standard command JSON object.

    Args:
        op: Operation code (e.g., ``"login"``, ``"check_device_id"``).
        data: Payload data (any serializable type).
        status: Status code (default 1).

    Returns:
        Command dictionary.
    """
    return {"op": op, "data": data, "status": status}


def unpack_command(message: Dict[str, Any]) -> Tuple[str, Any, Any]:
    """Unpack standard command JSON object.

    Args:
        message: Command dictionary.

    Returns:
        Tuple ``(op, data, status)``.

    Raises:
        ValueError: Message missing required fields.
    """
    if not isinstance(message, dict):
        raise ValueError(f"Command format error, expected dict, actual {type(message).__name__}")

    op = message.get("op")
    data = message.get("data")
    status = message.get("status")

    if op is None:
        raise ValueError(f"Command missing 'op' field: {message}")

    return op, data, status


def pack_user_data(username: str, password: str, device_key: str) -> Dict[str, str]:
    """Construct user information JSON object (replacing old ``user+pwd+key`` format).

    Args:
        username: Username.
        password: Password.
        device_key: Device key.

    Returns:
        User information dictionary.
    """
    return {"username": username, "password": password, "device_key": device_key}


def unpack_user_data(data: Any) -> Tuple[str, str, str]:
    """Unpack user information JSON object.

    Args:
        data: User information dictionary.

    Returns:
        Tuple ``(username, password, device_key)``.

    Raises:
        ValueError: Data format error.
    """
    if not isinstance(data, dict):
        raise ValueError(f"User data format error, expected dict, actual {type(data).__name__}")

    username = data.get("username", "")
    password = data.get("password", "")
    device_key = data.get("device_key", "")

    if not username:
        raise ValueError(f"User data missing 'username' field: {data}")

    return username, password, device_key
