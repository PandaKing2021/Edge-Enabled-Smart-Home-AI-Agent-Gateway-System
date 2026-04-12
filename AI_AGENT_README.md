# AI Agent 对话式任务编排系统

基于智谱AI GLM-4.7-Flash实现的智能家居对话式任务自动编排系统。

## 功能特性

- ✨ **自然语言交互**: 用户可通过自然语言指令控制智能家居设备
- 🧠 **意图理解**: 基于GLM-4.7-Flash的意图解析与任务规划
- 🔍 **RAG检索**: 基于设备能力库的增强检索
- 💬 **多轮对话**: 支持上下文保持的连续对话
- 📚 **偏好学习**: 记录用户修正,实现个性化优化
- 🔄 **FSM执行**: 有限状态机确保任务可靠执行,支持失败回滚

## 快速开始

### 1. 安装依赖

```bash
cd Python
pip install -r requirements.txt
```

### 2. 配置API Key

编辑 `Python/Gate/ai_agent_config.txt`,设置你的智谱AI API Key:

```
API_KEY = your_api_key_here
```

获取API Key: https://open.bigmodel.cn/

### 3. 初始化数据库

执行数据库扩展脚本:

```bash
mysql -u root -p < Python/Database\ Server/ai_agent_tables.sql
```

### 4. 运行测试

```bash
cd Python/scripts
python ai_agent_test.py
```

### 5. 启动网关

```bash
cd Python/Gate
python gate.py
```

## 系统架构

```
┌─────────────────┐
│  Android App    │
│  TCP 9301       │
└────────┬────────┘
         │ 对话指令
         ↓
┌─────────────────────────────────────┐
│       Android Handler               │
├─────────────────────────────────────┤
│  AI Agent Module                    │
│  ┌──────────────────────────────┐  │
│  │  Dialog Manager              │  │
│  │  (对话上下文管理)             │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │  Intent Planner              │  │
│  │  (GLM-4.7-Flash 意图解析)     │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │  Capability Retriever        │  │
│  │  (设备能力检索)               │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │  Task Executor               │  │
│  │  (FSM任务执行)                │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │  Device Controller           │  │
│  │  (设备控制接口)               │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │  Preference Manager          │  │
│  │  (偏好学习)                   │  │
│  └──────────────────────────────┘  │
└─────────────────┬───────────────────┘
                  │ 设备控制
                  ↓
          ┌───────────────┐
          │ Gateway State │
          │ (设备状态)     │
          └───────┬───────┘
                  │
                  ↓
          ┌───────────────┐
          │ 设备节点       │
          │ (空调/窗帘等)  │
          └───────────────┘
```

## 核心模块说明

### 1. DialogManager (对话管理器)

管理多轮对话上下文,维护会话历史。

**关键特性:**
- 最多保留5轮对话
- 会话超时自动清理
- 线程安全实现

### 2. IntentPlanner (意图解析器)

调用GLM-4.7-Flash API解析用户意图并生成任务计划。

**关键特性:**
- CoT(Chain-of-Thought)推理
- 结合设备状态和用户偏好
- 输出结构化JSON任务序列

### 3. CapabilityRetriever (RAG检索器)

基于关键词匹配检索相关设备能力。

**关键特性:**
- 设备能力描述库(JSON格式)
- 场景关键词匹配
- 相关性评分排序

### 4. TaskExecutor (任务执行器)

基于FSM的任务执行引擎。

**关键特性:**
- 状态: IDLE → EXECUTING → COMPLETED/FAILED
- 失败自动回滚
- 支持暂停/恢复/取消

### 5. DeviceController (设备控制器)

统一封装设备控制API。

**关键特性:**
- 映射抽象操作到GatewayState阈值
- 参数范围校验
- 设备状态查询

### 6. PreferenceManager (偏好管理器)

记录和应用用户偏好。

**关键特性:**
- 按场景存储偏好
- 自动应用偏好到任务计划
- 持久化到MySQL

## 支持的设备

| 设备ID | 名称 | 支持的动作 |
|--------|------|-----------|
| Light_TH | 智能空调 | turn_on, turn_off, set_temperature(16-30°C), set_humidity(30-90%) |
| Curtain_status | 智能窗帘 | open, close, set_brightness(0-65535 lux) |
| Light_CU | 智能灯光 | set_brightness(0-65535) |
| Door_Security_Status | 智能门禁 | verify_card(自动验证) |

