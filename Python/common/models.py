"""网关运行时共享状态模型。

使用 threading.Lock 保护所有共享状态，替代原始代码中的全局变量。
"""

import threading
from typing import Any, Dict, List


class GatewayState:
    """网关运行时共享状态，所有字段通过 threading.Lock 保护线程安全。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # 传感器数据
        self._data_from_source: Dict[str, Any] = {}
        # 阈值设置
        self._threshold_data: Dict[str, Any] = {}
        # 设备控制状态
        self._status: Dict[str, int] = {}
        # 允许设备列表
        self._permitted_device: List[str] = []
        # 用户登录状态
        self._login_status: int = 0
        # 门禁权限
        self._door_permission: int = 0
        # 设备节点是否开始收集数据
        self._source_start_flag: int = 0
        # 用于替代 listen_if_sensor_connected 的忙等待
        self._sensor_ready_event = threading.Event()

    # --- data_from_source ---

    @property
    def data_from_source(self) -> Dict[str, Any]:
        """获取设备节点数据快照。"""
        with self._lock:
            return dict(self._data_from_source)

    @data_from_source.setter
    def data_from_source(self, value: Dict[str, Any]) -> None:
        """设置设备节点数据。"""
        with self._lock:
            self._data_from_source = dict(value)

    def update_data(self, updates: Dict[str, Any]) -> None:
        """更新设备节点数据中的指定字段。"""
        with self._lock:
            self._data_from_source.update(updates)

    def get_data_snapshot(self) -> Dict[str, Any]:
        """获取设备节点数据快照（线程安全副本）。"""
        with self._lock:
            return dict(self._data_from_source)

    # --- threshold_data ---

    @property
    def threshold_data(self) -> Dict[str, Any]:
        """获取阈值数据快照。"""
        with self._lock:
            return dict(self._threshold_data)

    def set_threshold(self, key: str, value: Any) -> None:
        """设置单个阈值。"""
        with self._lock:
            self._threshold_data[key] = value

    def get_threshold(self, key: str, default: Any = None) -> Any:
        """获取单个阈值。"""
        with self._lock:
            return self._threshold_data.get(key, default)

    # --- status ---

    @property
    def status(self) -> Dict[str, int]:
        """获取设备控制状态快照。"""
        with self._lock:
            return dict(self._status)

    def update_status(self, updates: Dict[str, int]) -> None:
        """更新设备控制状态。"""
        with self._lock:
            self._status.update(updates)

    # --- permitted_device ---

    @property
    def permitted_device(self) -> List[str]:
        """获取允许设备列表快照。"""
        with self._lock:
            return list(self._permitted_device)

    def set_permitted_device(self, devices: List[str]) -> None:
        """设置允许设备列表。"""
        with self._lock:
            self._permitted_device = list(devices)

    def is_device_permitted(self, device_id: str) -> bool:
        """检查设备是否在允许列表中。"""
        with self._lock:
            return device_id in self._permitted_device

    # --- login_status ---

    @property
    def login_status(self) -> int:
        """获取登录状态。"""
        with self._lock:
            return self._login_status

    @login_status.setter
    def login_status(self, value: int) -> None:
        """设置登录状态。"""
        with self._lock:
            self._login_status = value

    # --- door_permission ---

    @property
    def door_permission(self) -> int:
        """获取门禁权限状态。"""
        with self._lock:
            return self._door_permission

    @door_permission.setter
    def door_permission(self, value: int) -> None:
        """设置门禁权限状态。"""
        with self._lock:
            self._door_permission = value

    # --- source_start_flag ---

    @property
    def source_start_flag(self) -> int:
        """获取设备节点数据采集状态。"""
        with self._lock:
            return self._source_start_flag

    @source_start_flag.setter
    def source_start_flag(self, value: int) -> None:
        """设置设备节点数据采集状态。"""
        with self._lock:
            self._source_start_flag = value
            if value == 1:
                self._sensor_ready_event.set()

    def wait_for_sensor(self, timeout: float = None) -> bool:
        """阻塞式等待设备节点开始收集数据。

        Args:
            timeout: 超时时间（秒），None 表示无限等待。

        Returns:
            True 表示设备已连接，False 表示超时。
        """
        return self._sensor_ready_event.wait(timeout=timeout)
