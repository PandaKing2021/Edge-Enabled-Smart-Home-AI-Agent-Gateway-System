#!/usr/bin/env python3
"""AI Agent 测试脚本。

测试AI Agent的核心功能:
- 意图解析和任务规划
- 设备能力检索
- 任务执行
- 对话管理
"""

import json
import logging
import sys
from pathlib import Path

# 设置编码 (Windows兼容)
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_GATE_DIR = _PROJECT_ROOT / "Gate"

if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
if str(_GATE_DIR) not in sys.path:
    sys.path.insert(0, str(_GATE_DIR))

from ai_agent import (
    DialogManager,
    IntentPlanner,
    CapabilityRetriever,
    TaskExecutor,
    DeviceController,
    PreferenceManager,
)
from common.models import GatewayState

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_capability_retriever():
    """测试设备能力检索器。"""
    print("\n" + "="*60)
    print("测试1: 设备能力检索器")
    print("="*60)

    capabilities_file = _GATE_DIR / "device_capabilities.json"
    retriever = CapabilityRetriever(str(capabilities_file))

    # 测试查询
    test_queries = [
        "我困了,想睡觉",
        "准备看电影",
        "打开空调",
        "把窗帘拉上",
    ]

    for query in test_queries:
        print(f"\n查询: '{query}'")
        devices = retriever.retrieve_relevant_devices(query, top_k=3)
        scenario = retriever.retrieve_scenario(query)

        print(f"  相关设备: {[d['device_id'] for d in devices]}")
        if scenario:
            print(f"  匹配场景: {scenario['scenario_id']}")


def test_dialog_manager():
    """测试对话管理器。"""
    print("\n" + "="*60)
    print("测试2: 对话管理器")
    print("="*60)

    dialog_manager = DialogManager(max_context_turns=3)

    # 创建会话
    session_id = dialog_manager.create_session(user_id="test_user")
    print(f"创建会话: {session_id}")

    # 添加对话轮次
    dialog_manager.add_message(
        session_id,
        user_input="我困了",
        agent_response="好的,正在为您准备睡眠环境",
    )

    dialog_manager.add_message(
        session_id,
        user_input="把空调调低一点",
        agent_response="已将温度调低",
    )

    # 获取上下文
    context = dialog_manager.get_context_string(session_id)
    print(f"\n对话上下文:\n{context}")

    # 获取会话信息
    session_info = dialog_manager.get_session_info(session_id)
    print(f"\n会话信息: {session_info}")


def test_intent_planner():
    """测试意图解析器(需要API Key)。"""
    print("\n" + "="*60)
    print("测试3: 意图解析器")
    print("="*60)

    # 读取配置
    config_file = _GATE_DIR / "ai_agent_config.txt"
    api_key = None

    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("API_KEY"):
                    api_key = line.split("=", 1)[1].strip()
                    break

    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("⚠️  API Key 未配置,跳过意图解析测试")
        print("请在 ai_agent_config.txt 中设置 API_KEY")
        return

    # 初始化组件
    capabilities_file = _GATE_DIR / "device_capabilities.json"
    retriever = CapabilityRetriever(str(capabilities_file))

    planner = IntentPlanner(
        api_key=api_key,
        capability_retriever=retriever,
    )

    # 模拟设备状态
    device_state = {
        "Light_TH": {
            "temperature": 26,
            "humidity": 60,
        },
        "Curtain_status": {
            "status": 1,
        }
    }

    # 测试意图解析
    test_inputs = [
        "我困了",
        "准备看电影",
        "把空调温度调到24度",
    ]

    for user_input in test_inputs:
        print(f"\n用户输入: '{user_input}'")
        try:
            task_plan = planner.quick_plan(user_input, device_state)
            print(f"推理过程: {task_plan.get('reasoning', '')}")
            print(f"任务列表: {json.dumps(task_plan.get('tasks', []), ensure_ascii=False, indent=2)}")
        except Exception as e:
            print(f"❌ 解析失败: {e}")


def test_task_executor():
    """测试任务执行器。"""
    print("\n" + "="*60)
    print("测试4: 任务执行器")
    print("="*60)

    # 创建模拟状态
    state = GatewayState()
    state.data_from_source = {
        "Temperature": 25,
        "Humidity": 55,
        "Brightness": 500,
    }

    # 初始化组件
    device_controller = DeviceController(state)
    task_executor = TaskExecutor(
        device_controller=device_controller,
        enable_rollback=True,
    )

    # 测试任务计划
    task_plan = {
        "reasoning": "测试任务执行",
        "tasks": [
            {"device": "Light_TH", "action": "set_temperature", "value": 24},
            {"device": "Curtain_status", "action": "close"},
        ]
    }

    print(f"\n执行任务计划:")
    print(json.dumps(task_plan, ensure_ascii=False, indent=2))

    result = task_executor.execute_task_plan(task_plan)
    print(f"\n执行结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 检查状态更新
    threshold = state.threshold_data
    print(f"\n阈值状态更新:")
    print(f"  温度阈值: {threshold.get('Temperature')}")
    print(f"  光照度阈值: {threshold.get('Brightness')}")


def test_preference_manager():
    """测试偏好管理器。"""
    print("\n" + "="*60)
    print("测试5: 偏好管理器")
    print("="*60)

    preference_manager = PreferenceManager(db_connection=None)

    # 记录偏好
    preference_manager.record_preference(
        user_id="test_user",
        scenario="sleep",
        device="Light_TH",
        action="set_temperature",
        parameter="temperature",
        preferred_value="22",
    )

    preference_manager.record_preference(
        user_id="test_user",
        scenario="movie",
        device="Light_CU",
        action="set_brightness",
        parameter="brightness",
        preferred_value="10",
    )

    # 查询偏好
    preferences = preference_manager.get_user_preferences("test_user")
    print(f"\n用户偏好:")
    print(json.dumps(preferences, ensure_ascii=False, indent=2))

    # 应用偏好
    task_plan = {
        "reasoning": "测试偏好应用",
        "tasks": [
            {"device": "Light_TH", "action": "set_temperature", "value": 24},
        ]
    }

    modified_plan = preference_manager.apply_preferences(
        "test_user", "sleep", task_plan
    )

    print(f"\n应用偏好后的任务计划:")
    print(json.dumps(modified_plan, ensure_ascii=False, indent=2))


def main():
    """运行所有测试。"""
    print("\n" + "╔"+ "="*58 + "╗")
    print("║" + " "*15 + "AI Agent 测试套件" + " "*15 + "║")
    print("╚" + "="*58 + "╝")

    try:
        test_capability_retriever()
        test_dialog_manager()
        test_intent_planner()
        test_task_executor()
        test_preference_manager()

        print("\n" + "="*60)
        print("✅ 所有测试完成")
        print("="*60)

    except Exception as e:
        logger.error("测试失败: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
