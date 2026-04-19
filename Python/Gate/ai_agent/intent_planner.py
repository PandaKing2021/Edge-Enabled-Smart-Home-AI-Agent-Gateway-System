"""Intent parsing and task planner module.

Integrates OpenAI GPT model, implements intent understanding and task planning.
"""

import hashlib
import json
import logging
import time
from collections import OrderedDict
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from openai import OpenAI

if TYPE_CHECKING:
    from .capability_retriever import CapabilityRetriever
    from .preference_manager import PreferenceManager

logger = logging.getLogger(__name__)


class IntentPlanner:
    """Intent parsing and task planner.

    Uses OpenAI GPT model to parse user intent and generate task plan.

    Attributes:
        api_key: OpenAI API key
        base_url: API base URL
        model_name: Model name
        temperature: Generation temperature
        client: OpenAI client
        capability_retriever: Device capability retriever
        preference_manager: Preference manager
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.7,
        capability_retriever: Optional["CapabilityRetriever"] = None,
        preference_manager: Optional["PreferenceManager"] = None,
    ) -> None:
        """Initialize intent parser.

        Args:
            api_key: OpenAI API key
            base_url: API base URL
            model_name: Model name
            temperature: Generation temperature (0-1)
            capability_retriever: Device capability retriever instance
            preference_manager: Preference manager instance
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.temperature = temperature
        self.capability_retriever = capability_retriever
        self.preference_manager = preference_manager

        # Intent cache mechanism
        self._intent_cache: OrderedDict[str, Tuple[Dict, float]] = OrderedDict()
        self._cache_ttl = 3600  # Cache TTL: 1 hour
        self._cache_max_size = 500  # Maximum cached entries
        self._cache_hits = 0
        self._cache_misses = 0

        # High-frequency command direct mapping (skip LLM)
        self._high_freq_commands: Dict[str, Dict] = {
            # Air conditioner
            "打开空调": {"device": "Light_TH", "action": "turn_on", "value": None},
            "开启空调": {"device": "Light_TH", "action": "turn_on", "value": None},
            "关闭空调": {"device": "Light_TH", "action": "turn_off", "value": None},
            "开空调": {"device": "Light_TH", "action": "turn_on", "value": None},
            "关空调": {"device": "Light_TH", "action": "turn_off", "value": None},
            # Curtain
            "打开窗帘": {"device": "Curtain_status", "action": "open", "value": None},
            "开启窗帘": {"device": "Curtain_status", "action": "open", "value": None},
            "关闭窗帘": {"device": "Curtain_status", "action": "close", "value": None},
            "开窗帘": {"device": "Curtain_status", "action": "open", "value": None},
            "关窗帘": {"device": "Curtain_status", "action": "close", "value": None},
            # Scenarios
            "晚安": {"scenario": "sleep"},
            "睡眠模式": {"scenario": "sleep"},
            "睡觉": {"scenario": "sleep"},
            "离家模式": {"scenario": "leave"},
            "出门": {"scenario": "leave"},
            "回家模式": {"scenario": "home"},
            "回家": {"scenario": "home"},
            "观影模式": {"scenario": "movie"},
            "看电影": {"scenario": "movie"},
        }

        # Initialize OpenAI client
        try:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            logger.info("OpenAI client initialized successfully: %s", model_name)
        except Exception as error:
            logger.error("OpenAI client initialization failed: %s", error)
            raise

    def plan_tasks(
        self,
        user_input: str,
        device_state: Dict,
        context_history: str = "No dialogue history",
        user_id: Optional[str] = None,
    ) -> Dict:
        """Parse user intent and generate task plan.

        Args:
            user_input: User input natural language command
            device_state: Current device status dictionary
            context_history: Dialogue context history
            user_id: User ID, used to query preferences

        Returns:
            Dict: Task plan, containing reasoning and tasks fields
        """
        try:
            # === Phase 1: High-frequency command direct mapping ===
            normalized_input = user_input.strip()
            if normalized_input in self._high_freq_commands:
                mapping = self._high_freq_commands[normalized_input]
                logger.info("High-frequency command cache hit: '%s'", user_input)
                self._cache_hits += 1

                # Scenario mapping
                if "scenario" in mapping:
                    scenario_key = mapping["scenario"]
                    task_plan = self._resolve_scenario(scenario_key, device_state)
                    task_plan["cache_hit"] = True
                    task_plan["cache_type"] = "high_freq_scenario"
                    return task_plan

                # Single device action mapping
                task_plan = {
                    "reasoning": f"High-frequency command direct mapping: {user_input}",
                    "tasks": [mapping],
                    "cache_hit": True,
                    "cache_type": "high_freq_command",
                }
                self._put_cache(normalized_input, user_id, task_plan)
                return task_plan

            # === Phase 2: Historical intent cache lookup ===
            cache_key = self._make_cache_key(user_input, user_id)
            cached_plan = self._get_cache(cache_key)
            if cached_plan is not None:
                logger.info("Intent cache hit: '%s'", user_input[:50])
                self._cache_hits += 1
                cached_plan["cache_hit"] = True
                cached_plan["cache_type"] = "intent_cache"
                return cached_plan

            self._cache_misses += 1

            # === Phase 3: LLM call (original logic) ===
            # 1. Retrieve relevant devices
            relevant_devices = []
            if self.capability_retriever:
                relevant_devices = self.capability_retriever.retrieve_relevant_devices(
                    user_input, top_k=3
                )

            # 2. Retrieve matching scenario
            matched_scenario = None
            if self.capability_retriever:
                matched_scenario = self.capability_retriever.retrieve_scenario(user_input)

            # 3. Retrieve user preferences
            user_preferences = {}
            if self.preference_manager and user_id:
                user_preferences = self.preference_manager.get_user_preferences(user_id)

            # 4. Build prompt
            prompt = self._build_planning_prompt(
                user_input=user_input,
                device_state=device_state,
                relevant_devices=relevant_devices,
                matched_scenario=matched_scenario,
                user_preferences=user_preferences,
                context_history=context_history,
            )

            # 5. Call OpenAI GPT
            logger.info("Calling OpenAI GPT for intent parsing: %s", user_input)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )

            # 6. Parse response
            content = response.choices[0].message.content
            logger.debug("OpenAI response: %s", content)

            task_plan = self._parse_task_plan(content)

            # Cache the successful result
            if task_plan.get("tasks") and not task_plan.get("error"):
                self._put_cache(normalized_input, user_id, task_plan)

            logger.info("Task planning completed: %d tasks", len(task_plan.get("tasks", [])))
            task_plan["cache_hit"] = False
            return task_plan

        except Exception as error:
            logger.error("Intent parsing failed: %s", error, exc_info=True)
            return {
                "reasoning": f"Parse failed: {str(error)}",
                "tasks": [],
                "error": str(error),
            }

    def _build_planning_prompt(
        self,
        user_input: str,
        device_state: Dict,
        relevant_devices: List[Dict],
        matched_scenario: Optional[Dict],
        user_preferences: Dict,
        context_history: str,
    ) -> str:
        """Build task planning prompt.

        Args:
            user_input: User input
            device_state: Device status
            relevant_devices: Relevant device list
            matched_scenario: Matched scenario
            user_preferences: User preferences
            context_history: Dialogue context

        Returns:
            str: Formatted prompt
        """
        # Format device state
        device_state_str = json.dumps(device_state, ensure_ascii=False, indent=2)

        # Format relevant device capabilities
        if self.capability_retriever:
            capabilities_str = self.capability_retriever.format_capabilities_for_prompt(
                relevant_devices
            )
        else:
            capabilities_str = "No device capability information"

        # Format scenario suggestion
        scenario_str = ""
        if matched_scenario:
            scenario_info = matched_scenario["scenario_info"]
            scenario_str = f"""
Detected scenario: {scenario_info['name']}
Scenario description: {scenario_info['description']}
Suggested operations: {json.dumps(scenario_info['suggested_actions'], ensure_ascii=False, indent=2)}
"""

        # Format user preferences
        preferences_str = "No preference records"
        if user_preferences:
            preferences_str = json.dumps(user_preferences, ensure_ascii=False, indent=2)

        # Build complete prompt
        prompt = f"""You are a smart home task orchestration assistant. User instruction: "{user_input}"

Dialogue context:
{context_history}

Current device status:
{device_state_str}

Relevant device capabilities:
{capabilities_str}
{scenario_str}
User preferences:
{preferences_str}

Please think step by step and generate task execution plan:
1. Analyze user intent and requirements
2. Identify required devices and operations
3. Adjust parameters considering user preferences
4. List execution steps in order

Output format must be JSON, strictly following this format:
{{
  "reasoning": "Your thought process",
  "tasks": [
    {{"device": "Device ID", "action": "Action name", "value": parameter value}},
    {{"device": "Device ID", "action": "Action name", "value": parameter value}}
  ]
}}

Notes:
- device field must be device ID (e.g., "Light_TH", "Curtain_status")
- action field must be action name supported by device (e.g., "set_temperature", "open", "close")
- value field is parameter value, set to null if no parameter
- If unable to understand user intent or no relevant devices, return empty tasks list

Please output JSON directly without any other text."""

        return prompt

    def _parse_task_plan(self, content: str) -> Dict:
        """Parse task plan returned by LLM.

        Args:
            content: Content returned by LLM

        Returns:
            Dict: Parsed task plan
        """
        try:
            # Try to parse JSON directly
            task_plan = json.loads(content)
            return task_plan

        except json.JSONDecodeError:
            # Try to extract JSON part
            try:
                # Find first { and last }
                start = content.find("{")
                end = content.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = content[start:end]
                    task_plan = json.loads(json_str)
                    return task_plan
                else:
                    logger.warning("Unable to extract JSON from response: %s", content)
                    return {
                        "reasoning": "Response format error",
                        "tasks": [],
                        "error": "Invalid JSON format",
                    }
            except Exception as error:
                logger.error("Failed to parse task plan: %s", error)
                return {
                    "reasoning": f"Parsing failed: {str(error)}",
                    "tasks": [],
                    "error": str(error),
                }

    def quick_plan(self, user_input: str, device_state: Dict) -> Dict:
        """Quick planning (simplified version, without preferences and context).

        Args:
            user_input: User input
            device_state: Device status

        Returns:
            Dict: Task plan
        """
        return self.plan_tasks(
            user_input=user_input,
            device_state=device_state,
            context_history="No dialogue history",
            user_id=None,
        )

    # ========== Cache Management Methods ==========

    def _make_cache_key(self, user_input: str, user_id: Optional[str] = None) -> str:
        """Generate cache key from user input and optional user ID.

        Uses MD5 hash of the normalized input to keep keys compact.
        """
        normalized = user_input.strip().lower()
        raw_key = f"{user_id}:{normalized}" if user_id else normalized
        return hashlib.md5(raw_key.encode("utf-8")).hexdigest()

    def _get_cache(self, cache_key: str) -> Optional[Dict]:
        """Retrieve cached plan if it exists and has not expired.

        Returns:
            Cached task plan dict, or None if not found / expired.
        """
        if cache_key not in self._intent_cache:
            return None
        cached_plan, timestamp = self._intent_cache[cache_key]
        if time.time() - timestamp > self._cache_ttl:
            # Expired — remove it
            del self._intent_cache[cache_key]
            return None
        # Move to end (most-recently-used) for LRU eviction
        self._intent_cache.move_to_end(cache_key)
        return cached_plan

    def _put_cache(self, user_input: str, user_id: Optional[str], task_plan: Dict) -> None:
        """Store a successful task plan in the intent cache.

        Also performs LRU eviction when the cache exceeds max size.
        """
        cache_key = self._make_cache_key(user_input, user_id)
        self._intent_cache[cache_key] = (task_plan, time.time())
        # Evict oldest entries if over capacity
        while len(self._intent_cache) > self._cache_max_size:
            self._intent_cache.popitem(last=False)  # FIFO eviction (oldest first)

    def _resolve_scenario(self, scenario_key: str, device_state: Dict) -> Dict:
        """Resolve a scenario key into a concrete task plan using device_capabilities.json.

        Falls back to an empty task list if the scenario is unknown.
        """
        # Load scenario actions from device capabilities
        try:
            import os
            cap_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "device_capabilities.json"
            )
            with open(cap_path, "r", encoding="utf-8") as f:
                capabilities = json.load(f)
            scenarios = capabilities.get("scenarios", {})
            if scenario_key in scenarios:
                scenario_info = scenarios[scenario_key]
                return {
                    "reasoning": f"Scenario mode: {scenario_info['name']} - {scenario_info['description']}",
                    "tasks": scenario_info.get("suggested_actions", []),
                }
        except Exception as error:
            logger.warning("Failed to resolve scenario '%s': %s", scenario_key, error)

        return {
            "reasoning": f"Unknown scenario: {scenario_key}",
            "tasks": [],
        }

    def get_cache_stats(self) -> Dict:
        """Return cache statistics for monitoring.

        Returns:
            Dict with cache_hits, cache_misses, hit_rate, cache_size, high_freq_count.
        """
        total = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total if total > 0 else 0.0
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": round(hit_rate, 4),
            "cache_size": len(self._intent_cache),
            "cache_max_size": self._cache_max_size,
            "cache_ttl": self._cache_ttl,
            "high_freq_commands": len(self._high_freq_commands),
        }

    def clear_cache(self) -> None:
        """Clear all cached intent entries and reset hit/miss counters."""
        self._intent_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info("Intent cache cleared")

    def add_high_freq_command(self, command: str, task: Dict) -> None:
        """Register a new high-frequency command mapping at runtime.

        Args:
            command: The exact user input string to match.
            task: A dict with device/action/value or scenario key.
        """
        self._high_freq_commands[command.strip()] = task
        logger.info("Added high-frequency command: '%s'", command)
