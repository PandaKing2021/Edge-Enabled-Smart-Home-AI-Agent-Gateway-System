"""AI Agent模块 - 对话式任务自动编排系统。

基于智谱AI GLM-4.7-Flash实现智能家居任务自动编排功能。
"""

from .dialog_manager import DialogManager
from .intent_planner import IntentPlanner
from .capability_retriever import CapabilityRetriever
from .task_executor import TaskExecutor
from .device_controller import DeviceController
from .preference_manager import PreferenceManager

__all__ = [
    "DialogManager",
    "IntentPlanner",
    "CapabilityRetriever",
    "TaskExecutor",
    "DeviceController",
    "PreferenceManager",
]

__version__ = "1.0.0"
