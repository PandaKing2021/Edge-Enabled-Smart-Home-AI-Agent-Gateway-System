<div align="center">

# EdgeHomeAI
### Smart Home AI Agent Task Orchestration System Based on Edge Computing

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.7+-green.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](https://github.com)
[![GLM](https://img.shields.io/badge/AI-GLM--4.7-Flash-orange.svg)](https://open.bigmodel.cn/)

</div>

---

## 📋 Project Overview

**EdgeHomeAI** is a smart home gateway system based on edge computing, integrating AI Agent conversational task orchestration capabilities. The system adopts an edge-cloud collaborative architecture, implementing unified device management, intelligent decision-making, and natural language interaction on the home edge gateway, effectively addressing issues of latency, privacy, and insufficient intelligence in traditional smart home systems.

### Core Advantages

- 🧠 **Edge Intelligence**: AI inference runs locally on home gateway, reducing cloud dependency
- 🚀 **Low Latency**: End-to-end response time < 10 seconds, meeting real-time control requirements
- 🔒 **Privacy Protection**: Sensitive data processed locally, reducing data uploads by 68.8%
- 🤖 **Natural Interaction**: Conversational task orchestration based on GLM-4.7-Flash
- 🏠 **Multi-Device Support**: Unified management of smart devices including AC, curtains, door access, etc.
- 📱 **Mobile Control**: Android application enables remote monitoring and control

---

## 🌟 Core Features

### Smart Control
- **AI Agent Task Orchestration**: Natural language understanding and task decomposition
- **Intelligent Decision Engine**: Automated control based on sensor data
- **Scenario Linkage**: Multi-device collaborative operation modes
- **User Preference Learning**: Personalized habit adaptation

### Device Management
- **Unified Gateway**: Python server centrally manages all IoT devices
- **Multi-Device Support**: Various device types including AC, curtains, door access, etc.
- **Device Simulator**: Complete device simulation test environment
- **Real-time Monitoring**: Real-time device status reporting and display

### System Architecture
- **Edge Computing**: Local inference and data processing
- **Microservice Design**: Modular architecture, easy to extend
- **Multi-threaded Concurrency**: Supports multiple device concurrent connections
- **Health Check**: Automated tools verify system status

### Data Management
- **Data Persistence**: MySQL database stores historical data
- **Cloud Integration**: Supports Aliyun IoT platform data upload
- **Data Preprocessing**: Real-time data cleaning and analysis
- **User Authentication**: Secure identity verification and device authorization

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   EdgeHomeAI System Architecture            │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │  Android     │
                    │   Mobile App │ (Port 9301)
                    └──────┬───────┘
                           │ TCP
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Python Edge Gateway Server                     │
│  ┌────────────────────────────────────────────────────┐     │
│  │  • Device Communication Module (Port 9300)         │     │
│  │  • Android Communication Module (Port 9301)        │     │
│  │  • Database Server Connection (Port 9302)          │     │
│  │  • AI Agent Dialog Orchestration Engine            │     │
│  │  • Intelligent Decision Engine                     │     │
│  │  • Aliyun IoT Upload Module                        │     │
│  │  • Data Preprocessing and Analysis                 │     │
│  │  • User Behavior Prediction and Pre-control        │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
        │               │               │
        ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  AC Unit    │  │ Curtain Unit│  │Door Access  │
│ (A1_tem_hum)│  │(A1_curtain) │  │(A1_security)│
│   ESP8266   │  │   ESP8266   │  │   ESP8266   │
└─────────────┘  └─────────────┘  └─────────────┘
   Sensor         Sensor         Sensor
   DHT11         BH1750         MFRC522
```

### AI Agent Module Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent Architecture                    │
└─────────────────────────────────────────────────────────────┘

    User Input (Natural Language)
           │
           ▼
┌──────────────────┐
│  Intent Planner  │ ← Intent Recognition and Task Planning
│  (GLM-4.7-Flash) │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Capability       │ ← Device Capability Retrieval
│ Retriever        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Task Executor   │ ← Task Execution and Device Control
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Dialog Manager  │ ← Dialog Management and Context Maintenance
└──────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.7 or higher
- **MySQL**: 5.7 or higher
- **Arduino IDE**: For device firmware upload
- **Android Studio**: For application building (optional)

### Installation Steps

#### 1. Get the Project

```bash
git clone https://github.com/yourusername/EdgeHomeAI.git
cd EdgeHomeAI
```

#### 2. Install Python Dependencies

```bash
cd Python
pip install -r requirements.txt
```

#### 3. Configure Gateway

Edit `Python/Gate/GateConfig.txt` configuration file:

```
192.168.1.107      # Gateway IP address
192.168.1.107      # Database server IP
9300               # Device communication port
9301               # Android communication port
9302               # Database server port
root               # Database username
your_password      # Database password
gate_database      # Database name
```

Edit `Python/Gate/UserConfig.txt` to configure user information:

```
username          # Username
password          # Password
device_id         # Device ID
```

#### 4. Initialize Database

```bash
# 创建数据库和表结构
mysql -u root -p < "Python/Database Server/init_database.sql"

# 创建 AI Agent 相关表（可选）
mysql -u root -p < "Python/Database Server/ai_agent_tables.sql"
```

#### 5. Start Database Server

```bash
cd "Python/Database Server"
python database_process_server.py
```

#### 6. Start Gateway

**Production Mode** (requires database server):

```bash
cd Python/Gate
python gate.py
```

**Test Mode** (no database, suitable for development and testing):

```bash
cd Python/Gate
python gate_test.py --test
```

#### 7. Upload Device Firmware

Use Arduino IDE to upload firmware for each device:

- `Device Unit code/esp8266_airconditioner_unit/` - AC unit
- `Device Unit code/esp8266_curtain_unit/` - Curtain unit
- `Device Unit code/esp8266_doorsecurity_unit/` - Door access unit

#### 8. Install Android App (Optional)

```bash
cd "Android IoT APP"
./gradlew assembleDebug
# Install the generated APK to Android device
```

### Health Check

Run health check to ensure system configuration is correct:

```bash
cd Python/scripts
python health_check.py
```

Expected output: `✓ All checks passed! System configuration is good.`

---

## 📁 Project Structure

```
EdgeHomeAI/
├── Python/                              # Python Gateway Server
│   ├── Gate/                            # Gateway Main Program
│   │   ├── gate.py                     # Production mode main entry
│   │   ├── gate_test.py                # Test mode main entry
│   │   ├── GateConfig.txt              # Gateway configuration file
│   │   ├── UserConfig.txt              # User configuration file
│   │   ├── ai_agent_config.txt         # AI Agent configuration
│   │   ├── device_capabilities.json    # Device capability description
│   │   ├── android_handler.py          # Android communication handler
│   │   ├── sensor_handler.py           # Sensor data processing
│   │   ├── database.py                 # Local database operations
│   │   ├── aliyun_handler.py           # Aliyun IoT integration
│   │   └── ai_agent/                   # AI Agent module
│   │       ├── intent_planner.py       # Intent recognition and task planning
│   │       ├── capability_retriever.py # Device capability retrieval
│   │       ├── task_executor.py        # Task execution
│   │       ├── dialog_manager.py       # Dialogue management
│   │       ├── preference_manager.py   # User preference management
│   │       └── device_controller.py    # Device controller
│   ├── Database Server/                 # Database Server
│   │   ├── database_process_server.py  # Database server process
│   │   ├── init_database.sql           # Initialization script
│   │   ├── ai_agent_tables.sql         # AI Agent table structure
│   │   └── serverConfig.txt            # Server configuration
│   └── common/                          # Common modules
│       ├── config.py                   # Configuration management
│       ├── constants.py                # Constants definition
│       ├── models.py                   # Data models
│       ├── protocol.py                 # Communication protocol
│       └── log_setup.py                # Logging configuration
│                          
│
├── Android IoT APP/                     # Android Mobile Application
│   └── app/src/main/
│       ├── assets/config.properties    # Application configuration
│       └── java/                       # Java source code
│
├── Device Unit code/                    # Device Unit Firmware
│   ├── config_template.h               # Configuration template
│   ├── esp8266_airconditioner_unit/    # AC unit firmware
│   ├── esp8266_curtain_unit/          # Curtain unit firmware
│   └── esp8266_doorsecurity_unit/     # Door security unit firmware
│
│
├── README.md                            # Project documentation (this file)
├── AI_AGENT_README.md                   # AI Agent Usage Guide
├── DEPLOYMENT_GUIDE.md                  # Deployment Guide
├── DEVELOPER_GUIDE.md                   # Developer Documentation
└── LICENSE                              # MIT Open Source License
```

---

## ⚙️ Configuration Instructions

### Port Allocation

| Port | Service           | Description                     |
|------|------------------|--------------------------------|
| 9300  | Device Unit       | ESP8266 device connection port    |
| 9301  | Android App       | Mobile application connection port |
| 9302  | Database Server   | Database process communication port |
| 3306  | MySQL            | Database connection port          |

### Device Description

| Device Name | Device ID    | Main Function                     | Sensor/Module |
|-------------|--------------|----------------------------------|-------------|
| Smart AC     | A1_tem_hum   | Temperature/humidity monitoring, AC control | DHT11       |
| Smart Curtain| A1_curtain   | Light intensity monitoring, curtain control | BH1750      |
| Smart Door Access | A1_security | Door access control, RFID card verification | MFRC522     |

### AI Agent Configuration

Edit `Python/Gate/ai_agent_config.txt`:

```ini
[LLM]
API_KEY = your_api_key
BASE_URL = https://open.bigmodel.cn/api/paas/v4
MODEL_NAME = GLM-4.7-Flash
TEMPERATURE = 0.7
MAX_TOKENS = 2048
STREAM = False

[DIALOG]
MAX_CONTEXT_TURNS = 5
SESSION_TIMEOUT = 3600

[RAG]
CAPABILITIES_FILE = device_capabilities.json
```

---

## 🛠️ Technology Stack

### Backend Technology
- **Python 3.7+**: Gateway server core
- **MySQL 5.7+**: Data persistence
- **Socket**: TCP network communication
- **Threading**: Multi-threaded concurrent processing
- **ZhipuAI GLM-4.7-Flash**: Large Language Model API

### Frontend Technology
- **Android (Java)**: Mobile application development
- **Material Design**: UI design specification

### Embedded Technology
- **ESP8266**: WiFi module and microcontroller
- **Arduino**: Firmware development framework
- **DHT11**: Temperature and humidity sensor
- **BH1750**: Light intensity sensor
- **MFRC522**: RFID card reader

### Cloud Services
- **Aliyun IoT**: Cloud platform integration
- **Zhipu AI**: LLM API service

---

## 📊 Performance Metrics

### AI Agent Performance

| Metric Dimension | Performance Indicator     | Target  | Actual  | Status |
|----------------|----------------------|----------|----------|-------|
| Intelligence & Function | Intent recognition accuracy | ≥ 95% | 100%     | ✅    |
|                | Task execution accuracy       | ≥ 90%    | 98.6%    | ✅    |
| Real-time Performance | End-to-end latency           | < 10s   | 9.2s     | ✅    |
|                | P95 latency                  | < 12s    | 9.7s     | ✅    |
| Resource & Energy     | Memory usage             | < 150MB  | 112.5MB  | ✅    |
|                | CPU usage              | < 40%   | 32.5%    | ✅    |
| AI Model Performance    | LLM inference time         | < 10s    | 8.7s     | ✅    |
|                | Token efficiency           | < 25ms   | 22.1ms   | ✅    |
| User Experience       | SUS score             | ≥ 80   | 85.5     | ✅    |
| System Robustness     | Long-term uptime success rate | ≥ 95% | 98.3%    | ✅    |
| Privacy & Security     | Data upload reduction rate       | ≥ 50%    | 68.8%    | ✅    |

### System Performance

- **Concurrent Connections**: Supports 10+ device concurrency
- **Data Processing**: Real-time sensor data processing latency < 100ms
- **System Stability**: 24-hour continuous operation without exceptions

---

## 📖 Documentation

### Core Documentation
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Detailed deployment steps and environment configuration
- **[Developer Guide](DEVELOPER_GUIDE.md)** - System architecture, API reference, and development guide
- **[AI Agent Usage Guide](AI_AGENT_README.md)** - AI Agent conversational task orchestration system usage instructions

### Test Documentation
- **[AI Agent Test Guide](Python/scripts/AI_AGENT_TEST_GUIDE.md)** - Complete test suite and test methods
- **[Quick Test Guide](Python/scripts/QUICK_TEST_GUIDE.md)** - Quick test script usage instructions

### Archived Documentation
All experiment and test related documents have been archived to `meteral/script/` directory.

---

## 🧪 Testing

### Run Tests

```bash
# Health check
python Python/scripts/health_check.py

# Database server test
python Python/scripts/test_database_server.py

# AI Agent unit test
python Python/scripts/ai_agent_test.py

# End-to-end test
python Python/scripts/test_ai_agent_e2e.py

# Integration test
python Python/scripts/integration_test.py

# Complete test suite
python Python/scripts/run_all_tests.py

# Device simulator
python Python/scripts/simulator_device.py

# Android simulator
python Python/scripts/simulator_android.py
```

### Test Coverage

- ✅ Unit Tests - Core module functionality verification
- ✅ Integration Tests - Multi-module collaboration verification
- ✅ End-to-end Tests - Complete business process verification
- ✅ Performance Tests - System performance benchmark testing
- ✅ Robustness Tests - Exception scenario handling verification

---

## 🤝 Contributing Guide

We welcome all forms of contributions!

### How to Contribute

1. Fork this repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### Contribution Guidelines

- Follow existing code style
- Update relevant documentation
- Add necessary tests
- Ensure all tests pass
- Provide clear and explicit commit messages

---

## 🐛 Troubleshooting

### Common Issues

**Q: Device cannot connect to gateway?**

- Check if WiFi configuration is correct
- Confirm gateway IP address configuration
- Run health check tool for diagnosis
- Check gateway log output

**Q: Android app connection failed?**

- Confirm port configuration is 9301
- Check gateway IP address
- Verify network connection
- Check firewall settings

**Q: Database connection error?**

- Confirm MySQL service has started
- Check database configuration information
- Run database server test script
- Verify username and password

**Q: AI Agent response slow?**

- Check network connection (API calls require network)
- Verify if API Key is correct
- Check LLM API service status
- Consider adjusting MAX_TOKENS parameter

For more issues, please refer to the troubleshooting section in [Deployment Guide](DEPLOYMENT_GUIDE.md).

---

## 📄 License

This project is open-sourced under the [MIT License](LICENSE).

```
MIT License

Copyright (c) 2024-2026 EdgeHomeAI Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 👥 Authors and Contributors

### Project Creator
- **PandaKing** - Initial architecture design and core development

### Core Contributors
- Check GitHub contributor list

Thank you to everyone who has contributed to this project!

---

## 📞 Contact Information

- **Issue Feedback**: Please send email to pandaking_shanghai@outlook.com
- **Feature Suggestions**: Welcome to submit Feature Request
- **Bug Reports**: Please submit Issue with detailed information

---

## 🙏 Acknowledgments

Thanks to the following open source projects and technical support:

- [Python](https://www.python.org/) - Programming language
- [Arduino](https://www.arduino.cc/) - Embedded development platform
- [Android](https://www.android.com/) - Mobile operating system
- [ESP8266](https://www.espressif.com/) - WiFi module
- [Aliyun IoT](https://www.aliyun.com/product/iot) - Cloud platform
- [Zhipu AI](https://open.bigmodel.cn/) - LLM API service

---

## 🌟 Star History

If this project is helpful to you, please give a ⭐️ Star!

---

<div align="center">

**Made with ❤️ by PandaKing**

**System Status**: ✅ Production Ready

**Last Update**: 2026-04-12

</div
