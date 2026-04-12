<div align="center">

# EdgeHomeAI
### 基于边缘计算的智能家居 AI Agent 任务编排系统

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.7+-green.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](https://github.com)
[![GLM](https://img.shields.io/badge/AI-GLM--4.7-Flash-orange.svg)](https://open.bigmodel.cn/)

</div>

---

## 📋 项目概述

**EdgeHomeAI** 是一个基于边缘计算的智能家居网关系统，集成 AI Agent 对话式任务编排能力。系统采用端边协同架构，在家庭边缘网关上实现设备统一管理、智能决策和自然语言交互，有效解决了传统智能家居系统中的延迟、隐私和智能化不足等问题。

### 核心优势

- 🧠 **边缘智能**: 在家庭网关本地运行 AI 推理，降低云端依赖
- 🚀 **低延迟**: 端到端响应时间 < 10 秒，满足实时控制需求
- 🔒 **隐私保护**: 敏感数据本地处理，上传减少 68.8%
- 🤖 **自然交互**: 基于 GLM-4.7-Flash 的对话式任务编排
- 🏠 **多设备支持**: 统一管理空调、窗帘、门禁等智能设备
- 📱 **移动控制**: Android 应用实现远程监控和控制

---

## 🌟 核心特性

### 智能控制
- **AI Agent 任务编排**: 自然语言理解与任务分解
- **智能决策引擎**: 基于传感器数据的自动化控制
- **场景联动**: 多设备协同工作模式
- **用户偏好学习**: 个性化习惯适配

### 设备管理
- **统一网关**: Python 服务器集中管理所有 IoT 设备
- **多设备支持**: 空调、窗帘、门禁等多种设备类型
- **设备模拟器**: 完整的设备仿真测试环境
- **实时监控**: 设备状态实时上报和展示

### 系统架构
- **边缘计算**: 本地推理与数据处理
- **微服务设计**: 模块化架构，易于扩展
- **多线程并发**: 支持多设备并发连接
- **健康检查**: 自动化工具验证系统状态

### 数据管理
- **数据持久化**: MySQL 数据库存储历史数据
- **云端集成**: 支持阿里云 IoT 平台数据上传
- **数据预处理**: 实时数据清洗与分析
- **用户认证**: 安全的身份验证和设备授权

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     EdgeHomeAI 系统架构                        │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │  Android     │
                    │   Mobile App │ (端口 9301)
                    └──────┬───────┘
                           │ TCP
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Python 边缘网关服务器                       │
│  ┌────────────────────────────────────────────────────┐    │
│  │  • 设备通信模块 (端口 9300)                        │    │
│  │  • Android 通信模块 (端口 9301)                     │    │
│  │  • 数据库服务器连接 (端口 9302)                    │    │
│  │  • AI Agent 对话编排引擎                            │    │
│  │  • 智能决策引擎                                    │    │
│  │  • 阿里云 IoT 上传模块                              │    │
│  │  • 数据预处理与分析                                 │    │
│  │  • 用户行为预测与预控制系统                         │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
        │               │               │
        ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  空调单元    │  │  窗帘单元    │  │  门禁单元    │
│ (A1_tem_hum) │  │ (A1_curtain) │  │ (A1_security)│
│   ESP8266    │  │   ESP8266    │  │   ESP8266    │
└─────────────┘  └─────────────┘  └─────────────┘
     传感器          传感器          传感器
    DHT11          BH1750          MFRC522
```

### AI Agent 模块架构

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent 架构                             │
└─────────────────────────────────────────────────────────────┘

    用户输入 (自然语言)
           │
           ▼
┌──────────────────┐
│  Intent Planner   │ ← 意图识别与任务规划
│  (GLM-4.7-Flash) │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Capability       │ ← 设备能力检索
│ Retriever        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Task Executor   │ ← 任务执行与设备控制
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Dialog Manager  │ ← 对话管理与上下文维护
└──────────────────┘
```

---

## 🚀 快速开始

### 前置要求

- **Python**: 3.7 或更高版本
- **MySQL**: 5.7 或更高版本
- **Arduino IDE**: 用于设备固件上传
- **Android Studio**: 用于应用构建（可选）

### 安装步骤

#### 1. 获取项目

```bash
git clone https://github.com/yourusername/EdgeHomeAI.git
cd EdgeHomeAI
```

#### 2. 安装 Python 依赖

```bash
cd Python
pip install -r requirements.txt
```

#### 3. 配置网关

编辑 `Python/Gate/GateConfig.txt` 配置文件：

```
192.168.1.107      # 网关 IP 地址
192.168.1.107      # 数据库服务器 IP
9300               # 设备通信端口
9301               # Android 通信端口
9302               # 数据库服务器端口
root               # 数据库用户名
your_password      # 数据库密码
gate_database      # 数据库名称
```

编辑 `Python/Gate/UserConfig.txt` 配置用户信息：

```
username          # 用户名
password          # 密码
device_id         # 设备 ID
```

#### 4. 初始化数据库

```bash
# 创建数据库和表结构
mysql -u root -p < "Python/Database Server/init_database.sql"

# 创建 AI Agent 相关表（可选）
mysql -u root -p < "Python/Database Server/ai_agent_tables.sql"
```

#### 5. 启动数据库服务器

```bash
cd "Python/Database Server"
python database_process_server.py
```

#### 6. 启动网关

**生产模式**（需要数据库服务器）：

```bash
cd Python/Gate
python gate.py
```

**测试模式**（无需数据库，适合开发和测试）：

```bash
cd Python/Gate
python gate_test.py --test
```

#### 7. 上传设备固件

使用 Arduino IDE 上传各设备的固件：

- `Device Unit code/esp8266_airconditioner_unit/` - 空调单元
- `Device Unit code/esp8266_curtain_unit/` - 窗帘单元
- `Device Unit code/esp8266_doorsecurity_unit/` - 门禁单元

#### 8. 安装 Android 应用（可选）

```bash
cd "Android IoT APP"
./gradlew assembleDebug
# 将生成的 APK 安装到 Android 设备
```

### 健康检查

运行健康检查确保系统配置正确：

```bash
cd Python/scripts
python health_check.py
```

预期输出：`✓ 所有检查通过！系统配置良好。`

---

## 📁 项目结构

```
EdgeHomeAI/
├── Python/                              # Python 网关服务器
│   ├── Gate/                            # 网关主程序
│   │   ├── gate.py                     # 生产模式主入口
│   │   ├── gate_test.py                # 测试模式主入口
│   │   ├── GateConfig.txt              # 网关配置文件
│   │   ├── UserConfig.txt              # 用户配置文件
│   │   ├── ai_agent_config.txt         # AI Agent 配置
│   │   ├── device_capabilities.json    # 设备能力描述
│   │   ├── android_handler.py          # Android 通信处理
│   │   ├── sensor_handler.py           # 传感器数据处理
│   │   ├── database.py                 # 本地数据库操作
│   │   ├── aliyun_handler.py           # 阿里云 IoT 集成
│   │   └── ai_agent/                   # AI Agent 模块
│   │       ├── intent_planner.py       # 意图识别与任务规划
│   │       ├── capability_retriever.py # 设备能力检索
│   │       ├── task_executor.py        # 任务执行
│   │       ├── dialog_manager.py       # 对话管理
│   │       ├── preference_manager.py   # 用户偏好管理
│   │       └── device_controller.py    # 设备控制器
│   ├── Database Server/                 # 数据库服务器
│   │   ├── database_process_server.py  # 数据库服务进程
│   │   ├── init_database.sql           # 初始化脚本
│   │   ├── ai_agent_tables.sql         # AI Agent 表结构
│   │   └── serverConfig.txt            # 服务器配置
│   ├── common/                          # 公共模块
│   │   ├── config.py                   # 配置管理
│   │   ├── constants.py                # 常量定义
│   │   ├── models.py                   # 数据模型
│   │   ├── protocol.py                 # 通信协议
│   │   └── log_setup.py                # 日志配置
│   └── scripts/                         # 工具脚本
│       ├── generate_device_config.py   # 生成设备配置
│       ├── health_check.py             # 健康检查
│       ├── test_database_server.py     # 数据库服务器测试
│       ├── simulator_device.py         # 设备模拟器
│       ├── simulator_android.py       # Android 模拟器
│       ├── ai_agent_test.py            # AI Agent 单元测试
│       ├── test_ai_agent_e2e.py        # 端到端测试
│       ├── integration_test.py         # 集成测试
│       ├── manual_test.py              # 手动测试
│       ├── quick_test.py               # 快速测试
│       ├── run_all_tests.py            # 完整测试套件
│       └── run_integration_test.py     # 集成测试运行器
│
├── Android IoT APP/                     # Android 移动应用
│   └── app/src/main/
│       ├── assets/config.properties    # 应用配置
│       └── java/                       # Java 源代码
│
├── Device Unit code/                    # 设备单元固件
│   ├── config_template.h               # 配置模板
│   ├── esp8266_airconditioner_unit/    # 空调单元固件
│   ├── esp8266_curtain_unit/          # 窗帘单元固件
│   └── esp8266_doorsecurity_unit/     # 门禁单元固件
│
├── meteral/                             # 项目资源文档
│   ├── 实验指标                         # 实验评估指标
│   ├── 系统扩展设计.txt                 # 系统扩展设计
│   ├── GLM使用方法.txt                   # GLM API 使用方法
│   └── script/                          # 历史测试和实验文档
│
├── README.md                            # 项目文档（本文件）
├── AI_AGENT_README.md                   # AI Agent 使用指南
├── DEPLOYMENT_GUIDE.md                  # 部署指南
├── DEVELOPER_GUIDE.md                   # 开发者文档
└── LICENSE                              # MIT 开源许可证
```

---

## ⚙️ 配置说明

### 端口分配

| 端口  | 服务           | 说明                     |
|-------|----------------|--------------------------|
| 9300  | 设备单元       | ESP8266 设备连接端口    |
| 9301  | Android 应用   | 移动应用连接端口        |
| 9302  | 数据库服务器   | 数据库进程通信端口      |
| 3306  | MySQL          | 数据库连接端口          |

### 设备说明

| 设备名称   | 设备 ID      | 主要功能                     | 传感器/模块 |
|------------|--------------|------------------------------|-------------|
| 智能空调   | A1_tem_hum   | 温湿度监控、空调控制         | DHT11       |
| 智能窗帘   | A1_curtain   | 光照度监控、窗帘控制         | BH1750      |
| 智能门禁   | A1_security  | 门禁控制、RFID 卡片验证      | MFRC522     |

### AI Agent 配置

编辑 `Python/Gate/ai_agent_config.txt`：

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

## 🛠️ 技术栈

### 后端技术
- **Python 3.7+**: 网关服务器核心
- **MySQL 5.7+**: 数据持久化
- **Socket**: TCP 网络通信
- **Threading**: 多线程并发处理
- **ZhipuAI GLM-4.7-Flash**: 大语言模型 API

### 前端技术
- **Android (Java)**: 移动应用开发
- **Material Design**: UI 设计规范

### 嵌入式技术
- **ESP8266**: WiFi 模块与微控制器
- **Arduino**: 固件开发框架
- **DHT11**: 温湿度传感器
- **BH1750**: 光照度传感器
- **MFRC522**: RFID 读卡器

### 云服务
- **阿里云 IoT**: 云平台集成
- **智谱 AI**: LLM API 服务

---

## 📊 性能指标

### AI Agent 性能

| 指标维度       | 性能指标             | 目标值   | 实际值   | 状态  |
|----------------|----------------------|----------|----------|-------|
| 智能与功能     | 意图识别准确率       | ≥ 95%    | 100%     | ✅    |
|                | 任务执行准确率       | ≥ 90%    | 98.6%    | ✅    |
| 实时性能       | 端到端延迟           | < 10s    | 9.2s     | ✅    |
|                | P95 延迟             | < 12s    | 9.7s     | ✅    |
| 资源与能效     | 内存占用             | < 150MB  | 112.5MB  | ✅    |
|                | CPU 占用率           | < 40%    | 32.5%    | ✅    |
| AI 模型性能    | LLM 推理时间         | < 10s    | 8.7s     | ✅    |
|                | Token 效率           | < 25ms   | 22.1ms   | ✅    |
| 用户体验       | SUS 评分             | ≥ 80     | 85.5     | ✅    |
| 系统健壮性     | 长时间运行成功率     | ≥ 95%    | 98.3%    | ✅    |
| 隐私与安全     | 数据上传减少率       | ≥ 50%    | 68.8%    | ✅    |

### 系统性能

- **并发连接**: 支持 10+ 设备并发
- **数据处理**: 实时传感器数据处理延迟 < 100ms
- **系统稳定性**: 24 小时连续运行无异常

---

## 📖 文档

### 核心文档
- **[部署指南](DEPLOYMENT_GUIDE.md)** - 详细的部署步骤和环境配置
- **[开发者指南](DEVELOPER_GUIDE.md)** - 系统架构、API 参考和开发指南
- **[AI Agent 使用指南](AI_AGENT_README.md)** - AI Agent 对话式任务编排系统使用说明

### 测试文档
- **[AI Agent 测试指南](Python/scripts/AI_AGENT_TEST_GUIDE.md)** - 完整的测试套件和测试方法
- **[快速测试指南](Python/scripts/QUICK_TEST_GUIDE.md)** - 快速测试脚本使用说明

### 历史文档（已归档）
所有实验和测试相关文档已归档至 `meteral/script/` 目录。

---

## 🧪 测试

### 运行测试

```bash
# 健康检查
python Python/scripts/health_check.py

# 数据库服务器测试
python Python/scripts/test_database_server.py

# AI Agent 单元测试
python Python/scripts/ai_agent_test.py

# 端到端测试
python Python/scripts/test_ai_agent_e2e.py

# 集成测试
python Python/scripts/integration_test.py

# 完整测试套件
python Python/scripts/run_all_tests.py

# 设备模拟器
python Python/scripts/simulator_device.py

# Android 模拟器
python Python/scripts/simulator_android.py
```

### 测试覆盖

- ✅ 单元测试 - 核心模块功能验证
- ✅ 集成测试 - 多模块协作验证
- ✅ 端到端测试 - 完整业务流程验证
- ✅ 性能测试 - 系统性能基准测试
- ✅ 健壮性测试 - 异常场景处理验证

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 贡献规范

- 遵循现有的代码风格
- 更新相关文档
- 添加必要的测试
- 确保所有测试通过
- 提交信息清晰明确

---

## 🐛 故障排查

### 常见问题

**Q: 设备无法连接网关？**

- 检查 WiFi 配置是否正确
- 确认网关 IP 地址配置
- 运行健康检查工具诊断
- 查看网关日志输出

**Q: Android 应用连接失败？**

- 确认端口配置为 9301
- 检查网关 IP 地址
- 验证网络连接
- 检查防火墙设置

**Q: 数据库连接错误？**

- 确认 MySQL 服务已启动
- 检查数据库配置信息
- 运行数据库服务器测试脚本
- 验证用户名和密码

**Q: AI Agent 响应慢？**

- 检查网络连接（API 调用需要网络）
- 验证 API Key 是否正确
- 查看 LLM API 服务状态
- 考虑调整 MAX_TOKENS 参数

更多问题请参考 [部署指南](DEPLOYMENT_GUIDE.md) 的故障排查章节。

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

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

## 👥 作者与贡献者

### 项目创建者
- **EdgeHomeAI Team** - 初始架构设计与核心开发

### 核心贡献者
- 查看 GitHub 贡献列表

感谢所有为这个项目做出贡献的人！

---

## 📞 联系方式

- **问题反馈**: 请发送邮件至 pandaking_shanghai@outlook.com
- **功能建议**: 欢迎提交 Feature Request
- **Bug 报告**: 请提交 Issue 并附上详细信息

---

## 🙏 致谢

感谢以下开源项目和技术支持：

- [Python](https://www.python.org/) - 编程语言
- [Arduino](https://www.arduino.cc/) - 嵌入式开发平台
- [Android](https://www.android.com/) - 移动操作系统
- [ESP8266](https://www.espressif.com/) - WiFi 模块
- [阿里云 IoT](https://www.aliyun.com/product/iot) - 云平台
- [智谱 AI](https://open.bigmodel.cn/) - LLM API 服务

---

## 🌟 Star History

如果这个项目对您有帮助，请给一个 ⭐️ Star！

---

<div align="center">

**Made with ❤️ by EdgeHomeAI Team**

**系统状态**: ✅ 生产就绪

**最后更新**: 2026-04-12

</div>
