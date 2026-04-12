"""Intent parsing and task planner module.

Integrates Zhipu AI GLM-4.7-Flash, implements intent understanding and task planning.
"""

import json
import logging
from typing import TYPE_CHECKING, Dict, List, Optional

from zhipuai import ZhipuAI

if TYPE_CHECKING:
    from .capability_retriever import CapabilityRetriever
    from .preference_manager import PreferenceManager

logger = logging.getLogger(__name__)


class IntentPlanner:
    """Intent parsing and task planner.

    Uses GLM-4.7-Flash model to parse user intent and generate task plan.

    Attributes:
        api_key: Zhipu AI API key
        base_url: API base URL
        model_name: Model name
        temperature: Generation temperature
        client: ZhipuAI client
        capability_retriever: Device capability retriever
        preference_manager: Preference manager
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://open.bigmodel.cn/api/paas/v4",
        model_name: str = "GLM-4.7-Flash",
        temperature: float = 0.7,
        capability_retriever: Optional["CapabilityRetriever"] = None,
        preference_manager: Optional["PreferenceManager"] = None,
    ) -> None:
        """Initialize intent parser.

        Args:
            api_key: Zhipu AI API key
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

        # Initialize ZhipuAI client
        try:
            self.client = ZhipuAI(api_key=api_key, base_url=base_url)
            logger.info("ZhipuAI client initialized successfully: %s", model_name)
        except Exception as error:
            logger.error("ZhipuAI client initialization failed: %s", error)
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

            # 5. Call GLM-4.7-Flash
            logger.info("Calling GLM-4.7-Flash for intent parsing: %s", user_input)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )

            # 6. Parse response
            content = response.choices[0].message.content
            logger.debug("GLM response: %s", content)

            task_plan = self._parse_task_plan(content)

            logger.info("Task planning completed: %d tasks", len(task_plan.get("tasks", [])))
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