## 支持的场景

| 场景 | 触发关键词 | 建议操作 |
|------|-----------|---------|
| 睡眠模式 | 困了、睡觉、休息、睡眠 | 空调24°C湿度50%、关闭窗帘、关灯 |
| 观影模式 | 看电影、观影、电影、影院 | 关闭窗帘、灯光10%、空调23°C |
| 离家模式 | 出门、离开、上班、外出 | 关闭空调、关灯、关闭窗帘 |
| 回家模式 | 回家、到家、回来 | 开启空调25°C、打开窗帘 |

## 对话示例

```
用户: "我困了,准备睡觉"
系统: 
  推理: 用户希望进入睡眠状态,需要准备睡眠环境
  任务: 
    1. 空调温度设置为24°C
    2. 空调湿度设置为50%
    3. 关闭窗帘
    4. 灯光亮度设置为0
  结果: 任务执行成功

用户: "把空调温度调低一点"
系统:
  推理: 用户觉得当前温度偏高,需要降低温度
  任务:
    1. 空调温度设置为22°C(应用用户偏好)
  结果: 任务执行成功
```

## API协议

### 对话请求格式

Android App发送:

```json
{
  "state": "chat",
  "data": {
    "account": "user_id",
    "session_id": "uuid" // 可选
  },
  "status": 1
}
```

### 对话响应格式

网关返回:

```json
{
  "type": "chat_response",
  "status": "success",
  "user_input": "我困了",
  "reasoning": "推理过程...",
  "tasks": [
    {"device": "Light_TH", "action": "set_temperature", "value": 24}
  ],
  "execution_result": {
    "success": true,
    "message": "任务执行完成",
    "details": [...]
  }
}
```

## 配置文件说明

### ai_agent_config.txt

```ini
[LLM]
API_KEY = your_api_key_here
BASE_URL = https://open.bigmodel.cn/api/paas/v4
MODEL_NAME = GLM-4.7-Flash
TEMPERATURE = 0.7

[DIALOG]
MAX_CONTEXT_TURNS = 5
SESSION_TIMEOUT = 3600

[TASK_EXECUTOR]
ENABLE_ROLLBACK = True
MAX_RETRY = 3
TASK_TIMEOUT = 30
```

## 性能指标

- **意图解析延迟**: 1-2秒 (云端API调用)
- **任务执行延迟**: < 100ms (本地执行)
- **对话上下文容量**: 最多5轮对话
- **并发会话支持**: 无限制(内存允许)

## 故障排查

### 问题1: API Key未配置

**症状**: 启动时警告 "AI Agent API Key 未配置"

**解决**: 编辑 `ai_agent_config.txt`,设置有效的API Key

### 问题2: 数据库表不存在

**症状**: 运行时报错 "Table 'user_test.conversation_history' doesn't exist"

**解决**: 执行 `ai_agent_tables.sql` 创建表结构

### 问题3: 设备能力文件不存在

**症状**: 启动时报错 "设备能力配置文件不存在"

**解决**: 确保 `device_capabilities.json` 存在于 `Python/Gate/` 目录

## 扩展开发

### 添加新设备

编辑 `device_capabilities.json`:

```json
{
  "devices": {
    "NewDevice": {
      "name": "新设备",
      "capabilities": ["功能1", "功能2"],
      "actions": {
        "action_name": {
          "description": "动作描述",
          "operation": "operation_code",
          "params": {...}
        }
      }
    }
  }
}
```

### 添加新场景

编辑 `device_capabilities.json`:

```json
{
  "scenarios": {
    "new_scenario": {
      "name": "新场景",
      "keywords": ["关键词1", "关键词2"],
      "suggested_actions": [
        {"device": "Light_TH", "action": "set_temperature", "value": 25}
      ]
    }
  }
}
```

## 技术栈

- **语言**: Python 3.7+
- **LLM**: 智谱AI GLM-4.7-Flash
- **SDK**: zhipuai
- **数据库**: MySQL
- **并发**: threading

## 许可证

与项目主许可证一致

## 联系方式

项目地址: EdgeIoT-SmartHomeGateway

---

**注意**: 使用本系统需要智谱AI API Key,请确保遵守智谱AI的使用条款和服务限制。
