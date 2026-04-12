"""FSM任务执行器模块。

基于有限状态机实现任务执行和回滚机制。
"""

import logging
import threading
import time
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

if TYPE_CHECKING:
    from .device_controller import DeviceController

logger = logging.getLogger(__name__)


class TaskState(Enum):
    """任务执行状态枚举。"""

    IDLE = "idle"
    EXECUTING = "executing"
    PAUSED = "paused"
    ROLLBACK = "rollback"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStep:
    """任务步骤类,表示单个执行单元。"""

    def __init__(
        self,
        device: str,
        action: str,
        value: Optional[Any] = None,
        timeout: int = 10,
        retry: int = 3,
    ) -> None:
        """初始化任务步骤。

        Args:
            device: 设备ID
            action: 动作名称
            value: 参数值
            timeout: 超时时间(秒)
            retry: 重试次数
        """
        self.device = device
        self.action = action
        self.value = value
        self.timeout = timeout
        self.retry = retry
        self.executed = False
        self.result: Optional[Dict] = None


class TaskExecutor:
    """FSM任务执行器。

    使用有限状态机管理任务执行流程,支持失败回滚。

    Attributes:
        device_controller: 设备控制器实例
        state: 当前FSM状态
        current_task: 当前任务步骤列表
        executed_steps: 已执行的步骤历史
        enable_rollback: 是否启用回滚
        max_retry: 最大重试次数
        task_timeout: 任务超时时间(秒)
    """

    def __init__(
        self,
        device_controller: "DeviceController",
        enable_rollback: bool = True,
        max_retry: int = 3,
        task_timeout: int = 30,
    ) -> None:
        """初始化任务执行器。

        Args:
            device_controller: 设备控制器实例
            enable_rollback: 是否启用回滚,默认True
            max_retry: 最大重试次数,默认3
            task_timeout: 任务超时时间(秒),默认30
        """
        self.device_controller = device_controller
        self.enable_rollback = enable_rollback
        self.max_retry = max_retry
        self.task_timeout = task_timeout

        # FSM状态
        self.state = TaskState.IDLE
        self._lock = threading.Lock()

        # 任务管理
        self.current_task: List[TaskStep] = []
        self.executed_steps: List[TaskStep] = []

    def execute_task_plan(self, task_plan: Dict) -> Dict:
        """执行任务计划。

        Args:
            task_plan: 任务计划字典,包含tasks列表

        Returns:
            Dict: 执行结果 {"success": bool, "message": str, "details": list}
        """
        with self._lock:
            # 检查当前状态
            if self.state != TaskState.IDLE:
                logger.warning("任务执行器忙: %s", self.state.value)
                return {
                    "success": False,
                    "message": f"任务执行器忙: {self.state.value}",
                    "details": [],
                }

            # 解析任务步骤
            tasks = task_plan.get("tasks", [])
            if not tasks:
                logger.info("无任务需要执行")
                return {
                    "success": True,
                    "message": "无任务需要执行",
                    "details": [],
                }

            # 创建任务步骤
            self.current_task = []
            for task in tasks:
                step = TaskStep(
                    device=task.get("device"),
                    action=task.get("action"),
                    value=task.get("value"),
                    timeout=self.task_timeout,
                    retry=self.max_retry,
                )
                self.current_task.append(step)

            # 更新状态为执行中
            self.state = TaskState.EXECUTING
            self.executed_steps = []

        # 执行任务
        try:
            results = self._execute_steps()

            # 检查是否所有步骤都成功
            all_success = all(r.get("success", False) for r in results)

            with self._lock:
                self.state = TaskState.COMPLETED if all_success else TaskState.FAILED

            return {
                "success": all_success,
                "message": "任务执行完成" if all_success else "任务执行失败",
                "details": results,
            }

        except Exception as error:
            logger.error("任务执行异常: %s", error, exc_info=True)
            with self._lock:
                self.state = TaskState.FAILED

            # 执行回滚
            if self.enable_rollback:
                self._rollback()

            return {
                "success": False,
                "message": f"任务执行异常: {str(error)}",
                "details": [],
            }

        finally:
            with self._lock:
                if self.state in [TaskState.COMPLETED, TaskState.FAILED]:
                    self.current_task = []
                    # 延迟重置为IDLE状态
                    threading.Timer(2.0, self._reset_to_idle).start()

    def _execute_steps(self) -> List[Dict]:
        """执行任务步骤序列。

        Returns:
            List[Dict]: 每个步骤的执行结果
        """
        results = []

        for i, step in enumerate(self.current_task):
            logger.info(
                "执行步骤 %d/%d: %s.%s(%s)",
                i + 1,
                len(self.current_task),
                step.device,
                step.action,
                step.value,
            )

            # 执行单个步骤(带重试)
            result = self._execute_step_with_retry(step)
            results.append(result)

            if result["success"]:
                # 成功,记录到已执行列表
                step.executed = True
                step.result = result
                self.executed_steps.append(step)
            else:
                # 失败,根据策略决定是否继续
                logger.error(
                    "步骤 %d 执行失败: %s", i + 1, result.get("message")
                )

                # 如果启用回滚,执行回滚
                if self.enable_rollback:
                    logger.info("启用回滚机制")
                    self._rollback()
                    break

        return results

    def _execute_step_with_retry(self, step: TaskStep) -> Dict:
        """执行单个任务步骤(带重试机制)。

        Args:
            step: 任务步骤对象

        Returns:
            Dict: 执行结果
        """
        last_error = None

        for attempt in range(step.retry):
            try:
                result = self.device_controller.execute_action(
                    device_id=step.device,
                    action=step.action,
                    value=step.value,
                )

                if result["success"]:
                    return result
                else:
                    last_error = result.get("message")
                    logger.warning(
                        "步骤执行失败(尝试 %d/%d): %s",
                        attempt + 1,
                        step.retry,
                        last_error,
                    )

                    # 如果不是最后一次尝试,等待后重试
                    if attempt < step.retry - 1:
                        time.sleep(1)

            except Exception as error:
                last_error = str(error)
                logger.error(
                    "步骤执行异常(尝试 %d/%d): %s",
                    attempt + 1,
                    step.retry,
                    error,
                )

                if attempt < step.retry - 1:
                    time.sleep(1)

        return {
            "success": False,
            "message": f"执行失败(重试{step.retry}次后): {last_error}",
        }

    def _rollback(self) -> None:
        """执行回滚操作。

        按相反顺序撤销已执行的步骤。
        """
        with self._lock:
            self.state = TaskState.ROLLBACK

        logger.info("开始回滚 %d 个步骤", len(self.executed_steps))

        # 按相反顺序执行撤销操作
        for step in reversed(self.executed_steps):
            try:
                # 获取撤销动作
                rollback_action = self._get_rollback_action(step)

                if rollback_action:
                    logger.info(
                        "回滚步骤: %s.%s(%s)",
                        step.device,
                        rollback_action["action"],
                        rollback_action.get("value"),
                    )

                    self.device_controller.execute_action(
                        device_id=step.device,
                        action=rollback_action["action"],
                        value=rollback_action.get("value"),
                    )

            except Exception as error:
                logger.error("回滚步骤失败: %s", error)

        with self._lock:
            self.executed_steps = []

    def _get_rollback_action(self, step: TaskStep) -> Optional[Dict]:
        """获取步骤的撤销动作。

        Args:
            step: 任务步骤对象

        Returns:
            Optional[Dict]: 撤销动作字典,无撤销动作返回None
        """
        # 简单的撤销映射
        rollback_map = {
            "turn_on": {"action": "turn_off", "value": None},
            "turn_off": {"action": "turn_on", "value": None},
            "open": {"action": "close", "value": None},
            "close": {"action": "open", "value": None},
        }

        return rollback_map.get(step.action)

    def _reset_to_idle(self) -> None:
        """重置状态为IDLE。"""
        with self._lock:
            self.state = TaskState.IDLE

    def get_state(self) -> TaskState:
        """获取当前FSM状态。

        Returns:
            TaskState: 当前状态
        """
        with self._lock:
            return self.state

    def pause(self) -> bool:
        """暂停任务执行。

        Returns:
            bool: 是否暂停成功
        """
        with self._lock:
            if self.state == TaskState.EXECUTING:
                self.state = TaskState.PAUSED
                logger.info("任务执行已暂停")
                return True
            return False

    def resume(self) -> bool:
        """恢复任务执行。

        Returns:
            bool: 是否恢复成功
        """
        with self._lock:
            if self.state == TaskState.PAUSED:
                self.state = TaskState.EXECUTING
                logger.info("任务执行已恢复")
                return True
            return False

    def cancel(self) -> bool:
        """取消任务执行。

        Returns:
            bool: 是否取消成功
        """
        with self._lock:
            if self.state in [TaskState.EXECUTING, TaskState.PAUSED]:
                # 执行回滚
                if self.enable_rollback and self.executed_steps:
                    self._rollback()

                self.state = TaskState.FAILED
                self.current_task = []
                logger.info("任务执行已取消")
                return True
            return False
