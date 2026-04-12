"""FSM Task Executor Module.

Implements task execution and rollback mechanism based on Finite State Machine.
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
    """Task execution state enumeration."""

    IDLE = "idle"
    EXECUTING = "executing"
    PAUSED = "paused"
    ROLLBACK = "rollback"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStep:
    """Task step class, represents a single execution unit."""

    def __init__(
        self,
        device: str,
        action: str,
        value: Optional[Any] = None,
        timeout: int = 10,
        retry: int = 3,
    ) -> None:
        """Initialize task step.

        Args:
            device: Device ID
            action: Action name
            value: Parameter value
            timeout: Timeout in seconds
            retry: Retry count
        """
        self.device = device
        self.action = action
        self.value = value
        self.timeout = timeout
        self.retry = retry
        self.executed = False
        self.result: Optional[Dict] = None


class TaskExecutor:
    """FSM Task Executor.

    Uses Finite State Machine to manage task execution flow, supports failure rollback.

    Attributes:
        device_controller: Device controller instance
        state: Current FSM state
        current_task: Current task step list
        executed_steps: Executed step history
        enable_rollback: Whether rollback is enabled
        max_retry: Maximum retry count
        task_timeout: Task timeout in seconds
    """

    def __init__(
        self,
        device_controller: "DeviceController",
        enable_rollback: bool = True,
        max_retry: int = 3,
        task_timeout: int = 30,
    ) -> None:
        """Initialize task executor.

        Args:
            device_controller: Device controller instance
            enable_rollback: Whether to enable rollback, default True
            max_retry: Maximum retry count, default 3
            task_timeout: Task timeout in seconds, default 30
        """
        self.device_controller = device_controller
        self.enable_rollback = enable_rollback
        self.max_retry = max_retry
        self.task_timeout = task_timeout

        # FSM state
        self.state = TaskState.IDLE
        self._lock = threading.Lock()

        # Task management
        self.current_task: List[TaskStep] = []
        self.executed_steps: List[TaskStep] = []

    def execute_task_plan(self, task_plan: Dict) -> Dict:
        """Execute task plan.

        Args:
            task_plan: Task plan dictionary, containing tasks list

        Returns:
            Dict: Execution result {"success": bool, "message": str, "details": list}
        """
        with self._lock:
            # Check current state
            if self.state != TaskState.IDLE:
                logger.warning("Task executor busy: %s", self.state.value)
                return {
                    "success": False,
                    "message": f"Task executor busy: {self.state.value}",
                    "details": [],
                }

            # Parse task steps
            tasks = task_plan.get("tasks", [])
            if not tasks:
                logger.info("No tasks to execute")
                return {
                    "success": True,
                    "message": "No tasks to execute",
                    "details": [],
                }

            # Create task steps
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

            # Update state to executing
            self.state = TaskState.EXECUTING
            self.executed_steps = []

        # Execute task
        try:
            results = self._execute_steps()

            # Check if all steps succeeded
            all_success = all(r.get("success", False) for r in results)

            with self._lock:
                self.state = TaskState.COMPLETED if all_success else TaskState.FAILED

            return {
                "success": all_success,
                "message": "Task execution completed" if all_success else "Task execution failed",
                "details": results,
            }

        except Exception as error:
            logger.error("Task execution exception: %s", error, exc_info=True)
            with self._lock:
                self.state = TaskState.FAILED

            # Execute rollback
            if self.enable_rollback:
                self._rollback()

            return {
                "success": False,
                "message": f"Task execution exception: {str(error)}",
                "details": [],
            }

        finally:
            with self._lock:
                if self.state in [TaskState.COMPLETED, TaskState.FAILED]:
                    self.current_task = []
                    # Delay reset to IDLE state
                    threading.Timer(2.0, self._reset_to_idle).start()

    def _execute_steps(self) -> List[Dict]:
        """Execute task step sequence.

        Returns:
            List[Dict]: Execution result of each step
        """
        results = []

        for i, step in enumerate(self.current_task):
            logger.info(
                "Executing step %d/%d: %s.%s(%s)",
                i + 1,
                len(self.current_task),
                step.device,
                step.action,
                step.value,
            )

            # Execute single step (with retry)
            result = self._execute_step_with_retry(step)
            results.append(result)

            if result["success"]:
                # Success, record to executed list
                step.executed = True
                step.result = result
                self.executed_steps.append(step)
            else:
                # Failed, decide whether to continue based on strategy
                logger.error(
                    "Step %d execution failed: %s", i + 1, result.get("message")
                )

                # If rollback is enabled, execute rollback
                if self.enable_rollback:
                    logger.info("Rollback mechanism enabled")
                    self._rollback()
                    break

        return results

    def _execute_step_with_retry(self, step: TaskStep) -> Dict:
        """Execute single task step (with retry mechanism).

        Args:
            step: Task step object

        Returns:
            Dict: Execution result
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
                        "Step execution failed (attempt %d/%d): %s",
                        attempt + 1,
                        step.retry,
                        last_error,
                    )

                    # If not last attempt, wait and retry
                    if attempt < step.retry - 1:
                        time.sleep(1)

            except Exception as error:
                last_error = str(error)
                logger.error(
                    "Step execution exception (attempt %d/%d): %s",
                    attempt + 1,
                    step.retry,
                    error,
                )

                if attempt < step.retry - 1:
                    time.sleep(1)

        return {
            "success": False,
            "message": f"Execution failed (after {step.retry} retries): {last_error}",
        }

    def _rollback(self) -> None:
        """Execute rollback operation.

        Undo executed steps in reverse order.
        """
        with self._lock:
            self.state = TaskState.ROLLBACK

        logger.info("Starting rollback for %d steps", len(self.executed_steps))

        # Execute undo operations in reverse order
        for step in reversed(self.executed_steps):
            try:
                # Get rollback action
                rollback_action = self._get_rollback_action(step)

                if rollback_action:
                    logger.info(
                        "Rollback step: %s.%s(%s)",
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
                logger.error("Rollback step failed: %s", error)

        with self._lock:
            self.executed_steps = []

    def _get_rollback_action(self, step: TaskStep) -> Optional[Dict]:
        """Get rollback action for step.

        Args:
            step: Task step object

        Returns:
            Optional[Dict]: Rollback action dictionary, None if no rollback action exists
        """
        # Simple rollback mapping
        rollback_map = {
            "turn_on": {"action": "turn_off", "value": None},
            "turn_off": {"action": "turn_on", "value": None},
            "open": {"action": "close", "value": None},
            "close": {"action": "open", "value": None},
        }

        return rollback_map.get(step.action)

    def _reset_to_idle(self) -> None:
        """Reset state to IDLE."""
        with self._lock:
            self.state = TaskState.IDLE

    def get_state(self) -> TaskState:
        """Get current FSM state.

        Returns:
            TaskState: Current state
        """
        with self._lock:
            return self.state

    def pause(self) -> bool:
        """Pause task execution.

        Returns:
            bool: Whether pause was successful
        """
        with self._lock:
            if self.state == TaskState.EXECUTING:
                self.state = TaskState.PAUSED
                logger.info("Task execution paused")
                return True
            return False

    def resume(self) -> bool:
        """Resume task execution.

        Returns:
            bool: Whether resume was successful
        """
        with self._lock:
            if self.state == TaskState.PAUSED:
                self.state = TaskState.EXECUTING
                logger.info("Task execution resumed")
                return True
            return False

    def cancel(self) -> bool:
        """Cancel task execution.

        Returns:
            bool: Whether cancel was successful
        """
        with self._lock:
            if self.state in [TaskState.EXECUTING, TaskState.PAUSED]:
                # Execute rollback
                if self.enable_rollback and self.executed_steps:
                    self._rollback()

                self.state = TaskState.FAILED
                self.current_task = []
                logger.info("Task execution cancelled")
                return True
            return False
