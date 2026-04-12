"""RAG retriever module.

Lightweight device capability retrieval based on keyword matching.
"""

import json
import logging
import os
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class CapabilityRetriever:
    """Device capability retriever.

    Reads device capabilities from device_capabilities.json, performs retrieval based on keyword matching.

    Attributes:
        capabilities_file: Device capability configuration file path
        capabilities: Device capability dictionary
        scenarios: Scenario dictionary
    """

    def __init__(self, capabilities_file: str) -> None:
        """Initialize retriever.

        Args:
            capabilities_file: Device capability configuration file path
        """
        self.capabilities_file = capabilities_file
        self.capabilities: Dict = {}
        self.scenarios: Dict = {}
        self._load_capabilities()

    def _load_capabilities(self) -> None:
        """Load device capability configuration file."""
        try:
            if not os.path.exists(self.capabilities_file):
                logger.error("Device capability configuration file does not exist: %s", self.capabilities_file)
                return

            with open(self.capabilities_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.capabilities = data.get("devices", {})
            self.scenarios = data.get("scenarios", {})
            logger.info(
                "Loaded device capabilities: %d devices, %d scenarios",
                len(self.capabilities),
                len(self.scenarios),
            )

        except Exception as error:
            logger.error("Failed to load device capability configuration: %s", error)

    def retrieve_relevant_devices(self, query: str, top_k: int = 3) -> List[Dict]:
        """Retrieve devices relevant to query.

        Args:
            query: User query string
            top_k: Top-k most relevant devices to return

        Returns:
            List[Dict]: Relevant device list, each element contains device_id and device_info
        """
        query_lower = query.lower()
        scored_devices = []

        for device_id, device_info in self.capabilities.items():
            score = self._calculate_relevance_score(query_lower, device_info)
            if score > 0:
                scored_devices.append((device_id, device_info, score))

        # Sort by relevance score in descending order
        scored_devices.sort(key=lambda x: x[2], reverse=True)

        # Return top-k results
        results = []
        for device_id, device_info, score in scored_devices[:top_k]:
            results.append(
                {
                    "device_id": device_id,
                    "device_info": device_info,
                    "relevance_score": score,
                }
            )

        logger.debug(
            "Retrieval query '%s' returned %d devices: %s",
            query,
            len(results),
            [r["device_id"] for r in results],
        )
        return results

    def retrieve_scenario(self, query: str) -> Optional[Dict]:
        """Retrieve matching scenario.

        Args:
            query: User query string

        Returns:
            Optional[Dict]: Matched scenario information, returns None if no match
        """
        query_lower = query.lower()

        for scenario_id, scenario_info in self.scenarios.items():
            # Check if scenario keywords are in the query
            keywords = scenario_info.get("keywords", [])
            for keyword in keywords:
                if keyword in query_lower:
                    logger.info("Matched scenario: %s (keyword: %s)", scenario_id, keyword)
                    return {
                        "scenario_id": scenario_id,
                        "scenario_info": scenario_info,
                        "matched_keyword": keyword,
                    }

        return None

    def _calculate_relevance_score(self, query: str, device_info: Dict) -> float:
        """Calculate relevance score between query and device.

        Args:
            query: Query string (already lowercased)
            device_info: Device information dictionary

        Returns:
            float: Relevance score (0-10)
        """
        score = 0.0

        # Check device name
        name = device_info.get("name", "").lower()
        name_en = device_info.get("name_en", "").lower()
        if name in query or name_en in query:
            score += 3.0

        # Check keywords
        keywords = device_info.get("keywords", [])
        matched_keywords = sum(1 for kw in keywords if kw in query)
        score += matched_keywords * 1.5

        # Check capability descriptions
        capabilities = device_info.get("capabilities", [])
        for capability in capabilities:
            if capability in query:
                score += 1.0

        return score

    def get_device_actions(self, device_id: str) -> Optional[Dict]:
        """Get all available actions for a device.

        Args:
            device_id: Device ID

        Returns:
            Optional[Dict]: Action dictionary, returns None if not exists
        """
        device_info = self.capabilities.get(device_id)
        if device_info:
            return device_info.get("actions", {})
        return None

    def get_device_info(self, device_id: str) -> Optional[Dict]:
        """Get complete device information.

        Args:
            device_id: Device ID

        Returns:
            Optional[Dict]: Device information dictionary, returns None if not exists
        """
        return self.capabilities.get(device_id)

    def format_capabilities_for_prompt(self, devices: List[Dict]) -> str:
        """Format device capabilities into LLM prompt text.

        Args:
            devices: Device list

        Returns:
            str: Formatted device capability description
        """
        if not devices:
            return "No relevant devices"

        parts = []
        for i, device in enumerate(devices, 1):
            device_id = device["device_id"]
            device_info = device["device_info"]
            score = device["relevance_score"]

            parts.append(f"{i}. {device_info['name']} (ID: {device_id})")
            parts.append(f"   Description: {device_info['description']}")
            parts.append(f"   Capabilities: {', '.join(device_info['capabilities'])}")

            # List available actions
            actions = device_info.get("actions", {})
            if actions:
                parts.append("   Available actions:")
                for action_name, action_info in actions.items():
                    params_desc = ""
                    if "params" in action_info and action_info["params"]:
                        params_desc = " (params: " + ", ".join(action_info["params"].keys()) + ")"
                    parts.append(f"     - {action_info['description']}{params_desc}")

            parts.append("")

        return "\n".join(parts)
