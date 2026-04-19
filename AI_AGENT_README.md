# AI Agent Conversational Task Orchestration System

Conversational task automation system for smart home implemented based on OpenAI GPT.

## Features

- ✨ **Natural Language Interaction**: Users can control smart home devices through natural language commands
- 🧠 **Intent Understanding**: Intent parsing and task planning based on OpenAI GPT
- 🔍 **RAG Retrieval**: Enhanced retrieval based on device capability library
- 💬 **Multi-turn Dialogue**: Supports continuous conversations with context maintenance
- 📚 **Preference Learning**: Records user corrections, implements personalized optimization
- 🔄 **FSM Execution**: Finite state machine ensures reliable task execution with rollback support

## Quick Start

### 1. Install Dependencies

```bash
cd Python
pip install -r requirements.txt
```

### 2. Configure API Key

Edit `Python/Gate/ai_agent_config.txt`, set your OpenAI API Key:

```
API_KEY = your_api_key_here
```

Get API Key: https://open.bigmodel.cn/

### 3. Initialize Database

Execute database extension script:

```bash
mysql -u root -p < Python/Database\ Server/ai_agent_tables.sql
```

### 4. Run Tests

```bash
cd Python/scripts
python ai_agent_test.py
```

### 5. Start Gateway

```bash
cd Python/Gate
python gate.py
```

## System Architecture

```
┌─────────────────┐
│  Android App    │
│  TCP 9301       │
└────────┬────────┘
         │ Dialogue Command
         ↓
┌─────────────────────────────────────┐
│       Android Handler               │
├─────────────────────────────────────┤
│  AI Agent Module                    │
│  ┌──────────────────────────────┐  │
│  │  Dialog Manager              │  │
│  │  (Dialogue Context Management)│  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │  Intent Planner              │  │
│  │  (OpenAI GPT Intent Parsing)   │ │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │  Capability Retriever        │  │
│  │  (Device Capability Retrieval) │ │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │  Task Executor               │  │
│  │  (FSM Task Execution)        │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │  Device Controller           │  │
│  │  (Device Control Interface)   │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │  Preference Manager          │  │
│  │  (Preference Learning)        │  │
│  └──────────────────────────────┘  │
└─────────────────┬───────────────────┘
                  │ Device Control
                  ↓
          ┌───────────────┐
          │ Gateway State │
          │ (Device Status)│
          └───────┬───────┘
                  │
                  ↓
          ┌───────────────┐
          │ Device Nodes  │
          │ (AC/Curtain)  │
          └───────────────┘
```

## Core Module Description

### 1. DialogManager (Dialogue Manager)

Manages multi-turn dialogue context, maintains conversation history.

**Key Features:**
- Maintains up to 5 turns of dialogue
- Automatic cleanup on session timeout
- Thread-safe implementation

### 2. IntentPlanner (Intent Parser)

Calls OpenAI GPT API to parse user intent and generate task plan.

**Key Features:**
- CoT (Chain-of-Thought) reasoning
- Combines device status and user preferences
- Outputs structured JSON task sequence

### 3. CapabilityRetriever (RAG Retriever)

Retrieves relevant device capabilities based on keyword matching.

**Key Features:**
- Device capability description library (JSON format)
- Scenario keyword matching
- Relevance scoring and sorting

### 4. TaskExecutor (Task Executor)

FSM-based task execution engine.

**Key Features:**
- States: IDLE → EXECUTING → COMPLETED/FAILED
- Automatic rollback on failure
- Supports pause/resume/cancel

### 5. DeviceController (Device Controller)

Unified encapsulation of device control API.

**Key Features:**
- Maps abstract operations to GatewayState thresholds
- Parameter range validation
- Device status query

### 6. PreferenceManager (Preference Manager)

Records and applies user preferences.

**Key Features:**
- Stores preferences by scenario
- Automatically applies preferences to task plan
- Persists to MySQL

## Supported Devices

| Device ID | Name | Supported Actions |
|-----------|------|-------------------|
| Light_TH | Smart AC | turn_on, turn_off, set_temperature(16-30°C), set_humidity(30-90%) |
| Curtain_status | Smart Curtain | open, close, set_brightness(0-65535 lux) |
| Light_CU | Smart Light | set_brightness(0-65535) |
| Door_Security_Status | Smart Door Access | verify_card(automatic verification) |

