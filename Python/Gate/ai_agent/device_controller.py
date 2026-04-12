"""设备控制接口模块。

统一封装设备控制API,与GatewayState集成。
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from common.models import GatewayState

logger = logging.getLogger(__name__)


class DeviceController:
    """设备控制器,统一封装设备控制API。

    将抽象的设备操作映射到GatewayState的阈值设置。

    Attributes:
        state: GatewayState实例
    """

    def __init__(self, state: "GatewayState") -> None:
        """初始化设备控制器。

        Args:
            state: 网关共享状态对象
        """
        self.state = state

    def execute_action(
        self, device_id: str, action: str, value: Optional[Any] = None
    ) -> Dict:
        """执行设备动作。

        Args:
            device_id: 设备ID(如"Light_TH", "Curtain_status")
            action: 动作名称(如"set_temperature", "open")
            value: 参数值,可选

        Returns:
            Dict: 执行结果 {"success": bool, "message": str}
        """
        try:
            # 根据设备类型和动作执行相应操作
            if device_id == "Light_TH":
                return self._control_air_conditioner(action, value)
            elif device_id == "Curtain_status":
                return self._control_curtain(action, value)
            elif device_id == "Light_CU":
                return self._control_light(action, value)
            elif device_id == "Door_Security_Status":
                return self._control_door(action, value)
            else:
                logger.warning("未知设备ID: %s", device_id)
                return {
                    "success": False,
                    "message": f"未知设备: {device_id}",
                }

        except Exception as error:
            logger.error("执行设备动作失败: %s", error, exc_info=True)
            return {
                "success": False,
                "message": f"执行失败: {str(error)}",
            }

    def _control_air_conditioner(
        self, action: str, value: Optional[Any]
    ) -> Dict:
        """控制智能空调。

        Args:
            action: 动作名称
            value: 参数值

        Returns:
            Dict: 执行结果
        """
        from common.constants import FIELD_TEMPERATURE, FIELD_HUMIDITY

        if action == "turn_on":
            # 开启空调
            self.state.set_threshold(FIELD_TEMPERATURE, -1)
            self.state.set_threshold(FIELD_HUMIDITY, -1)
            logger.info("智能空调已开启")
            return {"success": True, "message": "智能空调已开启"}

        elif action == "turn_off":
            # 关闭空调
            self.state.set_threshold(FIELD_TEMPERATURE, 101)
            self.state.set_threshold(FIELD_HUMIDITY, 101)
            logger.info("智能空调已关闭")
            return {"success": True, "message": "智能空调已关闭"}

        elif action == "set_temperature":
            # 设置温度
            if value is None:
                return {"success": False, "message": "缺少温度参数"}
            temperature = int(value)
            if not (16 <= temperature <= 30):
                return {
                    "success": False,
                    "message": f"温度超出范围(16-30): {temperature}",
                }
            self.state.set_threshold(FIELD_TEMPERATURE, temperature)
            logger.info("设置温度阈值: %d°C", temperature)
            return {
                "success": True,
                "message": f"温度已设置为 {temperature}°C",
            }

        elif action == "set_humidity":
            # 设置湿度
            if value is None:
                return {"success": False, "message": "缺少湿度参数"}
            humidity = int(value)
            if not (30 <= humidity <= 90):
                return {
                    "success": False,
                    "message": f"湿度超出范围(30-90): {humidity}",
                }
            self.state.set_threshold(FIELD_HUMIDITY, humidity)
            logger.info("设置湿度阈值: %d%%", humidity)
            return {
                "success": True,
                "message": f"湿度已设置为 {humidity}%",
            }

        else:
            return {
                "success": False,
                "message": f"未知空调动作: {action}",
            }

    def _control_curtain(self, action: str, value: Optional[Any]) -> Dict:
        """控制智能窗帘。

        Args:
            action: 动作名称
            value: 参数值

        Returns:
            Dict: 执行结果
        """
        from common.constants import FIELD_BRIGHTNESS

        if action == "open":
            # 打开窗帘
            self.state.set_threshold(FIELD_BRIGHTNESS, -2)
            logger.info("窗帘已打开")
            return {"success": True, "message": "窗帘已打开"}

        elif action == "close":
            # 关闭窗帘
            self.state.set_threshold(FIELD_BRIGHTNESS, 65535)
            logger.info("窗帘已关闭")
            return {"success": True, "message": "窗帘已关闭"}

        elif action == "set_brightness":
            # 设置光照度阈值
            if value is None:
                return {"success": False, "message": "缺少光照度参数"}
            brightness = int(value)
            if not (0 <= brightness <= 65535):
                return {
                    "success": False,
                    "message": f"光照度超出范围(0-65535): {brightness}",
                }
            self.state.set_threshold(FIELD_BRIGHTNESS, brightness)
            logger.info("设置光照度阈值: %d lux", brightness)
            return {
                "success": True,
                "message": f"光照度已设置为 {brightness} lux",
            }

        else:
            return {
                "success": False,
                "message": f"未知窗帘动作: {action}",
            }

    def _control_light(self, action: str, value: Optional[Any]) -> Dict:
        """控制智能灯光。

        Args:
            action: 动作名称
            value: 参数值

        Returns:
            Dict: 执行结果
        """
        from common.constants import FIELD_BRIGHTNESS

        if action == "set_brightness":
            # 设置亮度
            if value is None:
                return {"success": False, "message": "缺少亮度参数"}
            brightness = int(value)
            if not (0 <= brightness <= 65535):
                return {
                    "success": False,
                    "message": f"亮度超出范围(0-65535): {brightness}",
                }
            self.state.set_threshold(FIELD_BRIGHTNESS, brightness)
            logger.info("设置灯光亮度: %d", brightness)
            return {
                "success": True,
                "message": f"灯光亮度已设置为 {brightness}",
            }

        else:
            return {
                "success": False,
                "message": f"未知灯光动作: {action}",
            }

    def _control_door(self, action: str, value: Optional[Any]) -> Dict:
        """控制智能门禁。

        Args:
            action: 动作名称
            value: 参数值

        Returns:
            Dict: 执行结果
        """
        # 门禁系统由设备自动验证,网关暂不支持主动控制
        return {
            "success": False,
            "message": "门禁系统仅支持刷卡验证,不支持主动控制",
        }

    def get_device_state(self, device_id: str) -> Dict:
        """获取设备状态。

        Args:
            device_id: 设备ID

        Returns:
            Dict: 设备状态字典
        """
        data = self.state.get_data_snapshot()
        threshold = self.state.threshold_data

        if device_id == "Light_TH":
            return {
                "device": "智能空调",
                "temperature": data.get("Temperature", 0),
                "humidity": data.get("Humidity", 0),
                "temperature_threshold": threshold.get("Temperature", 0),
                "humidity_threshold": threshold.get("Humidity", 0),
            }
        elif device_id == "Curtain_status":
            return {
                "device": "智能窗帘",
                "status": data.get("Curtain_status", 0),
                "brightness": data.get("Brightness", 0),
                "brightness_threshold": threshold.get("Brightness", 0),
            }
        elif device_id == "Light_CU":
            return {
                "device": "智能灯光",
                "brightness": data.get("Brightness", 0),
                "brightness_threshold": threshold.get("Brightness", 0),
            }
        else:
            return {"device": device_id, "status": "未知设备"}

    def get_all_device_states(self) -> Dict:
        """获取所有设备状态。

        Returns:
            Dict: 所有设备状态字典
        """
        return {
            "Light_TH": self.get_device_state("Light_TH"),
            "Curtain_status": self.get_device_state("Curtain_status"),
            "Light_CU": self.get_device_state("Light_CU"),
        }
