"""Device control interface module.

Unified encapsulation of device control API, integrated with GatewayState.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from common.models import GatewayState

logger = logging.getLogger(__name__)


class DeviceController:
    """Device controller, unified encapsulation of device control API.

    Maps abstract device operations to GatewayState threshold settings.

    Attributes:
        state: GatewayState instance
    """

    def __init__(self, state: "GatewayState") -> None:
        """Initialize device controller.

        Args:
            state: Gateway shared state object
        """
        self.state = state

    def execute_action(
        self, device_id: str, action: str, value: Optional[Any] = None
    ) -> Dict:
        """Execute device action.

        Args:
            device_id: Device ID (e.g., "Light_TH", "Curtain_status")
            action: Action name (e.g., "set_temperature", "open")
            value: Parameter value, optional

        Returns:
            Dict: Execution result {"success": bool, "message": str}
        """
        try:
            # Execute corresponding operation based on device type and action
            if device_id == "Light_TH":
                return self._control_air_conditioner(action, value)
            elif device_id == "Curtain_status":
                return self._control_curtain(action, value)
            elif device_id == "Light_CU":
                return self._control_light(action, value)
            elif device_id == "Door_Security_Status":
                return self._control_door(action, value)
            else:
                logger.warning("Unknown device ID: %s", device_id)
                return {
                    "success": False,
                    "message": f"Unknown device: {device_id}",
                }

        except Exception as error:
            logger.error("Failed to execute device action: %s", error, exc_info=True)
            return {
                "success": False,
                "message": f"Execution failed: {str(error)}",
            }

    def _control_air_conditioner(
        self, action: str, value: Optional[Any]
    ) -> Dict:
        """Control smart air conditioner.

        Args:
            action: Action name
            value: Parameter value

        Returns:
            Dict: Execution result
        """
        from common.constants import FIELD_TEMPERATURE, FIELD_HUMIDITY

        if action == "turn_on":
            # Turn on AC
            self.state.set_threshold(FIELD_TEMPERATURE, -1)
            self.state.set_threshold(FIELD_HUMIDITY, -1)
            logger.info("Smart AC turned on")
            return {"success": True, "message": "Smart AC turned on"}

        elif action == "turn_off":
            # Turn off AC
            self.state.set_threshold(FIELD_TEMPERATURE, 101)
            self.state.set_threshold(FIELD_HUMIDITY, 101)
            logger.info("Smart AC turned off")
            return {"success": True, "message": "Smart AC turned off"}

        elif action == "set_temperature":
            # Set temperature
            if value is None:
                return {"success": False, "message": "Missing temperature parameter"}
            temperature = int(value)
            if not (16 <= temperature <= 30):
                return {
                    "success": False,
                    "message": f"Temperature out of range (16-30): {temperature}",
                }
            self.state.set_threshold(FIELD_TEMPERATURE, temperature)
            logger.info("Set temperature threshold: %d°C", temperature)
            return {
                "success": True,
                "message": f"Temperature set to {temperature}°C",
            }

        elif action == "set_humidity":
            # Set humidity
            if value is None:
                return {"success": False, "message": "Missing humidity parameter"}
            humidity = int(value)
            if not (30 <= humidity <= 90):
                return {
                    "success": False,
                    "message": f"Humidity out of range (30-90): {humidity}",
                }
            self.state.set_threshold(FIELD_HUMIDITY, humidity)
            logger.info("Set humidity threshold: %d%%", humidity)
            return {
                "success": True,
                "message": f"Humidity set to {humidity}%",
            }

        else:
            return {
                "success": False,
                "message": f"Unknown AC action: {action}",
            }

    def _control_curtain(self, action: str, value: Optional[Any]) -> Dict:
        """Control smart curtain.

        Args:
            action: Action name
            value: Parameter value

        Returns:
            Dict: Execution result
        """
        from common.constants import FIELD_BRIGHTNESS

        if action == "open":
            # Open curtain
            self.state.set_threshold(FIELD_BRIGHTNESS, -2)
            logger.info("Curtain opened")
            return {"success": True, "message": "Curtain opened"}

        elif action == "close":
            # Close curtain
            self.state.set_threshold(FIELD_BRIGHTNESS, 65535)
            logger.info("Curtain closed")
            return {"success": True, "message": "Curtain closed"}

        elif action == "set_brightness":
            # Set brightness threshold
            if value is None:
                return {"success": False, "message": "Missing brightness parameter"}
            brightness = int(value)
            if not (0 <= brightness <= 65535):
                return {
                    "success": False,
                    "message": f"Brightness out of range (0-65535): {brightness}",
                }
            self.state.set_threshold(FIELD_BRIGHTNESS, brightness)
            logger.info("Set brightness threshold: %d lux", brightness)
            return {
                "success": True,
                "message": f"Brightness set to {brightness} lux",
            }

        else:
            return {
                "success": False,
                "message": f"Unknown curtain action: {action}",
            }

    def _control_light(self, action: str, value: Optional[Any]) -> Dict:
        """Control smart light.

        Args:
            action: Action name
            value: Parameter value

        Returns:
            Dict: Execution result
        """
        from common.constants import FIELD_BRIGHTNESS

        if action == "set_brightness":
            # Set brightness
            if value is None:
                return {"success": False, "message": "Missing brightness parameter"}
            brightness = int(value)
            if not (0 <= brightness <= 65535):
                return {
                    "success": False,
                    "message": f"Brightness out of range (0-65535): {brightness}",
                }
            self.state.set_threshold(FIELD_BRIGHTNESS, brightness)
            logger.info("Set light brightness: %d", brightness)
            return {
                "success": True,
                "message": f"Light brightness set to {brightness}",
            }

        else:
            return {
                "success": False,
                "message": f"Unknown light action: {action}",
            }

    def _control_door(self, action: str, value: Optional[Any]) -> Dict:
        """Control smart door access.

        Args:
            action: Action name
            value: Parameter value

        Returns:
            Dict: Execution result
        """
        # Door access system is automatically verified by device, gateway doesn't support active control
        return {
            "success": False,
            "message": "Door access system only supports card verification, doesn't support active control",
        }

    def get_device_state(self, device_id: str) -> Dict:
        """Get device status.

        Args:
            device_id: Device ID

        Returns:
            Dict: Device status dictionary
        """
        data = self.state.get_data_snapshot()
        threshold = self.state.threshold_data

        if device_id == "Light_TH":
            return {
                "device": "Smart AC",
                "temperature": data.get("Temperature", 0),
                "humidity": data.get("Humidity", 0),
                "temperature_threshold": threshold.get("Temperature", 0),
                "humidity_threshold": threshold.get("Humidity", 0),
            }
        elif device_id == "Curtain_status":
            return {
                "device": "Smart Curtain",
                "status": data.get("Curtain_status", 0),
                "brightness": data.get("Brightness", 0),
                "brightness_threshold": threshold.get("Brightness", 0),
            }
        elif device_id == "Light_CU":
            return {
                "device": "Smart Light",
                "brightness": data.get("Brightness", 0),
                "brightness_threshold": threshold.get("Brightness", 0),
            }
        else:
            return {"device": device_id, "status": "Unknown device"}

    def get_all_device_states(self) -> Dict:
        """Get all device statuses.

        Returns:
            Dict: All device status dictionary
        """
        return {
            "Light_TH": self.get_device_state("Light_TH"),
            "Curtain_status": self.get_device_state("Curtain_status"),
            "Light_CU": self.get_device_state("Light_CU"),
        }