## Supported Scenarios

| Scenario | Trigger Keywords | Suggested Actions |
|----------|------------------|-------------------|
| Sleep Mode | 困了、睡觉、休息、睡眠 | AC 24°C humidity 50%, close curtain, turn off lights |
| Movie Mode | 看电影、观影、电影、影院 | Close curtain, lights 10%, AC 23°C |
| Away Mode | 出门、离开、上班、外出 | Turn off AC, turn off lights, close curtain |
| Home Mode | 回家、到家、回来 | Turn on AC 25°C, open curtain |

## Dialogue Examples

```
User: "我困了,准备睡觉"
System:
  Reasoning: User wants to enter sleep state, needs to prepare sleep environment
  Tasks:
    1. Set AC temperature to 24°C
    2. Set AC humidity to 50%
    3. Close curtain
    4. Set light brightness to 0
  Result: Task execution successful

User: "把空调温度调低一点"
System:
  Reasoning: User feels current temperature is too high, needs to lower temperature
  Tasks:
    1. Set AC temperature to 22°C (apply user preference)
  Result: Task execution successful
```

## API Protocol

### Dialogue Request Format

Android App sends:

```json
{
  "state": "chat",
  "data": {
    "account": "user_id",
    "session_id": "uuid" // optional
  },
  "status": 1
}
```

### Dialogue Response Format

Gateway returns:

```json
{
  "type": "chat_response",
  "status": "success",
  "user_input": "我困了",
  "reasoning": "Reasoning process...",
  "tasks": [
    {"device": "Light_TH", "action": "set_temperature", "value": 24}
  ],
  "execution_result": {
    "success": true,
    "message": "Task execution completed",
    "details": [...]
  }
}
```

## Configuration File Description

### ai_agent_config.txt

```ini
[LLM]
API_KEY = your_api_key_here
BASE_URL = https://api.openai.com/v1
MODEL_NAME = gpt-4o-mini
TEMPERATURE = 0.7

[DIALOG]
MAX_CONTEXT_TURNS = 5
SESSION_TIMEOUT = 3600

[TASK_EXECUTOR]
ENABLE_ROLLBACK = True
MAX_RETRY = 3
TASK_TIMEOUT = 30
```

## Performance Metrics

- **Intent Parsing Latency**: 1-2 seconds (cloud API call)
- **Task Execution Latency**: < 100ms (local execution)
- **Dialogue Context Capacity**: Maximum 5 turns of dialogue
- **Concurrent Session Support**: Unlimited (memory permitting)

## Troubleshooting

### Issue 1: API Key Not Configured

**Symptoms**: Warning "AI Agent API Key not configured" at startup

**Solution**: Edit `ai_agent_config.txt`, set valid API Key

### Issue 2: Database Table Does Not Exist

**Symptoms**: Runtime error "Table 'user_test.conversation_history' doesn't exist"

**Solution**: Execute `ai_agent_tables.sql` to create table structure

### Issue 3: Device Capability File Does Not Exist

**Symptoms**: Startup error "Device capability configuration file does not exist"

**Solution**: Ensure `device_capabilities.json` exists in `Python/Gate/` directory

## Extension Development

### Adding New Device

Edit `device_capabilities.json`:

```json
{
  "devices": {
    "NewDevice": {
      "name": "New Device",
      "capabilities": ["Capability 1", "Capability 2"],
      "actions": {
        "action_name": {
          "description": "Action description",
          "operation": "operation_code",
          "params": {...}
        }
      }
    }
  }
}
```

### Adding New Scenario

Edit `device_capabilities.json`:

```json
{
  "scenarios": {
    "new_scenario": {
      "name": "New Scenario",
      "keywords": ["keyword1", "keyword2"],
      "suggested_actions": [
        {"device": "Light_TH", "action": "set_temperature", "value": 25}
      ]
    }
  }
}
```

## Technology Stack

- **Language**: Python 3.7+
- **LLM**: OpenAI GPT (gpt-4o-mini)
- **SDK**: openai
- **Database**: MySQL
- **Concurrency**: threading

## License

Consistent with project main license

## Contact

Project Address: EdgeIoT-SmartHomeGateway

---

**Note**: Using this system requires an OpenAI API Key. Please ensure compliance with OpenAI's terms of service and usage restrictions.
