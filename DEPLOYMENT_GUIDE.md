# IoT Gateway System Deployment Guide

This document provides complete deployment instructions for the IoT gateway system, including configuration and deployment of the Python gateway, Android application, and device units.

## 📋 Table of Contents

- [System Architecture](#system-architecture)
- [Environment Preparation](#environment-preparation)
- [Python Gateway Deployment](#python-gateway-deployment)
- [Android Application Deployment](#android-application-deployment)
- [Device Unit Deployment](#device-unit-deployment)
- [System Testing](#system-testing)
- [Common Issues](#common-issues)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 IoT Gateway System Architecture              │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │   Android    │
                    │     App      │
                    │ (Port 9301)  │
                    └──────┬───────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Python Gateway Server                      │
│                                                         │
│  ┌─────────────────────────────────────────────────┐      │
│  │  • Device Communication Module (Port 9300)      │      │
│  │  • Android Communication Module (Port 9301)    │      │
│  │  • Database Server Connection (Port 9302)      │      │
│  │  • Intelligent Decision Logic                  │      │
│  │  • Aliyun IoT Upload                           │      │
│  └─────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
        │               │               │
        ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ AC Unit     │  │ Curtain     │  │ Door Access │
│ (A1_tem_hum)│  │ (A1_curtain)│  │ (A1_security)│
└─────────────┘  └─────────────┘  └─────────────┘
```

---

## Environment Preparation

### 1. Hardware Requirements

- **Server**: Computer or server running Python 3.8+
- **Network**: All devices on the same local area network
- **Device Units**:
  - ESP8266 development boards × 3 (air conditioner, curtain, door access)
  - Sensor modules (DHT11 temperature/humidity, BH1750 light intensity, RFID reader)
  - Actuator modules (LED lights, servos, relays, etc.)
  - OLED display (optional, for local display)

### 2. Software Requirements

- **Python Gateway**:
  - Python 3.8+
  - MySQL 8.0+
  - Dependencies (see `Python/requirements.txt`)

- **Android Application**:
  - Android Studio
  - Android SDK API 21+
  - Android device (phone/tablet) API 21+

- **Device Units**:
  - Arduino IDE 1.8+
  - ESP8266 board support package
  - Required Arduino libraries (see below)

### 3. Python Dependencies Installation

```bash
cd Python
pip install -r requirements.txt
```

Main dependencies:
```
paho-mqtt>=1.6.0
mysql-connector-python>=8.0.0
pyyaml>=5.4.0
```

---

## Python Gateway Deployment

### 1. Configure Gateway Parameters

Edit `Python/Gate/GateConfig.txt`:

```
192.168.1.107          # Gateway IP (local machine IP)
192.168.1.107          # Database server IP (usually same as gateway)
9300                   # Device unit communication port
9301                   # Android application communication port
9302                   # Database server communication port
root                   # MySQL username
1234                   # MySQL password
gate_database          # Database name
```

### 2. Configure User Information

Edit `Python/Gate/UserConfig.txt` (can be left blank for first deployment):

```
username
password
device_key
```

### 3. Initialize Database

```bash
# Enter database server directory
cd "Database Server"

# Run database initialization script
python database_process_server.py
```

### 4. Start Gateway

```bash
cd Python/Gate
python gate.py
```

Expected output:
```
INFO - Gateway configuration loaded successfully: Gateway IP=192.168.1.107, Device Port=9300, Android Port=9301
INFO - Connected to database server: 192.168.1.107:9302
INFO - Device node communication port opened: 192.168.1.107:9300
INFO - Mobile application communication port opened: 192.168.1.107:9301
INFO - Thread 'sensor-listener' started
INFO - Thread 'android-listener' started
INFO - Thread 'aliyun-uploader' started
INFO - Gateway ready
```

### 5. Verify Gateway Operation

```bash
# Run health check
cd Python/scripts
python health_check.py
```

---

## Android Application Deployment

### 1. Configure Gateway Connection

Edit `Android IoT APP/app/src/main/assets/config.properties`:

```
ip = 192.168.1.107    # Python gateway IP
port = 9301           # Android communication port (Note: it's 9301, not 3001)
```

⚠️ **Important**: Ensure the port is 9301, consistent with Python gateway configuration!

### 2. Build APK

Using Android Studio:

1. Open project: `Android IoT APP`
2. Wait for Gradle sync to complete
3. Build → Generate Signed Bundle / APK
4. Select APK, create or select signing key
5. Select release build

Or use command line:

```bash
cd "Android IoT APP"
./gradlew assembleRelease
```

APK output location: `app/build/outputs/apk/release/app-release.apk`

### 3. Install to Device

```bash
# Install using ADB
adb install app/build/outputs/apk/release/app-release.apk

# Or transfer APK to phone and install directly
```

---

## Device Unit Deployment

### 1. Configuration Generation

**Method 1: Using Configuration Generator (Recommended)**

```bash
cd Python/scripts
python generate_device_config.py
```

This will automatically generate configuration files for each device.

**Method 2: Manual Configuration**

Edit `Device Unit code/config_template.h`, then rename to `config.h`:

```c
#define WIFI_SSID           "Your WiFi Name"
#define WIFI_PASSWORD       "Your WiFi Password"
#define GATEWAY_IP          "192.168.1.107"
#define GATEWAY_PORT        9300
#define DEVICE_ID           "A1_tem_hum"  // Modify based on device type
```

### 2. Arduino IDE Configuration

1. Install ESP8266 board support:
   - File → Preferences → Additional Boards Manager URLs
   - Add: `http://arduino.esp8266.com/stable/package_esp8266com_index.json`
   - Tools → Board → Boards Manager → Search "ESP8266" → Install

2. Install required libraries:
   - `Adafruit_SSD1306` (OLED display)
   - `Adafruit_GFX` (Graphics library)
   - `DHT_sensor_library` (Temperature/humidity sensor)
   - `BH1750` (Light intensity sensor)
   - `MFRC522` (RFID reader)
   - `ArduinoJson` (JSON processing)
   - `PubSubClient` (MQTT, for Aliyun use)

3. Select board:
   - Tools → Board → ESP8266 Boards → Generic ESP8266 Module

4. Configure upload parameters:
   - Flash Size: 4MB (FS:2MB OTA:~1019KB)
   - CPU Frequency: 80 MHz
   - Upload Speed: 115200

### 3. Upload Firmware

**Air Conditioner Unit**:
```bash
# Open Arduino IDE
# File → Open → Device Unit code/esp8266_airconditioner_unit/esp8266_airconditioner_unit.ino
# Click Upload button or press Ctrl+U
```

**Curtain Unit**:
```bash
# File → Open → Device Unit code/esp8266_curtain_unit/esp8266_curtain_unit.ino
# Upload
```

**Door Access Unit**:
```bash
# File → Open → Device Unit code/esp8266_doorsecurity_unit/esp8266_doorsecurity_unit.ino
# Upload
```

### 4. Verify Device Connection

After device upload successfully, check connection logs in Python gateway console:

```
INFO - Device node connection: ('192.168.1.xxx', xxxxx)
INFO - Device node 'A1_tem_hum' connected to gateway
```

Device OLED should display:
```
T: 25.0
H: 60.0
S: 10
```

---

## System Testing

### 1. Unit Testing

**Python Gateway Testing**:
```bash
# Test database connection
cd Python/Database Server
python -c "import database_process_server; print('OK')"

# Test gateway startup
cd Gate
python gate.py
```

**Android Application Testing**:
1. Launch application
2. Test login functionality
3. Test registration functionality
4. View sensor data display

**Device Unit Testing**:
1. Observe OLED display
2. Check serial monitor (Tools → Serial Monitor, baud rate 115200)
3. Verify sensor data upload

### 2. Integration Testing

**Test Data Flow**:

1. **Device → Gateway → Android**:
   - Change environment near device (temperature, light)
   - Observe Android application data update

2. **Android → Gateway → Device**:
   - Adjust thresholds in Android application
   - Observe device executing control actions (LED, curtain)

3. **Database Synchronization**:
   - Query historical data in MySQL
   ```sql
   USE gate_database;
   SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 10;
   ```

### 3. Stress Testing

```bash
# Run test script continuously
python scripts/stress_test.py  # If this script exists

# Monitor gateway resources
top  # Linux/Mac
taskmgr  # Windows
```

---

## Common Issues

### Q1: Device Units Cannot Connect to Gateway

**Symptoms**: ESP8266 serial displays "Connection failed"

**Causes and Solutions**:
- WiFi password error → Check `config.h`
- Gateway IP error → Confirm `GATEWAY_IP`
- Port error → Confirm `GATEWAY_PORT = 9300`
- Firewall blocking → Check if port 9300 is open
- Gateway not started → Check if `gate.py` is running

### Q2: Android Application Cannot Connect to Gateway

**Symptoms**: "Connection failed" prompt during login

**Causes and Solutions**:
- Port configuration error → Confirm `port = 9301` in `config.properties`
- Gateway IP error → Confirm IP address is correct
- Network not reachable → Check phone and gateway on same network
- Gateway not started → Check gateway logs

### Q3: Inaccurate Sensor Data

**Symptoms**: Abnormal temperature/humidity/light intensity values

**Causes and Solutions**:
- Sensor not calibrated → Refer to sensor documentation for calibration
- Wiring error → Check I2C/Wire connections
- Unstable power supply → Check 3.3V/5V power supply

### Q4: Device Control No Response

**Symptoms**: Device no action after Android sends command

**Causes and Solutions**:
- Threshold not triggered → Check intelligent decision logic
- Device ID error → Confirm `DEVICE_ID` is correct
- JSON format error → Check serial monitor output

### Q5: Database Connection Failed

**Symptoms**: "Connection to database server failed" when gateway starts

**Causes and Solutions**:
- MySQL not started → Start MySQL service
- Password error → Check `GateConfig.txt`
- Port error → Confirm MySQL port is 3306
- Firewall blocking → Open port 9302

---

## Maintenance and Monitoring

### Log Viewing

**Gateway Logs**:
```bash
# View in real-time
tail -f Python/Gate/gateway.log

# View errors
grep ERROR Python/Gate/gateway.log
```

**Database Logs**:
```bash
tail -f Python/Database Server/database.log
```

### Backup

**Database Backup**:
```bash
mysqldump -u root -p gate_database > backup_$(date +%Y%m%d).sql
```

**Configuration Backup**:
```bash
tar -czf config_backup_$(date +%Y%m%d).tar.gz Python/Gate/*.txt
```

### Performance Monitoring

```bash
# View network connections
netstat -an | grep -E '9300|9301|9302'

# View process resources
ps aux | grep python
```

---

## Appendix

### A. Port Allocation

| Service | Port | Purpose |
|---------|------|---------|
| Device Unit Communication | 9300 | ESP8266 device connection |
| Android Application | 9301 | Mobile application connection |
| Database Server | 9302 | Database process communication |
| MySQL | 3306 | Database connection |
| Aliyun MQTT | 1883 | IoT cloud platform |

### B. Device ID Mapping

| Device | Device ID | Function |
|--------|-----------|----------|
| Smart Air Conditioner | A1_tem_hum | Temperature/humidity monitoring |
| Smart Curtain | A1_curtain | Light intensity monitoring, curtain control |
| Smart Door Access | A1_security | Door access control |

### C. Data Field Description

| Field Name | Description | Unit |
|------------|-------------|------|
| Light_TH | AC light status | 0/1 |
| Temperature | Temperature | °C |
| Humidity | Humidity | % |
| Light_CU | Indoor light status | 0/1 |
| Brightness | Light intensity | Lux |
| Curtain_status | Curtain status | 0/1 |
| Door_Security_Status | Door access status | 0/1 |

---

## Technical Support

Having trouble?

1. Run health check: `python scripts/health_check.py`
2. Check log files
3. Review Common Issues section
4. Contact technical support

---

**Document Version**: 1.0
**Last Updated**: 2024
**Maintainer**: IoT Development Team
