"""偏好记忆管理器模块。

存储和管理用户对自动生成任务的修正偏好。
"""

import json
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PreferenceManager:
    """偏好记忆管理器。

    记录用户对任务执行结果的修正,实现个性化优化。

    Attributes:
        db_connection: 数据库连接对象
        table_name: 偏好表名称
    """

    def __init__(self, db_connection=None, table_name: str = "user_preferences") -> None:
        """初始化偏好管理器。

        Args:
            db_connection: 数据库连接对象(MySQL connector)
            table_name: 偏好表名称
        """
        self.db_connection = db_connection
        self.table_name = table_name
        self._lock = threading.Lock()

        # 内存缓存
        self._cache: Dict[str, List[Dict]] = {}

    def record_preference(
        self,
        user_id: str,
        scenario: str,
        device: str,
        action: str,
        parameter: str,
        preferred_value: str,
    ) -> bool:
        """记录用户偏好修正。

        Args:
            user_id: 用户ID
            scenario: 场景标识(如"sleep", "movie")
            device: 设备ID
            action: 动作名称
            parameter: 参数名称
            preferred_value: 用户偏好的值

        Returns:
            bool: 是否记录成功
        """
        try:
            timestamp = datetime.now()

            # 存储到内存缓存
            with self._lock:
                if user_id not in self._cache:
                    self._cache[user_id] = []

                preference = {
                    "scenario": scenario,
                    "device": device,
                    "action": action,
                    "parameter": parameter,
                    "preferred_value": preferred_value,
                    "created_at": timestamp,
                    "updated_at": timestamp,
                }

                # 检查是否已存在相同偏好
                existing_idx = None
                for i, p in enumerate(self._cache[user_id]):
                    if (
                        p["scenario"] == scenario
                        and p["device"] == device
                        and p["action"] == action
                        and p["parameter"] == parameter
                    ):
                        existing_idx = i
                        break

                if existing_idx is not None:
                    # 更新已有偏好
                    self._cache[user_id][existing_idx].update(preference)
                else:
                    # 添加新偏好
                    self._cache[user_id].append(preference)

            # 存储到数据库
            if self.db_connection:
                self._save_to_db(
                    user_id=user_id,
                    scenario=scenario,
                    device=device,
                    action=action,
                    parameter=parameter,
                    preferred_value=preferred_value,
                )

            logger.info(
                "记录用户偏好: %s -> %s.%s.%s=%s",
                user_id,
                device,
                action,
                parameter,
                preferred_value,
            )
            return True

        except Exception as error:
            logger.error("记录用户偏好失败: %s", error, exc_info=True)
            return False

    def get_user_preferences(
        self, user_id: str, scenario: Optional[str] = None
    ) -> Dict:
        """获取用户偏好。

        Args:
            user_id: 用户ID
            scenario: 场景标识,可选(不指定则返回所有偏好)

        Returns:
            Dict: 用户偏好字典 {scenario: [{device, action, parameter, preferred_value}]}
        """
        try:
            # 从缓存中获取
            with self._lock:
                user_prefs = self._cache.get(user_id, [])

            # 按场景分组
            preferences_by_scenario: Dict[str, List[Dict]] = {}

            for pref in user_prefs:
                pref_scenario = pref["scenario"]
                if scenario and pref_scenario != scenario:
                    continue

                if pref_scenario not in preferences_by_scenario:
                    preferences_by_scenario[pref_scenario] = []

                preferences_by_scenario[pref_scenario].append(
                    {
                        "device": pref["device"],
                        "action": pref["action"],
                        "parameter": pref["parameter"],
                        "preferred_value": pref["preferred_value"],
                    }
                )

            logger.debug(
                "获取用户偏好: %s (场景: %s) -> %d 条",
                user_id,
                scenario or "全部",
                sum(len(v) for v in preferences_by_scenario.values()),
            )

            return preferences_by_scenario

        except Exception as error:
            logger.error("获取用户偏好失败: %s", error, exc_info=True)
            return {}

    def apply_preferences(
        self, user_id: str, scenario: str, task_plan: Dict
    ) -> Dict:
        """将用户偏好应用到任务计划。

        Args:
            user_id: 用户ID
            scenario: 场景标识
            task_plan: 任务计划字典

        Returns:
            Dict: 应用偏好后的任务计划
        """
        try:
            # 获取该场景的用户偏好
            preferences = self.get_user_preferences(user_id, scenario)

            if scenario not in preferences:
                return task_plan

            user_prefs = preferences[scenario]

            # 应用偏好到任务
            tasks = task_plan.get("tasks", [])
            modified_tasks = []

            for task in tasks:
                modified_task = task.copy()

                # 检查是否有匹配的偏好
                for pref in user_prefs:
                    if (
                        pref["device"] == task.get("device")
                        and pref["action"] == task.get("action")
                    ):
                        # 应用偏好值
                        modified_task["value"] = pref["preferred_value"]
                        logger.info(
                            "应用用户偏好: %s.%s=%s",
                            pref["device"],
                            pref["action"],
                            pref["preferred_value"],
                        )

                modified_tasks.append(modified_task)

            task_plan["tasks"] = modified_tasks
            return task_plan

        except Exception as error:
            logger.error("应用用户偏好失败: %s", error, exc_info=True)
            return task_plan

    def _save_to_db(
        self,
        user_id: str,
        scenario: str,
        device: str,
        action: str,
        parameter: str,
        preferred_value: str,
    ) -> bool:
        """保存偏好到数据库。

        Args:
            user_id: 用户ID
            scenario: 场景标识
            device: 设备ID
            action: 动作名称
            parameter: 参数名称
            preferred_value: 偏好值

        Returns:
            bool: 是否保存成功
        """
        try:
            if not self.db_connection:
                return False

            cursor = self.db_connection.cursor()

            # 使用INSERT ... ON DUPLICATE KEY UPDATE
            query = f"""
                INSERT INTO {self.table_name}
                (user_id, scenario, device, action, parameter, preferred_value, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                    preferred_value = VALUES(preferred_value),
                    updated_at = NOW()
            """

            cursor.execute(
                query,
                (user_id, scenario, device, action, parameter, preferred_value),
            )
            self.db_connection.commit()
            cursor.close()

            logger.debug("偏好已保存到数据库")
            return True

        except Exception as error:
            logger.error("保存偏好到数据库失败: %s", error, exc_info=True)
            return False

    def load_from_db(self, user_id: str) -> int:
        """从数据库加载用户偏好到缓存。

        Args:
            user_id: 用户ID

        Returns:
            int: 加载的偏好数量
        """
        try:
            if not self.db_connection:
                return 0

            cursor = self.db_connection.cursor(dictionary=True)
            query = f"""
                SELECT scenario, device, action, parameter, preferred_value, created_at, updated_at
                FROM {self.table_name}
                WHERE user_id = %s
            """
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()
            cursor.close()

            # 加载到缓存
            with self._lock:
                self._cache[user_id] = []
                for row in rows:
                    self._cache[user_id].append(
                        {
                            "scenario": row["scenario"],
                            "device": row["device"],
                            "action": row["action"],
                            "parameter": row["parameter"],
                            "preferred_value": row["preferred_value"],
                            "created_at": row["created_at"],
                            "updated_at": row["updated_at"],
                        }
                    )

            logger.info("从数据库加载用户偏好: %s -> %d 条", user_id, len(rows))
            return len(rows)

        except Exception as error:
            logger.error("从数据库加载偏好失败: %s", error, exc_info=True)
            return 0

    def clear_cache(self, user_id: Optional[str] = None) -> None:
        """清空缓存。

        Args:
            user_id: 用户ID,不指定则清空所有
        """
        with self._lock:
            if user_id:
                self._cache.pop(user_id, None)
                logger.info("清空用户缓存: %s", user_id)
            else:
                self._cache.clear()
                logger.info("清空所有缓存")
