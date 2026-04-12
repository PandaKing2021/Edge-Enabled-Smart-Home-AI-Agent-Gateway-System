"""Preference memory manager module.

Stores and manages user correction preferences for auto-generated tasks.
"""

import json
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PreferenceManager:
    """Preference Memory Manager.

    Records user corrections to task execution results, enabling personalized optimization.

    Attributes:
        db_connection: Database connection object
        table_name: Preference table name
    """

    def __init__(self, db_connection=None, table_name: str = "user_preferences") -> None:
        """Initialize preference manager.

        Args:
            db_connection: Database connection object (MySQL connector)
            table_name: Preference table name
        """
        self.db_connection = db_connection
        self.table_name = table_name
        self._lock = threading.Lock()

        # In-memory cache
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
        """Record user preference correction.

        Args:
            user_id: User ID
            scenario: Scenario identifier (e.g., "sleep", "movie")
            device: Device ID
            action: Action name
            parameter: Parameter name
            preferred_value: User's preferred value

        Returns:
            bool: Whether recording was successful
        """
        try:
            timestamp = datetime.now()

            # Store to in-memory cache
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

                # Check if same preference already exists
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
                    # Update existing preference
                    self._cache[user_id][existing_idx].update(preference)
                else:
                    # Add new preference
                    self._cache[user_id].append(preference)

            # Store to database
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
                "Recorded user preference: %s -> %s.%s.%s=%s",
                user_id,
                device,
                action,
                parameter,
                preferred_value,
            )
            return True

        except Exception as error:
            logger.error("Failed to record user preference: %s", error, exc_info=True)
            return False

    def get_user_preferences(
        self, user_id: str, scenario: Optional[str] = None
    ) -> Dict:
        """Get user preferences.

        Args:
            user_id: User ID
            scenario: Scenario identifier, optional (returns all preferences if not specified)

        Returns:
            Dict: User preferences dictionary {scenario: [{device, action, parameter, preferred_value}]}
        """
        try:
            # Get from cache
            with self._lock:
                user_prefs = self._cache.get(user_id, [])

            # Group by scenario
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
                "Retrieved user preferences: %s (scenario: %s) -> %d items",
                user_id,
                scenario or "all",
                sum(len(v) for v in preferences_by_scenario.values()),
            )

            return preferences_by_scenario

        except Exception as error:
            logger.error("Failed to get user preferences: %s", error, exc_info=True)
            return {}

    def apply_preferences(
        self, user_id: str, scenario: str, task_plan: Dict
    ) -> Dict:
        """Apply user preferences to task plan.

        Args:
            user_id: User ID
            scenario: Scenario identifier
            task_plan: Task plan dictionary

        Returns:
            Dict: Task plan after applying preferences
        """
        try:
            # Get user preferences for this scenario
            preferences = self.get_user_preferences(user_id, scenario)

            if scenario not in preferences:
                return task_plan

            user_prefs = preferences[scenario]

            # Apply preferences to tasks
            tasks = task_plan.get("tasks", [])
            modified_tasks = []

            for task in tasks:
                modified_task = task.copy()

                # Check for matching preferences
                for pref in user_prefs:
                    if (
                        pref["device"] == task.get("device")
                        and pref["action"] == task.get("action")
                    ):
                        # Apply preferred value
                        modified_task["value"] = pref["preferred_value"]
                        logger.info(
                            "Applied user preference: %s.%s=%s",
                            pref["device"],
                            pref["action"],
                            pref["preferred_value"],
                        )

                modified_tasks.append(modified_task)

            task_plan["tasks"] = modified_tasks
            return task_plan

        except Exception as error:
            logger.error("Failed to apply user preferences: %s", error, exc_info=True)
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
        """Save preference to database.

        Args:
            user_id: User ID
            scenario: Scenario identifier
            device: Device ID
            action: Action name
            parameter: Parameter name
            preferred_value: Preferred value

        Returns:
            bool: Whether save was successful
        """
        try:
            if not self.db_connection:
                return False

            cursor = self.db_connection.cursor()

            # Use INSERT ... ON DUPLICATE KEY UPDATE
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

            logger.debug("Preference saved to database")
            return True

        except Exception as error:
            logger.error("Failed to save preference to database: %s", error, exc_info=True)
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

            # Load to cache
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

            logger.info("Loaded user preferences from database: %s -> %d items", user_id, len(rows))
            return len(rows)

        except Exception as error:
            logger.error("Failed to load preferences from database: %s", error, exc_info=True)
            return 0

    def clear_cache(self, user_id: Optional[str] = None) -> None:
        """Clear cache.

        Args:
            user_id: User ID, clear all if not specified
        """
        with self._lock:
            if user_id:
                self._cache.pop(user_id, None)
                logger.info("Cleared user cache: %s", user_id)
            else:
                self._cache.clear()
                logger.info("Cleared all caches")
