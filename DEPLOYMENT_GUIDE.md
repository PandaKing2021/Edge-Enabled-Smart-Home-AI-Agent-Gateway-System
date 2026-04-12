# IoT 网关系统部署指南

本文档提供IoT网关系统的完整部署说明，包括Python网关、Android应用和设备单元的配置和部署。

## 📋 目录

- [系统架构](#系统架构)
- [环境准备](#环境准备)
- [Python网关部署](#python网关部署)
- [Android应用部署](#android应用部署)
- [设备单元部署](#设备单元部署)
- [系统测试](#系统测试)
- [常见问题](#常见问题)

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    IoT 网关系统架构                      │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │   Android    │
                    │     App      │
                    │  (9301端口)  │
                    └──────┬───────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Python 网关服务器                            │
│                                                         │
│  ┌─────────────────────────────────────────────────┐      │
│  │  • 设备通信模块 (端口9300)                     │      │
│  │  • Android通信模块 (端口9301)                   │      │
│  │  • 数据库服务器连接 (端口9302)                  │      │
│  │  • 智能决策逻辑                                │      │
│  │  • 阿里云IoT上传                                │      │
│  └─────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
        │               │               │
        ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  空调单元    │  │  窗帘单元    │  │  门禁单元    │
│ (A1_tem_hum) │  │ (A1_curtain) │  │ (A1_security) │
└─────────────┘  └─────────────┘  └─────────────┘
```

---

## 环境准备

### 1. 硬件要求

- **服务器**: 运行Python 3.8+的计算机或服务器
- **网络**: 所有设备在同一局域网内
- **设备单元**:
  - ESP8266开发板 × 3（空调、窗帘、门禁）
  - 传感器模块（DHT11温湿度、BH1750光照度、RFID读卡器）
  - 执行器模块（LED灯、舵机、继电器等）
  - OLED显示屏（可选，用于本地显示）

### 2. 软件要求

- **Python网关**:
  - Python 3.8+
  - MySQL 8.0+
  - 依赖包（见`Python/requirements.txt`）

- **Android应用**:
  - Android Studio
  - Android SDK API 21+
  - Android设备（手机/平板）API 21+

- **设备单元**:
  - Arduino IDE 1.8+
  - ESP8266开发板支持包
  - 所需的Arduino库（见下文）

### 3. Python依赖安装

```bash
cd Python
pip install -r requirements.txt
```

主要依赖：
```
paho-mqtt>=1.6.0
mysql-connector-python>=8.0.0
pyyaml>=5.4.0
```

---

## Python网关部署

### 1. 配置网关参数

编辑 `Python/Gate/GateConfig.txt`：

```
192.168.1.107          # 网关IP（本机IP）
192.168.1.107          # 数据库服务器IP（通常与网关同机）
9300                   # 设备单元通信端口
9301                   # Android应用通信端口
9302                   # 数据库服务器通信端口
root                   # MySQL用户名
1234                   # MySQL密码
gate_database          # 数据库名称
```

### 2. 配置用户信息

编辑 `Python/Gate/UserConfig.txt`（首次部署可留空）：

```
username
password
device_key
```

### 3. 初始化数据库

```bash
# 进入数据库服务器目录
cd "Database Server"

# 运行数据库初始化脚本
python database_process_server.py
```

### 4. 启动网关

```bash
cd Python/Gate
python gate.py
```

预期输出：
```
INFO - 网关配置加载成功: 网关IP=192.168.1.107, 设备端口=9300, Android端口=9301
INFO - 与数据库服务器连接成功: 192.168.1.107:9302
INFO - 设备节点通信端口已开启: 192.168.1.107:9300
INFO - 移动应用通信端口已开启: 192.168.1.107:9301
INFO - 线程 'sensor-listener' 已启动
INFO - 线程 'android-listener' 已启动
INFO - 线程 'aliyun-uploader' 已启动
INFO - 网关就绪
```

### 5. 验证网关运行

```bash
# 运行健康检查
cd Python/scripts
python health_check.py
```

---

## Android应用部署

### 1. 配置网关连接

编辑 `Android IoT APP/app/src/main/assets/config.properties`：

```
ip = 192.168.1.107    # Python网关IP
port = 9301           # Android通信端口（注意：是9301不是3001）
```

⚠️ **重要**: 确保端口为9301，与Python网关配置一致！

### 2. 构建APK

使用Android Studio：

1. 打开项目：`Android IoT APP`
2. 等待Gradle同步完成
3. Build → Generate Signed Bundle / APK
4. 选择APK，创建或选择签名密钥
5. 选择release构建

或使用命令行：

```bash
cd "Android IoT APP"
./gradlew assembleRelease
```

APK输出位置：`app/build/outputs/apk/release/app-release.apk`

### 3. 安装到设备

```bash
# 使用ADB安装
adb install app/build/outputs/apk/release/app-release.apk

# 或直接传输APK到手机安装
```

---

## 设备单元部署

### 1. 配置生成

**方式1：使用配置生成器（推荐）**

```bash
cd Python/scripts
python generate_device_config.py
```

这将自动生成各设备的配置文件。

**方式2：手动配置**

编辑 `Device Unit code/config_template.h`，然后重命名为 `config.h`：

```c
#define WIFI_SSID           "你的WiFi名称"
#define WIFI_PASSWORD       "你的WiFi密码"
#define GATEWAY_IP          "192.168.1.107"
#define GATEWAY_PORT        9300
#define DEVICE_ID           "A1_tem_hum"  // 根据设备类型修改
```

### 2. Arduino IDE配置

1. 安装ESP8266开发板支持：
   - File → Preferences → Additional Boards Manager URLs
   - 添加：`http://arduino.esp8266.com/stable/package_esp8266com_index.json`
   - Tools → Board → Boards Manager → 搜索"ESP8266" → 安装

2. 安装所需库：
   - `Adafruit_SSD1306`（OLED显示）
   - `Adafruit_GFX`（图形库）
   - `DHT_sensor_library`（温湿度传感器）
   - `BH1750`（光照度传感器）
   - `MFRC522`（RFID读卡器）
   - `ArduinoJson`（JSON处理）
   - `PubSubClient`（MQTT，阿里云使用）

3. 选择开发板：
   - Tools → Board → ESP8266 Boards → Generic ESP8266 Module

4. 配置上传参数：
   - Flash Size: 4MB (FS:2MB OTA:~1019KB)
   - CPU Frequency: 80 MHz
   - Upload Speed: 115200

### 3. 上传固件

**空调单元**：
```bash
# 打开 Arduino IDE
# File → Open → Device Unit code/esp8266_airconditioner_unit/esp8266_airconditioner_unit.ino
# 点击 Upload 按钮或按 Ctrl+U
```

**窗帘单元**：
```bash
# File → Open → Device Unit code/esp8266_curtain_unit/esp8266_curtain_unit.ino
# Upload
```

**门禁单元**：
```bash
# File → Open → Device Unit code/esp8266_doorsecurity_unit/esp8266_doorsecurity_unit.ino
# Upload
```

### 4. 验证设备连接

设备上传成功后，在Python网关控制台查看连接日志：

```
INFO - 设备节点连接: ('192.168.1.xxx', xxxxx)
INFO - 设备节点 'A1_tem_hum' 已连入网关
```

设备OLED应显示：
```
T: 25.0
H: 60.0
S: 10
```

---

## 系统测试

### 1. 单元测试

**Python网关测试**：
```bash
# 测试数据库连接
cd Python/Database Server
python -c "import database_process_server; print('OK')"

# 测试网关启动
cd Gate
python gate.py
```

**Android应用测试**：
1. 启动应用
2. 测试登录功能
3. 测试注册功能
4. 查看传感器数据展示

**设备单元测试**：
1. 观察OLED显示
2. 检查串口监视器（Tools → Serial Monitor，波特率115200）
3. 验证传感器数据上传

### 2. 集成测试

**测试数据流**：

1. **设备 → 网关 → Android**：
   - 在设备旁改变环境（温度、光照）
   - 观察Android应用数据更新

2. **Android → 网关 → 设备**：
   - 在Android应用调整阈值
   - 观察设备执行控制动作（LED、窗帘）

3. **数据库同步**：
   - 在MySQL中查询历史数据
   ```sql
   USE gate_database;
   SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 10;
   ```

### 3. 压力测试

```bash
# 持续运行测试脚本
python scripts/stress_test.py  # 如果有此脚本

# 监控网关资源
top  # Linux/Mac
taskmgr  # Windows
```

---

## 常见问题

### Q1: 设备单元无法连接网关

**症状**: ESP8266串口显示 "Connection failed"

**原因与解决**:
- WiFi密码错误 → 检查 `config.h`
- 网关IP错误 → 确认 `GATEWAY_IP`
- 端口错误 → 确认 `GATEWAY_PORT = 9300`
- 防火墙阻止 → 检查9300端口是否开放
- 网关未启动 → 检查 `gate.py` 是否运行

### Q2: Android应用无法连接网关

**症状**: 登录时提示 "连接失败"

**原因与解决**:
- 端口配置错误 → 确认 `config.properties` 中 `port = 9301`
- 网关IP错误 → 确认IP地址正确
- 网络不通 → 检查手机与网关在同一网络
- 网关未启动 → 检查网关日志

### Q3: 传感器数据不准确

**症状**: 温湿度/光照度数值异常

**原因与解决**:
- 传感器未校准 → 参考传感器文档校准
- 接线错误 → 检查I2C/Wire接线
- 电源不稳定 → 检查3.3V/5V电源

### Q4: 设备控制无响应

**症状**: Android发送指令后设备无动作

**原因与解决**:
- 阈值未触发 → 检查智能决策逻辑
- 设备ID错误 → 确认 `DEVICE_ID` 正确
- JSON格式错误 → 检查串口监视器输出

### Q5: 数据库连接失败

**症状**: 网关启动时 "与数据库服务器连接失败"

**原因与解决**:
- MySQL未启动 → 启动MySQL服务
- 密码错误 → 检查 `GateConfig.txt`
- 端口错误 → 确认MySQL端口为3306
- 防火墙阻止 → 开放9302端口

---

## 维护与监控

### 日志查看

**网关日志**：
```bash
# 实时查看
tail -f Python/Gate/gateway.log

# 查看错误
grep ERROR Python/Gate/gateway.log
```

**数据库日志**：
```bash
tail -f Python/Database Server/database.log
```

### 备份

**数据库备份**：
```bash
mysqldump -u root -p gate_database > backup_$(date +%Y%m%d).sql
```

**配置备份**：
```bash
tar -czf config_backup_$(date +%Y%m%d).tar.gz Python/Gate/*.txt
```

### 性能监控

```bash
# 查看网络连接
netstat -an | grep -E '9300|9301|9302'

# 查看进程资源
ps aux | grep python
```

---

## 附录

### A. 端口分配

| 服务 | 端口 | 用途 |
|------|------|------|
| 设备单元通信 | 9300 | ESP8266设备连接 |
| Android应用 | 9301 | 移动应用连接 |
| 数据库服务器 | 9302 | 数据库进程通信 |
| MySQL | 3306 | 数据库连接 |
| 阿里云MQTT | 1883 | 物联网云平台 |

### B. 设备ID映射

| 设备 | 设备ID | 功能 |
|------|--------|------|
| 智能空调 | A1_tem_hum | 温湿度监控 |
| 智能窗帘 | A1_curtain | 光照度监控、窗帘控制 |
| 智能门禁 | A1_security | 门禁控制 |

### C. 数据字段说明

| 字段名 | 说明 | 单位 |
|--------|------|------|
| Light_TH | 空调灯状态 | 0/1 |
| Temperature | 温度 | °C |
| Humidity | 湿度 | % |
| Light_CU | 室内灯状态 | 0/1 |
| Brightness | 光照度 | Lux |
| Curtain_status | 窗帘状态 | 0/1 |
| Door_Security_Status | 门禁状态 | 0/1 |

---

## 技术支持

遇到问题？

1. 运行健康检查：`python scripts/health_check.py`
2. 查看日志文件
3. 检查常见问题章节
4. 联系技术支持

---

**文档版本**: 1.0
**最后更新**: 2024年
**维护者**: IoT开发团队
