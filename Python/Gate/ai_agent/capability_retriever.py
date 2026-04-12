"""RAG检索器模块。

基于关键词匹配的轻量级设备能力检索。
"""

import json
import logging
import os
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class CapabilityRetriever:
    """设备能力检索器。

    从device_capabilities.json读取设备能力,基于关键词匹配进行检索。

    Attributes:
        capabilities_file: 设备能力配置文件路径
        capabilities: 设备能力字典
        scenarios: 场景字典
    """

    def __init__(self, capabilities_file: str) -> None:
        """初始化检索器。

        Args:
            capabilities_file: 设备能力配置文件路径
        """
        self.capabilities_file = capabilities_file
        self.capabilities: Dict = {}
        self.scenarios: Dict = {}
        self._load_capabilities()

    def _load_capabilities(self) -> None:
        """加载设备能力配置文件。"""
        try:
            if not os.path.exists(self.capabilities_file):
                logger.error("设备能力配置文件不存在: %s", self.capabilities_file)
                return

            with open(self.capabilities_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.capabilities = data.get("devices", {})
            self.scenarios = data.get("scenarios", {})
            logger.info(
                "加载设备能力: %d个设备, %d个场景",
                len(self.capabilities),
                len(self.scenarios),
            )

        except Exception as error:
            logger.error("加载设备能力配置失败: %s", error)

    def retrieve_relevant_devices(self, query: str, top_k: int = 3) -> List[Dict]:
        """检索与查询相关的设备。

        Args:
            query: 用户查询字符串
            top_k: 返回的top-k个最相关设备

        Returns:
            List[Dict]: 相关设备列表,每个元素包含device_id和device_info
        """
        query_lower = query.lower()
        scored_devices = []

        for device_id, device_info in self.capabilities.items():
            score = self._calculate_relevance_score(query_lower, device_info)
            if score > 0:
                scored_devices.append((device_id, device_info, score))

        # 按相关性分数降序排序
        scored_devices.sort(key=lambda x: x[2], reverse=True)

        # 返回top-k结果
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
            "检索查询 '%s' 返回 %d 个设备: %s",
            query,
            len(results),
            [r["device_id"] for r in results],
        )
        return results

    def retrieve_scenario(self, query: str) -> Optional[Dict]:
        """检索匹配的场景。

        Args:
            query: 用户查询字符串

        Returns:
            Optional[Dict]: 匹配的场景信息,无匹配返回None
        """
        query_lower = query.lower()

        for scenario_id, scenario_info in self.scenarios.items():
            # 检查场景关键词是否在查询中
            keywords = scenario_info.get("keywords", [])
            for keyword in keywords:
                if keyword in query_lower:
                    logger.info("匹配场景: %s (关键词: %s)", scenario_id, keyword)
                    return {
                        "scenario_id": scenario_id,
                        "scenario_info": scenario_info,
                        "matched_keyword": keyword,
                    }

        return None

    def _calculate_relevance_score(self, query: str, device_info: Dict) -> float:
        """计算查询与设备的相关性分数。

        Args:
            query: 查询字符串(已转小写)
            device_info: 设备信息字典

        Returns:
            float: 相关性分数(0-10)
        """
        score = 0.0

        # 检查设备名称
        name = device_info.get("name", "").lower()
        name_en = device_info.get("name_en", "").lower()
        if name in query or name_en in query:
            score += 3.0

        # 检查关键词
        keywords = device_info.get("keywords", [])
        matched_keywords = sum(1 for kw in keywords if kw in query)
        score += matched_keywords * 1.5

        # 检查能力描述
        capabilities = device_info.get("capabilities", [])
        for capability in capabilities:
            if capability in query:
                score += 1.0

        return score

    def get_device_actions(self, device_id: str) -> Optional[Dict]:
        """获取设备的所有可用动作。

        Args:
            device_id: 设备ID

        Returns:
            Optional[Dict]: 动作字典,不存在返回None
        """
        device_info = self.capabilities.get(device_id)
        if device_info:
            return device_info.get("actions", {})
        return None

    def get_device_info(self, device_id: str) -> Optional[Dict]:
        """获取设备的完整信息。

        Args:
            device_id: 设备ID

        Returns:
            Optional[Dict]: 设备信息字典,不存在返回None
        """
        return self.capabilities.get(device_id)

    def format_capabilities_for_prompt(self, devices: List[Dict]) -> str:
        """将设备能力格式化为LLM提示文本。

        Args:
            devices: 设备列表

        Returns:
            str: 格式化的设备能力描述
        """
        if not devices:
            return "无相关设备"

        parts = []
        for i, device in enumerate(devices, 1):
            device_id = device["device_id"]
            device_info = device["device_info"]
            score = device["relevance_score"]

            parts.append(f"{i}. {device_info['name']} (ID: {device_id})")
            parts.append(f"   描述: {device_info['description']}")
            parts.append(f"   能力: {', '.join(device_info['capabilities'])}")

            # 列出可用动作
            actions = device_info.get("actions", {})
            if actions:
                parts.append("   可用动作:")
                for action_name, action_info in actions.items():
                    params_desc = ""
                    if "params" in action_info and action_info["params"]:
                        params_desc = " (参数: " + ", ".join(action_info["params"].keys()) + ")"
                    parts.append(f"     - {action_info['description']}{params_desc}")

            parts.append("")

        return "\n".join(parts)
