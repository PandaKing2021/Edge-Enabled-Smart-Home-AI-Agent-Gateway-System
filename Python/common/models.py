"""Gateway runtime shared state models.

Use threading.Lock to protect all shared states, replacing global variables in original code.
"""

import threading
from typing import Any, Dict, List


class GatewayState:
    """Gateway runtime shared state, all fields protected by threading.Lock for thread safety."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # Sensor data
        self._data_from_source: Dict[str, Any] = {}
        # Threshold settings
        self._threshold_data: Dict[str, Any] = {}
        # Device control status
        self._status: Dict[str, int] = {}
        # Permitted device list
        self._permitted_device: List[str] = []
        # User login status
        self._login_status: int = 0
        # Door access permission
        self._door_permission: int = 0
        # Whether device node has started collecting data
        self._source_start_flag: int = 0
        # Used to replace listen_if_sensor_connected busy waiting
        self._sensor_ready_event = threading.Event()

    # --- data_from_source ---

    @property
    def data_from_source(self) -> Dict[str, Any]:
        """Get device node data snapshot."""
        with self._lock:
            return dict(self._data_from_source)

    @data_from_source.setter
    def data_from_source(self, value: Dict[str, Any]) -> None:
        """Set device node data."""
        with self._lock:
            self._data_from_source = dict(value)

    def update_data(self, updates: Dict[str, Any]) -> None:
        """Update specified fields in device node data."""
        with self._lock:
            self._data_from_source.update(updates)

    def get_data_snapshot(self) -> Dict[str, Any]:
        """Get device node data snapshot (thread-safe copy)."""
        with self._lock:
            return dict(self._data_from_source)

    # --- threshold_data ---

    @property
    def threshold_data(self) -> Dict[str, Any]:
        """Get threshold data snapshot."""
        with self._lock:
            return dict(self._threshold_data)

    def set_threshold(self, key: str, value: Any) -> None:
        """Set a single threshold."""
        with self._lock:
            self._threshold_data[key] = value

    def get_threshold(self, key: str, default: Any = None) -> Any:
        """Get a single threshold."""
        with self._lock:
            return self._threshold_data.get(key, default)

    # --- status ---

    @property
    def status(self) -> Dict[str, int]:
        """Get device control status snapshot."""
        with self._lock:
            return dict(self._status)

    def update_status(self, updates: Dict[str, int]) -> None:
        """Update device control status."""
        with self._lock:
            self._status.update(updates)

    # --- permitted_device ---

    @property
    def permitted_device(self) -> List[str]:
        """Get permitted device list snapshot."""
        with self._lock:
            return list(self._permitted_device)

    def set_permitted_device(self, devices: List[str]) -> None:
        """Set permitted device list."""
        with self._lock:
            self._permitted_device = list(devices)

    def is_device_permitted(self, device_id: str) -> bool:
        """Check if device is in permitted list."""
        with self._lock:
            return device_id in self._permitted_device

    # --- login_status ---

    @property
    def login_status(self) -> int:
        """Get login status."""
        with self._lock:
            return self._login_status

    @login_status.setter
    def login_status(self, value: int) -> None:
        """Set login status."""
        with self._lock:
            self._login_status = value

    # --- door_permission ---

    @property
    def door_permission(self) -> int:
        """Get door access permission status."""
        with self._lock:
            return self._door_permission

    @door_permission.setter
    def door_permission(self, value: int) -> None:
        """Set door access permission status."""
        with self._lock:
            self._door_permission = value

    # --- source_start_flag ---

    @property
    def source_start_flag(self) -> int:
        """Get device node data collection status."""
        with self._lock:
            return self._source_start_flag

    @source_start_flag.setter
    def source_start_flag(self, value: int) -> None:
        """Set device node data collection status."""
        with self._lock:
            self._source_start_flag = value
            if value == 1:
                self._sensor_ready_event.set()

    def wait_for_sensor(self, timeout: float = None) -> bool:
        """Blocking wait for device node to start collecting data.

        Args:
            timeout: Timeout in seconds, None means wait indefinitely.

        Returns:
            True indicates device connected, False indicates timeout.
        """
        return self._sensor_ready_event.wait(timeout=timeout)
