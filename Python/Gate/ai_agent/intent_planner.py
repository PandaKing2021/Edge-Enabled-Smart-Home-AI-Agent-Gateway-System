"""意图解析与任务规划器模块。

集成智谱AI GLM-4.7-Flash,实现意图理解与任务规划。
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
    """意图解析与任务规划器。

    使用GLM-4.7-Flash模型解析用户意图并生成任务计划。

    Attributes:
        api_key: 智谱AI API密钥
        base_url: API基础URL
        model_name: 模型名称
        temperature: 生成温度
        client: ZhipuAI客户端
        capability_retriever: 设备能力检索器
        preference_manager: 偏好管理器
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
        """初始化意图解析器。

        Args:
            api_key: 智谱AI API密钥
            base_url: API基础URL
            model_name: 模型名称
            temperature: 生成温度(0-1)
            capability_retriever: 设备能力检索器实例
            preference_manager: 偏好管理器实例
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.temperature = temperature
        self.capability_retriever = capability_retriever
        self.preference_manager = preference_manager

        # 初始化ZhipuAI客户端
        try:
            self.client = ZhipuAI(api_key=api_key, base_url=base_url)
            logger.info("ZhipuAI客户端初始化成功: %s", model_name)
        except Exception as error:
            logger.error("ZhipuAI客户端初始化失败: %s", error)
            raise

    def plan_tasks(
        self,
        user_input: str,
        device_state: Dict,
        context_history: str = "无历史对话",
        user_id: Optional[str] = None,
    ) -> Dict:
        """解析用户意图并生成任务计划。

        Args:
            user_input: 用户输入的自然语言指令
            device_state: 当前设备状态字典
            context_history: 对话上下文历史
            user_id: 用户ID,用于查询偏好

        Returns:
            Dict: 任务计划,包含reasoning和tasks字段
        """
        try:
            # 1. 检索相关设备
            relevant_devices = []
            if self.capability_retriever:
                relevant_devices = self.capability_retriever.retrieve_relevant_devices(
                    user_input, top_k=3
                )

            # 2. 检索匹配场景
            matched_scenario = None
            if self.capability_retriever:
                matched_scenario = self.capability_retriever.retrieve_scenario(user_input)

            # 3. 检索用户偏好
            user_preferences = {}
            if self.preference_manager and user_id:
                user_preferences = self.preference_manager.get_user_preferences(user_id)

            # 4. 构建提示词
            prompt = self._build_planning_prompt(
                user_input=user_input,
                device_state=device_state,
                relevant_devices=relevant_devices,
                matched_scenario=matched_scenario,
                user_preferences=user_preferences,
                context_history=context_history,
            )

            # 5. 调用GLM-4.7-Flash
            logger.info("调用GLM-4.7-Flash进行意图解析: %s", user_input)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )

            # 6. 解析响应
            content = response.choices[0].message.content
            logger.debug("GLM响应: %s", content)

            task_plan = self._parse_task_plan(content)

            logger.info("任务规划完成: %d个任务", len(task_plan.get("tasks", [])))
            return task_plan

        except Exception as error:
            logger.error("意图解析失败: %s", error, exc_info=True)
            return {
                "reasoning": f"解析失败: {str(error)}",
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
        """构建任务规划提示词。

        Args:
            user_input: 用户输入
            device_state: 设备状态
            relevant_devices: 相关设备列表
            matched_scenario: 匹配的场景
            user_preferences: 用户偏好
            context_history: 对话上下文

        Returns:
            str: 格式化的提示词
        """
        # 格式化设备状态
        device_state_str = json.dumps(device_state, ensure_ascii=False, indent=2)

        # 格式化相关设备能力
        if self.capability_retriever:
            capabilities_str = self.capability_retriever.format_capabilities_for_prompt(
                relevant_devices
            )
        else:
            capabilities_str = "无设备能力信息"

        # 格式化场景建议
        scenario_str = ""
        if matched_scenario:
            scenario_info = matched_scenario["scenario_info"]
            scenario_str = f"""
检测到场景: {scenario_info['name']}
场景描述: {scenario_info['description']}
建议操作: {json.dumps(scenario_info['suggested_actions'], ensure_ascii=False, indent=2)}
"""

        # 格式化用户偏好
        preferences_str = "无偏好记录"
        if user_preferences:
            preferences_str = json.dumps(user_preferences, ensure_ascii=False, indent=2)

        # 构建完整提示词
        prompt = f"""你是一个智能家居任务编排助手。用户指令："{user_input}"

对话上下文：
{context_history}

当前设备状态：
{device_state_str}

相关设备能力：
{capabilities_str}
{scenario_str}
用户偏好：
{preferences_str}

请逐步思考并生成任务执行计划：
1. 分析用户意图和需求
2. 识别需要的设备和操作
3. 考虑用户偏好调整参数
4. 按顺序列出执行步骤

输出格式为JSON，严格按照以下格式：
{{
  "reasoning": "你的思考过程",
  "tasks": [
    {{"device": "设备ID", "action": "动作名称", "value": 参数值}},
    {{"device": "设备ID", "action": "动作名称", "value": 参数值}}
  ]
}}

注意：
- device字段必须是设备ID(如"Light_TH", "Curtain_status")
- action字段必须是设备支持的action名称(如"set_temperature", "open", "close")
- value字段为参数值,如果没有参数则设为null
- 如果无法理解用户意图或没有相关设备,返回空tasks列表

请直接输出JSON,不要包含其他文字。"""

        return prompt

    def _parse_task_plan(self, content: str) -> Dict:
        """解析LLM返回的任务计划。

        Args:
            content: LLM返回的内容

        Returns:
            Dict: 解析后的任务计划
        """
        try:
            # 尝试直接解析JSON
            task_plan = json.loads(content)
            return task_plan

        except json.JSONDecodeError:
            # 尝试提取JSON部分
            try:
                # 查找第一个 { 和最后一个 }
                start = content.find("{")
                end = content.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = content[start:end]
                    task_plan = json.loads(json_str)
                    return task_plan
                else:
                    logger.warning("无法从响应中提取JSON: %s", content)
                    return {
                        "reasoning": "响应格式错误",
                        "tasks": [],
                        "error": "Invalid JSON format",
                    }
            except Exception as error:
                logger.error("解析任务计划失败: %s", error)
                return {
                    "reasoning": f"解析失败: {str(error)}",
                    "tasks": [],
                    "error": str(error),
                }

    def quick_plan(self, user_input: str, device_state: Dict) -> Dict:
        """快速规划(简化版,不包含偏好和上下文)。

        Args:
            user_input: 用户输入
            device_state: 设备状态

        Returns:
            Dict: 任务计划
        """
        return self.plan_tasks(
            user_input=user_input,
            device_state=device_state,
            context_history="无历史对话",
            user_id=None,
        )
