# IoT Smart Gateway System - Developer Documentation

**Version**: v1.0  
**Update Date**: April 6, 2026  
**Scope**: Edge Computing IoT Gateway System

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Three-Tier Interaction Description](#2-three-tier-interaction-description)
3. [Network Port Configuration](#3-network-port-configuration)
4. [Communication Protocol Details](#4-communication-protocol-details)
5. [Data Format and Data Codes](#5-data-format-and-data-codes)
6. [Database Server](#6-database-server)
7. [Startup Methods](#7-startup-methods)
8. [AI Agent and LLM Technology](#8-ai-agent-and-llm-technology)
9. [Development Guide](#9-development-guide)
10. [API Reference](#10-api-reference)
11. [Troubleshooting](#11-troubleshooting)
12. [Appendix](#12-appendix)

---

## 1. System Architecture Overview

### 1.1 System Components

The IoT smart gateway system consists of three main tiers:

```
┌─────────────────────────────────────────────────────────────┐
│               IoT Smart Gateway System Architecture         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐         ┌──────────────┐         ┌────────┐ │
│  │ Android End │◄────────┤ Edge Gateway  │─────────►│ Device │ │
│  │ (Mobile App)│  TCP    │   (Python)    │   TCP    │ (ESP)  │ │
│  └─────────────┘         └──────────────┘         └────────┘ │
│         │                        │                       │    │
│         │                        │                       │    │
│         ▼                        ▼                       ▼    │
│  User Interface          Data Processing and          Sensor  │
│  Control                 Forwarding                   Data    │
│  Threshold Settings      Intelligent Decision         Device  │
│  Data Visualization      Data Storage                 Status  │
│                          Reporting                     Control │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              External Services                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   MySQL     │  │  Aliyun IoT │  │   Database  │  │  │
│  │  │   Local DB  │  │    MQTT     │  │   Server    │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Tier Responsibilities

#### Android End (Mobile Application)
- **Responsibilities**:
  - User login and registration
  - Real-time display of sensor data
  - Send control commands to gateway
  - Set sensor thresholds
  - Control device on/off status
- **Tech Stack**: Android (Java/Kotlin)
- **Configuration File**: `app/src/main/assets/config.properties`

#### Edge Gateway End (Python)
- **Responsibilities**:
  - Manage device connections and authentication
  - Receive sensor data and store it
  - Execute intelligent decision logic
  - Forward control commands to devices
  - Push data to Android and Aliyun IoT
  - Communicate with database server
- **Tech Stack**: Python 3.x
- **Main Modules**:
  - `gate.py` / `gate_test.py` (Main program)
  - `sensor_handler.py` (Device communication)
  - `android_handler.py` (Android communication)
  - `aliyun_handler.py` (Aliyun IoT communication)
  - `database.py` (Local database operations)

#### Device End (ESP8266)
- **Responsibilities**:
  - Collect sensor data (temperature/humidity, light, etc.)
  - Send data to gateway
  - Receive control commands
  - Execute device control (LED, relay, etc.)
- **Tech Stack**: Arduino C++ (ESP8266)
- **Device Types**:
  - `A1_tem_hum` - Smart Air Conditioner Unit
  - `A1_curtain` - Smart Curtain Unit
  - `A1_security` - Door Access Security Unit

### 1.3 Data Flow

```
┌─────────┐
│ Device  │
│ ESP8266 │
└────┬────┘
     │ TCP:9300
     │ 1. Send device ID
     │ 2. Receive "start" response
     │ 3. Send sensor data (every 3 seconds)
     │ 4. Receive control commands (every 3 seconds)
     ▼
┌──────────────┐
│ Edge Gateway │
│   Python     │
└────┬───────┬─┘
     │       │
     │       │ TCP:9301
     │       │ 1. Send login request
     │       │ 2. Receive login response
     │       │ 3. Receive sensor data (every 2 seconds)
     │       │ 4. Send control commands
     │       ▼
     │   ┌─────────┐
     │   │Android │
     │   └─────────┘
     │
     │ MySQL (Local storage)
     │ MQTT (Aliyun IoT)
     │ TCP:9302 (Database server)
     ▼
┌──────────────────┐
│  External Service│
│      Layer       │
└──────────────────┘
```

---

## 2. Three-Tier Interaction Description

### 2.1 Device End → Gateway End

#### Connection Establishment Process

```
Device End (ESP8266)                Gateway End (Python)
      │                                  │
      │  1. TCP connection request      │
      │─────────────────────────────────►│
      │                                  │
      │  2. Send device ID + "\n"       │
      │─────────────────────────────────►│
      │   "A1_tem_hum\n"                 │
      │                                  │  3. Verify device permission
      │                                  │  (Check allowed device list)
      │                                  │
      │  4. Receive response + "\n"      │
      │◄─────────────────────────────────│
      │   "start\n"                      │  Device authorized, start communication
      │                                  │
      │  5. Start bidirectional         │
      │     communication                │
      │    - Send sensor data (every 3s) │
      │    - Receive control commands (every 3s)│
```

#### Device ID Verification Rules

- **Verification Condition**: Device ID must be in the allowed device list
- **Allowed Device List**: Retrieved from database server (default list used in test mode)
- **Default Device List**: `["A1_tem_hum", "A1_curtain", "A1_security"]`
- **Verification Result**:
  - ✅ Pass: Send `"start\n"`, start bidirectional communication
  - ❌ Fail: Close connection, refuse service

#### Sensor Data Sending

**Sending Frequency**: Every 3 seconds (configurable)  
**Data Format**: JSON object + "\n"

**Example Data**:
```json
{
  "device_id": "A1_tem_hum",
  "Light_TH": 0,
  "Temperature": 25.5,
  "Humidity": 60.5,
  "Light_CU": 0,
  "Brightness": 500.0,
  "Curtain_status": 1
}
```

**Data Field Description**:
| Field Name | Type | Description | Range |
|------------|------|-------------|-------|
| device_id | string | Device unique identifier | - |
| Light_TH | int | AC light status | 0=off, 1=on |
| Temperature | float | Temperature value | 0.0-100.0 |
| Humidity | float | Humidity value | 0.0-100.0 |
| Light_CU | int | Light sensor status | 0=off, 1=on |
| Brightness | float | Light intensity | 0.0-65535.0 |
| Curtain_status | int | Curtain status | 0=off, 1=on |

#### Control Command Reception

**Receiving Frequency**: Every 3 seconds (configurable)  
**Data Format**: JSON object + "\n"

**Example Data**:
```json
{
  "Light_TH": 1,
  "Temperature": -1,
  "Humidity": -1,
  "Light_CU": 0,
  "Brightness": 500.0,
  "Curtain_status": 1
}
```

**Device Response**:
- Parse JSON data
- Update local control variables
- Execute device control (such as LED on/off)

---

### 2.2 Android End → Gateway End

#### Connection Establishment Process

```
Android End                        Gateway End
     │                                  │
     │  1. TCP connection request      │
     │─────────────────────────────────►│
     │                                  │
     │  2. Send login request (JSON)    │
     │─────────────────────────────────►│
     │   {                              │
     │     "op": "login",               │
     │     "data": {                    │
     │       "account": "Jiang",        │
     │       "password": "pwd",         │
     │       "device_Key": "A1"         │
     │     },                           │
     │     "status": "1"                │
     │   }                              │
     │                                  │  3. Verify user credentials
     │                                  │  (Check UserConfig.txt)
     │                                  │
     │  4. Receive login response (JSON)│
     │◄─────────────────────────────────│
     │   {                              │  Login successful
     │     "status": 1                  │  status=1
     │   }                              │
     │                                  │
     │  5. Wait for device connection   │
     │  (Wait for sensor_data available)│
     │                                  │  6. Start bidirectional
     │  7. Receive sensor data (every 2s)│  communication
     │◄─────────────────────────────────│
     │                                  │  Push data snapshot
     │  8. Send control command         │
     │─────────────────────────────────►│
     │   {                              │
     │     "op": "light_th_open",       │
     │     "data": "1",                 │
     │     "status": "1"                │
     │   }                              │
     │                                  │  9. Update threshold data
     │                                  │  10. Push new threshold to device
```

#### User Login

**Request Format**:
```json
{
  "op": "login",
  "data": {
    "account": "username",
    "password": "password",
    "device_Key": "device_key"
  },
  "status": "1"
}
```

**Response Format**:
```json
{
  "status": 1
}
```

**Response Code**:
| status | Description |
|--------|-------------|
| 1 | Login successful |
| 0 | Login failed (incorrect username or password) |

#### User Registration

**Request Format**:
```json
{
  "op": "register",
  "data": {
    "account": "username",
    "password": "password",
    "device_Key": "device_key"
  },
  "status": "1"
}
```

**Response Format**:
```json
{
  "status": 1
}
```

**Registration Process**:
1. Gateway receives registration request
2. Forward to database server
3. Database server creates user record
4. Gateway updates local UserConfig.txt
5. Return response to Android

#### Sensor Data Reception

**Receiving Frequency**: Every 2 seconds (configurable)  
**Data Format**: JSON object + "\n"

**Example Data**:
```json
{
  "Light_TH": 0,
  "Temperature": 25.5,
  "Humidity": 60.5,
  "Light_CU": 0,
  "Brightness": 500.0,
  "Curtain_status": 1
}
```

**Android End Processing**:
- Parse JSON data
- Update UI display
- Draw real-time charts
- Display device status

#### Control Command Sending

**Command Format**:
```json
{
  "op": "operation_code",
  "data": "data_value",
  "status": "1"
}
```

**Supported Commands**:
| Operation Code | Data Value | Description |
|----------------|------------|-------------|
| light_th_open | "1" | Turn on smart AC |
| light_th_close | "1" | Turn off smart AC |
| change_temperature_threshold | "28" | Modify temperature threshold |
| change_humidity_threshold | "60" | Modify humidity threshold |
| curtain_open | "1" | Open curtain |
| curtain_close | "1" | Close curtain |
| change_brightness_threshold | "500" | Modify brightness threshold |

---

### 2.3 Gateway End → Database Server

#### Connection Establishment Process

```
Gateway End                     Database Server
     │                                  │
     │  1. TCP connection request (port 9302)│
     │─────────────────────────────────►│
     │                                  │
     │  2. Connection successful        │
     │                                  │
     │  3. Send request (JSON)          │
     │─────────────────────────────────►│
     │   {                              │
     │     "op": "check_device_id",     │
     │     "data": "A1",                │
     │     "status": 1                  │
     │   }                              │
     │                                  │  4. Process request
     │                                  │  (Query database)
     │                                  │
     │  5. Receive response (JSON)      │
     │◄─────────────────────────────────│
     │   {                              │
     │     "op": "check_device_id",     │
     │     "data": ["A1_tem_hum",...],   │
     │     "status": 1                  │
     │   }                              │
```

#### Supported Operations

| Operation Code | Description | Request Data | Response Data |
|----------------|-------------|--------------|---------------|
| check_device_id | Get allowed device list | device_key | Device ID array |
| check_userconfig_illegal | Check user configuration | {"username":...} | Corrected user information |
| add_new_user | Add new user | {"username":...} | status: 1=success, 0=fail, 2=error |

---

## 3. Network Port Configuration

### 3.1 Port Allocation Table

| Port | Purpose | Protocol | Description |
|------|---------|----------|-------------|
| **9300** | Device Communication Port | TCP | ESP8266 device connection |
| **9301** | Android Communication Port | TCP | Android application connection |
| **9302** | Database Server Port | TCP | Database server communication |
| **1883** | Aliyun IoT MQTT | TCP | MQTT protocol communication |
| **3306** | MySQL Database | TCP | Local database |

### 3.2 Configuration Files

#### Gateway Configuration File (GateConfig.txt)

**Location**: `Python/Gate/GateConfig.txt`  
**Format**: Plain text, one configuration item per line

```
Gateway IP
Database server IP
Device port
Android port
Database server port
MySQL username
MySQL password
Database name
```

**Example**:
```
192.168.1.107
192.168.1.107
9300
9301
9302
root
1234
gate_database
```

#### User Configuration File (UserConfig.txt)

**Location**: `Python/Gate/UserConfig.txt`  
**Format**: Plain text, one configuration item per line

```
Username
Password
Device key
```

**Example**:
```
Jiang
pwd
A1
```

#### Android Configuration File (config.properties)

**Location**: `Android IoT APP/app/src/main/assets/config.properties`  
**Format**: key=value format

```properties
ip = 192.168.1.107
port = 9301
```

#### Device Configuration File (config.h)

**Location**: `Device Unit code/*/config.h`  
**Format**: C++ macro definitions

```cpp
#define DEVICE_ID "A1_tem_hum"
#define GATEWAY_IP "192.168.1.107"
#define GATEWAY_PORT 9300
#define WIFI_SSID "your_wifi_ssid"
#define WIFI_PASSWORD "your_wifi_password"
```

### 3.3 Configuration Generation Tool

**Tool**: `Python/scripts/generate_device_config.py`

**Purpose**: Automatically generate device configuration files

**Usage**:
```bash
cd "d:\projects\ai_generate\edge computing home"
python Python/scripts/generate_device_config.py
```

---

## 4. Communication Protocol Details

### 4.1 Protocol Overview

All TCP communications use **JSON format** uniformly, with messages separated by **`\n` (LF)**.

#### Message Format

**Type 1: Command/Response Messages**
```json
{
  "op": "operation_code",
  "data": "data_payload",
  "status": "status_code"
}
```

**Type 2: Data Stream Push Messages**
```json
{
  "field1": "value1",
  "field2": "value2",
  ...
}
```

### 4.2 Message Terminator

**Terminator**: `\n` (Line Feed, ASCII 10)  
**Purpose**: Separate independent messages  
**Processing**:
- Automatically append `\n` when sending
- Read until `\n` when receiving

### 4.3 JSON Encoding Standards

#### Character Encoding
- **Encoding Format**: UTF-8
- **Chinese Characters**: Allowed, use `ensure_ascii=False` for serialization

#### Data Type Mapping

| JSON Type | Python Type | Description |
|-----------|-------------|-------------|
| string | str | Text string |
| number | int/float | Numeric value |
| boolean | bool | Boolean value |
| array | list | Array |
| object | dict | Object |

### 4.4 Communication Function Library

#### Python End (common/protocol.py)

**Send JSON Data**:
```python
from common.protocol import send_json

send_json(socket, {"key": "value"})
# Actually sends: {"key": "value"}\n
```

**Receive JSON Data**:
```python
from common.protocol import recv_json

data = recv_json(socket)
# Returns: {"key": "value"}
```

**Send Text Line**:
```python
from common.protocol import send_line

send_line(socket, "start")
# Actually sends: start\n
```

**Receive Text Line**:
```python
from common.protocol import recv_line

line = recv_line(socket)
# Returns: "start"
```

#### Device End (ESP8266)

**Send JSON Data**:
```cpp
#include <ArduinoJson.h>

StaticJsonDocument<200> doc;
doc["device_id"] = "A1_tem_hum";
doc["Temperature"] = 25.5;

String jsonStr;
serializeJson(doc, jsonStr);
client.println(jsonStr);  // Automatically appends \n
```

**Receive JSON Data**:
```cpp
StaticJsonDocument<200> doc;
String jsonStr = client.readStringUntil('\n');

deserializeJson(doc, jsonStr);
int temperature = doc["Temperature"];
```

#### Android End (Java)

**Send JSON Data**:
```java
JSONObject json = new JSONObject();
json.put("op", "login");
json.put("data", userData);

String jsonString = json.toString();
outputStream.write((jsonString + "\n").getBytes());
```

**Receive JSON Data**:
```java
BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream));
String line = reader.readLine();  // Read until \n

JSONObject json = new JSONObject(line);
String status = json.getString("status");
```

---

## 5. Data Format and Data Codes

### 5.1 Operation Codes (op) List

#### Android → Gateway

| Operation Code | Purpose | data Type | status |
|----------------|---------|-----------|--------|
| login | User login | JSONObject | "1" |
| register | User registration | JSONObject | "1" |
| light_th_open | Turn on AC | "1" | "1" |
| light_th_close | Turn off AC | "1" | "1" |
| change_temperature_threshold | Modify temperature threshold | "28" | "1" |
| change_humidity_threshold | Modify humidity threshold | "60" | "1" |
| curtain_open | Open curtain | "1" | "1" |
| curtain_close | Close curtain | "1" | "1" |
| change_brightness_threshold | Modify brightness threshold | "500" | "1" |

#### Gateway → Database Server

| Operation Code | Purpose | data Type | status |
|----------------|---------|-----------|--------|
| check_device_id | Get allowed device list | "A1" | 1 |
| check_userconfig_illegal | Check user configuration | JSONObject | 1 |
| add_new_user | Add new user | JSONObject | 1 |

### 5.2 Data Field Description

#### Sensor Data Fields

| Field Name | Type | Description | Default | Range |
|------------|------|-------------|---------|-------|
| Light_TH | int | Smart AC light status | 0 | 0=off, 1=on |
| Temperature | float | Temperature value | 0.0 | 0.0-100.0 (°C) |
| Humidity | float | Humidity value | 0.0 | 0.0-100.0 (%) |
| Light_CU | int | Light sensor status | 0 | 0=off, 1=on |
| Brightness | float | Light intensity | 0.0 | 0.0-65535.0 |
| Curtain_status | int | Curtain status | 1 | 0=off, 1=on |

#### Door Access Data Fields

| Field Name | Type | Description | Default | Range |
|------------|------|-------------|---------|-------|
| Door_Security_Status | int | Door access status | 0 | 0=denied, 1=granted |
| Door_Secur_Card_id | string | Card ID | "" | - |

#### Threshold Data Fields

| Field Name | Type | Description | Default | Special Values |
|------------|------|-------------|---------|----------------|
| Temperature | float | Temperature threshold | 30.0 | -1=no limit |
| Humidity | float | Humidity threshold | 65.0 | -1=no limit |
| Brightness | float | Light intensity threshold | 500.0 | -2=no limit, 65535=never trigger |

### 5.3 Status Codes Description

#### General Status Codes

| Value | Description | Usage Scenario |
|-------|-------------|----------------|
| 0 | Failed | Login failed, registration failed, data format error |
| 1 | Successful | Operation successful, data correct |
| 2 | Error | Database server error, exception |

#### Door Access Status Codes

| Value | Description | Constant |
|-------|-------------|----------|
| 0 | Denied | `DOOR_DENIED` |
| 1 | Granted | `DOOR_GRANTED` |

### 5.4 Data Examples

#### Login Request Example

**Request**:
```json
{
  "op": "login",
  "data": {
    "account": "Jiang",
    "password": "pwd",
    "device_Key": "A1"
  },
  "status": "1"
}
```

**Response**:
```json
{
  "status": 1
}
```

#### Sensor Data Example

**Device Sends**:
```json
{
  "device_id": "A1_tem_hum",
  "Light_TH": 0,
  "Temperature": 25.5,
  "Humidity": 60.5,
  "Light_CU": 0,
  "Brightness": 500.0,
  "Curtain_status": 1
}
```

**Gateway Stores** (MySQL):
```sql
INSERT INTO gate_local_data 
(timestamp, light_th, temperature, humidity, light_cu, brightness, curtain_status)
VALUES 
('2026-04-06 13:16:23', 0, 25.5, 60.5, 0, 500.0, 1);
```

#### Control Command Example

**Android Sends**:
```json
{
  "op": "light_th_open",
  "data": "1",
  "status": "1"
}
```

**Gateway Processing**:
```python
# Update thresholds
state.set_threshold(FIELD_TEMPERATURE, -1)
state.set_threshold(FIELD_HUMIDITY, -1)

# Push to device
# Device receives:
{
  "Light_TH": 1,
  "Temperature": -1,
  "Humidity": -1,
  ...
}
```

#### Intelligent Decision Example

**Trigger Conditions**:
```
Temperature = 31.5 >= Threshold = 30.0
Humidity = 68.0 >= Threshold = 65.0
```

**Decision Result**:
```json
{
  "Light_TH": 1,  // Turn on AC
  "Temperature": 31.5,
  "Humidity": 68.0,
  ...
}
```

---

## 6. Database Server

### 6.1 Server Overview

The database server is the central data management component of the system, responsible for:
- User registration and authentication
- User configuration validation and correction
- Device key management
- Device list queries
- Remote data persistence

**Tech Stack**: Python + MySQL  
**Communication Protocol**: TCP (port 9302)  
**Data Format**: JSON

### 6.2 Server Architecture

```
┌───────────────────────────────────────────────────────────┐
│               Database Server Architecture                │
├───────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐      ┌──────────────┐              │
│  │  Gateway End │◄─────│ Database     │              │
│  │  (Python)    │ TCP   │ Server       │              │
│  └──────────────┘ 9302  └──────┬───────┘              │
│                               │                        │
│                               │ MySQL                  │
│                               ▼                        │
│                      ┌───────────────┐                │
│                      │  MySQL Database│                │
│                      │   (user_test) │                │
│                      └───────┬───────┘                │
│                              │                        │
│          ┌───────────────────┼───────────────────┐    │
│          ▼                   ▼                   ▼    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │  users_data │    │  device_key │    │ device_data │ │
│  │   User Table│    │   Key Table │    │  Device Table│ │
│  └─────────────┘    └─────────────┘    └─────────────┘ │
│                                                          │
└───────────────────────────────────────────────────────────┘
```

### 6.3 Database Table Structure

#### users_data - User Data Table

Stores user account information and associated device keys.

| Field Name | Type | Description | Constraint |
|------------|------|-------------|-------------|
| username | VARCHAR(50) | Username | PRIMARY KEY |
| password | VARCHAR(100) | Password | NOT NULL |
| owned_device_key | VARCHAR(50) | Owned device key | UNIQUE KEY |

**SQL CREATE Statement**:
```sql
CREATE TABLE IF NOT EXISTS `users_data` (
  `username` VARCHAR(50) NOT NULL,
  `password` VARCHAR(100) NOT NULL,
  `owned_device_key` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`username`),
  UNIQUE KEY `owned_device_key` (`owned_device_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### device_key - Device Key Table

Stores allocation and usage status of device keys.

| Field Name | Type | Description | Constraint |
|------------|------|-------------|-------------|
| key_id | VARCHAR(50) | Key ID | PRIMARY KEY |
| owned_by_user | VARCHAR(50) | Owning user | DEFAULT NULL |
| is_used | TINYINT(1) | Whether used | DEFAULT 0 |

**SQL CREATE Statement**:
```sql
CREATE TABLE IF NOT EXISTS `device_key` (
  `key_id` VARCHAR(50) NOT NULL,
  `owned_by_user` VARCHAR(50) DEFAULT NULL,
  `is_used` TINYINT(1) DEFAULT 0,
  PRIMARY KEY (`key_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### device_data - Device Data Table

Stores device names and bound keys.

| Field Name | Type | Description | Constraint |
|------------|------|-------------|-------------|
| device_name | VARCHAR(50) | Device name | PRIMARY KEY |
| bind_device_key | VARCHAR(50) | Bound key | NOT NULL |

**SQL CREATE Statement**:
```sql
CREATE TABLE IF NOT EXISTS `device_data` (
  `device_name` VARCHAR(50) NOT NULL,
  `bind_device_key` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`device_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 6.4 Communication Protocol

#### Connection Flow

```
Gateway End                     Database Server
     │                                  │
     │  1. TCP connection request (port 9302)│
     │─────────────────────────────────►│
     │                                  │  2. Accept connection
     │                                  │  Create separate thread
     │                                  │
     │  3. Send request (JSON)          │
     │─────────────────────────────────►│
     │   {                              │
     │     "op": "check_device_id",      │  4. Parse request
     │     "data": "A1",               │     Identify operation code
     │     "status": 1                  │
     │   }                              │
     │                                  │  5. Execute SQL query
     │                                  │     SELECT ...
     │                                  │
     │  6. Receive response (JSON)       │
     │◄─────────────────────────────────│
     │   {                              │  6. Construct response
     │     "op": "check_device_id",     │     Query results
     │     "data": ["A1_tem_hum",...],   │
     │     "status": 1                  │
     │   }                              │
     │                                  │
     │  7. Continue sending next request...│
     │─────────────────────────────────►│
```

#### Message Format

**Request Format**:
```json
{
  "op": "operation_code",
  "data": "data_payload",
  "status": 1
}
```

**Response Format**:
```json
{
  "op": "operation_code",
  "data": "response_data",
  "status": 1
}
```

#### Communication Features

- **Protocol**: TCP
- **Port**: 9302
- **Message Format**: JSON
- **Separator**: `\n` (Line Feed)
- **Encoding**: UTF-8
- **Concurrency**: Multi-threaded processing, separate thread per gateway connection

### 6.5 Operation Code Details

#### 6.5.1 check_device_id - Query Device List

**Purpose**: Query all device names bound to a device key based on the key

**Request Example**:
```json
{
  "op": "check_device_id",
  "data": "A1",
  "status": 1
}
```

**Request Parameters**:
| Field Name | Type | Description |
|------------|------|-------------|
| op | string | Fixed value: "check_device_id" |
| data | string | Device key (e.g., "A1") |
| status | int | Fixed value: 1 |

**SQL Query**:
```sql
SELECT device_name FROM device_data WHERE bind_device_key = %s
```

**Response Example** (Success):
```json
{
  "op": "check_device_id",
  "data": ["A1_tem_hum", "A1_curtain", "A1_security"],
  "status": 1
}
```

**Response Example** (Failure):
```json
{
  "op": "check_device_id",
  "data": "Device key does not exist",
  "status": 0
}
```

**Response Code**:
| status | Description |
|--------|-------------|
| 1 | Query successful, return device list |
| 0 | Query failed, return error message |
| 2 | Database exception |

**Usage Scenarios**:
- Gateway retrieves allowed device list at startup
- User retrieves their owned devices when logging in
- Query device ownership during device management

#### 6.5.2 check_userconfig_illegal - User Configuration Validation

**Purpose**: Verify if gateway local user configuration is valid, attempt to correct if abnormal

**Request Example**:
```json
{
  "op": "check_userconfig_illegal",
  "data": {
    "username": "Jiang",
    "password": "pwd",
    "device_key": "A1"
  },
  "status": 1
}
```

**Request Parameters**:
| Field Name | Type | Description |
|------------|------|-------------|
| op | string | Fixed value: "check_userconfig_illegal" |
| data | object | User information object |
| data.username | string | Username |
| data.password | string | Password |
| data.device_key | string | Device key |
| status | int | Fixed value: 1 |

**SQL Query**:
```sql
SELECT * FROM users_data 
WHERE username = %s AND password = %s AND owned_device_key = %s
```

**Response Example 1** (Configuration Valid):
```json
{
  "op": "check_userconfig_illegal",
  "data": "NULL",
  "status": 1
}
```

**Response Example 2** (Configuration Invalid, Corrected):
```json
{
  "op": "check_userconfig_illegal",
  "data": {
    "username": "Jiang",
    "password": "correct_pwd",
    "device_key": "A1"
  },
  "status": 1
}
```

**Response Example 3** (User Not Registered):
```json
{
  "op": "check_userconfig_illegal",
  "data": "NULL",
  "status": 0
}
```

**Response Code**:
| status | Description | Follow-up Action |
|--------|-------------|-----------------|
| 1 | Configuration valid or corrected | Gateway updates configuration |
| 0 | Configuration invalid, cannot correct | Gateway logs warning |
| 2 | Database exception | Gateway logs error |

**Processing Flow**:
```
1. Receive user configuration
   ↓
2. Query database for verification
   ↓
3a. Configuration matches → Return status=1
   ↓
3b. Configuration mismatch → Return status=0
   ↓
4. Attempt correction: query by username
   ↓
5a. User found → Return correct configuration (status=1)
   ↓
5b. User not found → Return status=0
```

#### 6.5.3 add_new_user - Add New User

**Purpose**: Register a new user and associate with device key

**Request Example**:
```json
{
  "op": "add_new_user",
  "data": {
    "username": "test_user",
    "password": "test_password",
    "device_key": "A2"
  },
  "status": 1
}
```

**Request Parameters**:
| Field Name | Type | Description |
|------------|------|-------------|
| op | string | Fixed value: "add_new_user" |
| data | object | User information object |
| data.username | string | Username |
| data.password | string | Password |
| data.device_key | string | Device key |
| status | int | Fixed value: 1 |

**SQL Operations** (Transaction):
```sql
-- 1. Insert user data
INSERT INTO users_data (username, password, owned_device_key) 
VALUES (%s, %s, %s);

-- 2. Update device key ownership
UPDATE device_key SET owned_by_user = %s WHERE key_id = %s;

-- 3. Mark key as used
UPDATE device_key SET is_used = 1 WHERE owned_by_user = %s;
```

**Response Example** (Success):
```json
{
  "op": "add_new_user",
  "data": "NULL",
  "status": 1
}
```

**Response Example** (Failure - User Already Exists):
```json
{
  "op": "add_new_user",
  "data": "NULL",
  "status": 0
}
```

**Response Example** (Database Exception):
```json
{
  "op": "add_new_user",
  "data": "Duplicate entry 'test_user' for key 'PRIMARY'",
  "status": 2
}
```

**Response Code**:
| status | Description |
|--------|-------------|
| 1 | User added successfully |
| 0 | User addition failed (primary key or unique key conflict) |
| 2 | Database exception, return error message |

**Transaction Handling**:
```python
try:
    cursor.execute(sql1, (username, password, device_key))
    cursor.execute(sql2, (username, device_key))
    cursor.execute(sql3, (username,))
    db.commit()  # Commit transaction
except Exception:
    db.rollback()  # Rollback transaction
```

### 6.6 Various Scenario Handling

#### Scenario 1: Gateway Configuration Correct

**Scenario**: Gateway's `UserConfig.txt` matches database

**Request**:
```json
{
  "op": "check_userconfig_illegal",
  "data": {"username": "Jiang", "password": "pwd", "device_key": "A1"},
  "status": 1
}
```

**Response**:
```json
{
  "op": "check_userconfig_illegal",
  "data": "NULL",
  "status": 1
}
```

**Gateway Behavior**: Configuration normal, continue operation

---

#### Scenario 2: Gateway Password Error

**Scenario**: User modified gateway configuration file password

**Request**:
```json
{
  "op": "check_userconfig_illegal",
  "data": {"username": "Jiang", "password": "wrong_pwd", "device_key": "A1"},
  "status": 1
}
```

**First Response**:
```json
{
  "op": "check_userconfig_illegal",
  "data": "NULL",
  "status": 0
}
```

**Correction Request**: Query database by username

**Correction Response**:
```json
{
  "op": "check_userconfig_illegal",
  "data": {"username": "Jiang", "password": "pwd", "device_key": "A1"},
  "status": 1
}
```

**Gateway Behavior**:
1. Receive status=0, log warning
2. Receive correct configuration, update `UserConfig.txt`
3. Restart gateway or reload configuration

---

#### Scenario 3: User Not Registered

**Scenario**: New gateway or user deleted

**Request**:
```json
{
  "op": "check_userconfig_illegal",
  "data": {"username": "new_user", "password": "pwd", "device_key": "A1"},
  "status": 1
}
```

**First Response**:
```json
{
  "op": "check_userconfig_illegal",
  "data": "NULL",
  "status": 0
}
```

**Correction Attempt**: Query by username

**Correction Response**:
```json
{
  "op": "check_userconfig_illegal",
  "data": "NULL",
  "status": 0
}
```

**Gateway Behavior**:
1. Log error
2. Refuse service
3. Prompt user to register first

---

#### Scenario 4: Device Key Does Not Exist

**Scenario**: Query non-existent device key

**Request**:
```json
{
  "op": "check_device_id",
  "data": "A99",
  "status": 1
}
```

**Response**:
```json
{
  "op": "check_device_id",
  "data": [],
  "status": 1
}
```

**Gateway Behavior**:
1. Return empty list
2. Log: Device not found
3. Gateway unable to connect any devices

---

#### Scenario 5: User Already Exists

**Scenario**: Attempt to register existing username

**Request**:
```json
{
  "op": "add_new_user",
  "data": {"username": "Jiang", "password": "new_pwd", "device_key": "A2"},
  "status": 1
}
```

**Response**:
```json
{
  "op": "add_new_user",
  "data": "NULL",
  "status": 0
}
```

**Gateway Behavior**:
1. Receive status=0
2. Return registration failure message to Android
3. Prompt user: Username already exists

---

#### Scenario 6: Device Key Already Used

**Scenario**: Attempt to register with already allocated key

**Request**:
```json
{
  "op": "add_new_user",
  "data": {"username": "new_user", "password": "pwd", "device_key": "A1"},
  "status": 1
}
```

**Response**:
```json
{
  "op": "add_new_user",
  "data": "NULL",
  "status": 0
}
```

**Gateway Behavior**:
1. Receive status=0
2. Return registration failure message to Android
3. Prompt user: Device key already in use

---

#### Scenario 7: Database Connection Failed

**Scenario**: MySQL service not started or network interrupted

**Request**: Send any request

**Response**: No response (connection timeout)

**Gateway Behavior**:
1. Catch connection exception
2. Log error
3. Production mode: Exit program
4. Test mode: Continue to run, use default configuration

---

#### Scenario 8: Database Query Exception

**Scenario**: SQL syntax error or table does not exist

**Request**:
```json
{
  "op": "check_device_id",
  "data": "A1",
  "status": 1
}
```

**Response**:
```json
{
  "op": "check_device_id",
  "data": "Table 'user_test.device_data' doesn't exist",
  "status": 0
}
```

**Gateway Behavior**:
1. Receive status=0
2. Log error and stack trace
3. Return empty list or error message

---

### 6.7 Configuration Files

#### serverConfig.txt

**Location**: `Python/Database Server/serverConfig.txt`

**Format**:
```
<Listening IP>
<Listening Port>
```

**Example**:
```
0.0.0.0
9302
```

**Configuration Description**:
- **Listening IP**:
  - `0.0.0.0`: Listen on all network interfaces (recommended)
  - `127.0.0.1`: Local access only
  - `192.168.x.x`: Specific IP (valid only if that IP exists)
- **Listening Port**: 9302 (default)

**Notes**:
- ⚠️ Do not use non-existent IP addresses (e.g., `192.168.1.107` may not exist locally)
- ⚠️ Port 9302 must not be occupied
- ⚠️ Restart server after modifying configuration

### 6.8 Starting Database Server

#### Method 1: Direct Start

```bash
cd "d:\projects\ai_generate\edge computing home\Python\Database Server"
python database_process_server.py
```

#### Method 2: Use Test Script

```bash
cd "d:\projects\ai_generate\edge computing home"
python Python/scripts/test_database_server.py
```

#### Method 3: Background Run

**Windows**:
```bash
start /B python database_process_server.py > server.log 2>&1
```

**Linux/Mac**:
```bash
nohup python database_process_server.py > server.log 2>&1 &
```

### 6.9 Database Initialization

#### Initialize Database and Tables

```bash
mysql -u root -p1234 < Python/Database\ Server/init_database.sql
```

#### Manual Initialization

```sql
-- Create database
CREATE DATABASE IF NOT EXISTS `user_test` 
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `user_test`;

-- Create tables (see section 6.3)

-- Insert sample data
INSERT INTO users_data (username, password, owned_device_key)
VALUES ('Jiang', 'pwd', 'A1');
```

### 6.10 Testing Tools

#### Test Script

**Location**: `Python/scripts/test_database_server.py`

**Features**:
- Test database connection
- Start database server
- Test server connection
- Test query device list
- Test user configuration verification
- Test add new user

**Run Tests**:
```bash
python Python/scripts/test_database_server.py
```

**Expected Output**:
```
============================================================
Database Server and Gateway Connection Test
============================================================

============================================================
Test 1: Database Connection
============================================================
✓ Database 'user_test' exists
✓ Found 3 tables:
  - device_data
  - device_key
  - users_data

============================================================
Test 2: Start Database Server
============================================================
✓ Configuration loaded successfully:
  - Server IP: 0.0.0.0
  - Listening Port: 9302
✓ Database server started successfully

============================================================
Test Result Summary
============================================================
Database connection: ✓ Passed
Server start: ✓ Passed
Server connection: ✓ Passed
Query device list: ✓ Passed
User configuration verification: ✓ Passed
Add new user: ✓ Passed

✅ Core tests passed! Database server running normally
```

### 6.11 Logging and Debugging

#### Log Files

**Location**: `Python/Database Server/serverLogs.log`

**Log Format**:
```
[2026-04-06 13:37:10,805][INFO][__main__][database_process_server.py:60] Database connection successful
[2026-04-06 13:37:11,123][INFO][__main__][database_process_server.py:78] Gateway ('192.168.1.108', 54321) connected
[2026-04-06 13:37:11,456][INFO][__main__][database_process_server.py:104] Processing check_device_id request
[2026-04-06 13:37:11,457][INFO][__main__][database_process_server.py:238] Found 3 devices
```

#### Log Levels

| Level | Description | Usage Scenario |
|-------|-------------|----------------|
| DEBUG | Debug information | Development and debugging |
| INFO | General information | Normal operation |
| WARNING | Warning information | Configuration anomalies |
| ERROR | Error information | Operation failures |

#### Debugging Tips

**1. View Real-time Logs**:
```bash
tail -f Python/Database\ Server/serverLogs.log
```

**2. Check Database Connection**:
```python
import mysql.connector
conn = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="1234",
    database="user_test"
)
print("Connection successful")
```

**3. Test SQL Query**:
```bash
mysql -u root -p1234 user_test -e "SELECT * FROM users_data;"
```

### 6.12 Common Issues

#### Q1: Database Server Cannot Start

**Symptom**: `OSError: [WinError 10049] The requested address is not valid in its context`

**Cause**: Listening IP does not exist or is unavailable

**Solution**:
```bash
# Modify serverConfig.txt
# Change 192.168.1.107 to 0.0.0.0
```

#### Q2: Gateway Cannot Connect to Database Server

**Symptom**: Connection timeout or connection refused

**Causes**:
1. Server not started
2. Incorrect IP address configuration
3. Firewall blocking

**Solution**:
```bash
# 1. Check if server is running
netstat -ano | findstr "9302"

# 2. Test port connectivity
telnet 127.0.0.1 9302

# 3. Check firewall (Windows)
netsh advfirewall firewall show rule name=all
```

#### Q3: Database Connection Failed

**Symptom**: `mysql.connector.Error: Access denied for user`

**Cause**: Incorrect username or password

**Solution**:
```bash
# Test connection
mysql -u root -p1234

# Modify configuration
# Ensure user_test database exists
# Ensure root user password is 1234
```

---

## 7. Startup Methods

### 7.1 Environment Requirements

#### Python Environment
- **Python Version**: 3.7+
- **Dependency Packages**:
  ```bash
  pip install -r requirements.txt
  ```

**requirements.txt**:
```
mysql-connector-python
aliyun-iot-linkkit
```

#### MySQL Environment
- **MySQL Version**: 5.7+
- **Database**: gate_database
- **User Permissions**: CREATE, INSERT, SELECT

#### ESP8266 Environment
- **Development Environment**: Arduino IDE
- **Board**: ESP8266 (NodeMCU/Wemos)
- **Required Libraries**:
  - ESP8266WiFi
  - ArduinoJson
  - DHT_sensor_library
  - Adafruit_SSD1306
  - Adafruit_GFX

#### Android Environment
- **Android Studio**: 4.0+
- **Minimum SDK Version**: API 21 (Android 5.0)
- **Target SDK Version**: API 33 (Android 13)

### 7.2 Gateway Startup

#### Production Mode Startup

```bash
cd "d:\projects\ai_generate\edge computing home\Python\Gate"
python gate.py
```

**Production Mode Features**:
- Connect to database server
- Verify user configuration
- Get allowed device list
- All features enabled

#### Test Mode Startup

```bash
cd "d:\projects\ai_generate\edge computing home\Python\Gate"
python gate_test.py --test
```

**Test Mode Features**:
- ⚠️ Skip database server connection
- Use default device list
- Skip user configuration verification
- Suitable for development and testing environments

**Environment Variable Method**:
```bash
# Windows
set TEST_MODE=true
python gate.py

# Linux/Mac
export TEST_MODE=true
python gate.py
```

#### Background Run

**Windows**:
```bash
start /B python gate.py > gateway.log 2>&1
```

**Linux/Mac**:
```bash
nohup python gate.py > gateway.log 2>&1 &
```

### 7.3 Device Startup

#### Upload Firmware to ESP8266

1. **Configure Device Parameters**
   - Copy `config_template.h` to `config.h`
   - Modify WiFi information
   - Modify gateway IP and port

2. **Upload Using Arduino IDE**
   - Open `.ino` file
   - Select board: NodeMCU 1.0
   - Select port: COMx
   - Click upload button

3. **View Serial Monitor**
   - Baud rate: 115200
   - Observe connection status
   - Confirm gateway connection successful

#### Automatic Startup

**Device Auto-starts After Power-on**:
1. Connect to WiFi
2. Connect to gateway
3. Send device ID
4. Start data communication

### 7.4 Android Application Startup

#### Development Environment Startup

1. **Open Android Studio**
2. **Import Project**: `Android IoT APP`
3. **Configure Network**: Ensure `app/src/main/assets/config.properties` is correct
4. **Run Application**: Click run button

#### Install APK

1. **Build APK**
   - Build > Generate Signed Bundle / APK
   - Select APK
   - Select debug or release

2. **Install to Device**
   ```bash
   adb install app-release.apk
   ```

3. **Configure Gateway Address**
   - Open application
   - Enter gateway IP and port
   - Click connect

### 7.5 Startup Order

**Recommended Startup Order**:

```
1. Start MySQL database service
   ↓
2. Start database server (optional)
   ↓
3. Start gateway (Python)
   ↓
4. Start ESP8266 devices (multiple devices can run in parallel)
   ↓
5. Start Android application
```

**Notes**:
- ⚠️ Must start gateway before devices and Android
- ⚠️ If device or Android connection fails, check if gateway is running normally
- ⚠️ Test mode can skip steps 1 and 2

### 7.6 Health Check

**Use Health Check Tool**:
```bash
cd "d:\projects\ai_generate\edge computing home"
python Python/scripts/health_check.py
```

**Check Items**:
- Configuration file integrity
- Gateway process status
- Network port availability
- Database connection status
- Device connection status

---

## 8. AI Agent 与 LLM 技术

### 8.1 概述

EdgeHomeAI 系统集成了基于大语言模型（LLM）的 AI Agent 对话式任务编排功能，通过智谱 AI 的 GLM-4.7-Flash 模型实现自然语言理解和任务分解。该模块允许用户使用自然语言与系统交互，自动完成复杂的设备控制任务。

**核心特性**:
- 🧠 自然语言理解：支持中文对话交互
- 🎯 意图识别：自动识别用户意图和任务类型
- 📋 任务分解：将复杂任务分解为可执行的原子操作
- 🔍 能力检索：基于 RAG（检索增强生成）检索设备能力
- ⚡ 实时响应：端到端响应时间 < 10 秒
- 🔒 隐私保护：数据本地处理，减少云端依赖

### 8.2 技术架构

#### 8.2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent 系统架构                         │
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
│ Capability       │ ← 设备能力检索 (RAG)
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

#### 8.2.2 模块说明

| 模块 | 文件 | 功能描述 |
|------|------|---------|
| **Intent Planner** | `intent_planner.py` | 意图识别与任务规划，调用 LLM API |
| **Capability Retriever** | `capability_retriever.py` | 设备能力检索，基于 RAG 技术 |
| **Task Executor** | `task_executor.py` | 任务执行，调用设备控制器 |
| **Dialog Manager** | `dialog_manager.py` | 对话管理，维护对话历史和上下文 |
| **Preference Manager** | `preference_manager.py` | 用户偏好管理，学习用户习惯 |
| **Device Controller** | `device_controller.py` | 设备控制器，执行具体设备操作 |

### 8.3 LLM 技术栈

#### 8.3.1 智谱 AI GLM-4.7-Flash

**模型信息**:
- **模型名称**: GLM-4.7-Flash
- **API 提供商**: 智谱 AI (ZhipuAI)
- **模型类型**: 大语言模型
- **推理速度**: 平均 8.7 秒/请求
- **Token 效率**: 22.1ms/Token
- **上下文长度**: 2048 Tokens

**核心优势**:
- ✅ 中文理解能力强
- ✅ 响应速度快
- ✅ API 稳定可靠
- ✅ 支持流式和非流式输出
- ✅ 合理的定价策略

#### 8.3.2 API 配置

**配置文件**: `Python/Gate/ai_agent_config.txt`

```ini
[LLM]
# 智谱 AI API 配置
API_KEY = your_api_key
BASE_URL = https://open.bigmodel.cn/api/paas/v4
MODEL_NAME = GLM-4.7-Flash
TEMPERATURE = 0.7
MAX_TOKENS = 2048
STREAM = False

[DIALOG]
# 对话管理配置
MAX_CONTEXT_TURNS = 5
SESSION_TIMEOUT = 3600

[RAG]
# RAG 检索配置
CAPABILITIES_FILE = device_capabilities.json
```

**参数说明**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `API_KEY` | String | - | 智谱 AI API 密钥，必需 |
| `BASE_URL` | String | - | API 基础 URL |
| `MODEL_NAME` | String | GLM-4.7-Flash | 使用的模型名称 |
| `TEMPERATURE` | Float | 0.7 | 生成随机性控制，范围 0-1 |
| `MAX_TOKENS` | Integer | 2048 | 最大生成 Token 数 |
| `STREAM` | Boolean | False | 是否启用流式输出 |
| `MAX_CONTEXT_TURNS` | Integer | 5 | 最大对话上下文轮数 |
| `SESSION_TIMEOUT` | Integer | 3600 | 会话超时时间（秒） |

#### 8.3.3 设备能力描述

**配置文件**: `Python/Gate/device_capabilities.json`

该文件描述了系统中所有设备的能力，用于 RAG 检索。

```json
{
  "devices": [
    {
      "device_id": "A1_tem_hum",
      "device_name": "智能空调",
      "capabilities": [
        {
          "action": "get_temperature",
          "description": "获取当前温度",
          "parameters": {}
        },
        {
          "action": "get_humidity",
          "description": "获取当前湿度",
          "parameters": {}
        },
        {
          "action": "set_ac_power",
          "description": "设置空调电源",
          "parameters": {
            "power": {
              "type": "string",
              "enum": ["on", "off"],
              "required": true
            }
          }
        },
        {
          "action": "set_temperature",
          "description": "设置目标温度",
          "parameters": {
            "temperature": {
              "type": "float",
              "range": [16, 30],
              "required": true
            }
          }
        }
      ]
    },
    {
      "device_id": "A1_curtain",
      "device_name": "智能窗帘",
      "capabilities": [...]
    },
    {
      "device_id": "A1_security",
      "device_name": "智能门禁",
      "capabilities": [...]
    }
  ]
}
```

### 8.4 工作流程

#### 8.4.1 完整流程

```
1. 用户输入自然语言
   ↓
2. Dialog Manager 接收输入
   ↓
3. Intent Planner 调用 LLM 识别意图
   ↓
4. Capability Retriever 检索相关设备能力
   ↓
5. Intent Planner 生成任务计划
   ↓
6. Task Executor 执行任务
   ↓
7. Device Controller 控制设备
   ↓
8. 返回执行结果给用户
   ↓
9. Dialog Manager 更新对话历史
```

#### 8.4.2 Example Dialogue

**User Input**:
```
Please help me turn on the air conditioner, set the temperature to 26 degrees, and then open the curtain
```

**AI Agent Processing Flow**:

1. **Intent Recognition**:
```python
{
  "intent": "control_devices",
  "devices": ["A1_tem_hum", "A1_curtain"],
  "actions": [
    {"device": "A1_tem_hum", "action": "set_ac_power", "params": {"power": "on"}},
    {"device": "A1_tem_hum", "action": "set_temperature", "params": {"temperature": 26}},
    {"device": "A1_curtain", "action": "set_curtain", "params": {"open": true}}
  ]
}
```

2. **Task Execution**:
```python
# Task Executor calls Device Controller
device_controller.execute("A1_tem_hum", "set_ac_power", {"power": "on"})
device_controller.execute("A1_tem_hum", "set_temperature", {"temperature": 26})
device_controller.execute("A1_curtain", "set_curtain", {"open": true})
```

3. **Return Result**:
```python
{
  "status": "success",
  "message": "The following operations have been performed for you:\n1. Turn on the air conditioner\n2. Set temperature to 26 degrees\n3. Open the curtain",
  "details": [
    {"device": "A1_tem_hum", "action": "set_ac_power", "result": "success"},
    {"device": "A1_tem_hum", "action": "set_temperature", "result": "success"},
    {"device": "A1_curtain", "action": "set_curtain", "result": "success"}
  ]
}
```

### 8.5 API Usage

#### 8.5.1 Zhipu AI Python SDK Installation

```bash
pip install zhipuai
```

#### 8.5.2 Basic Usage

```python
from zhipuai import ZhipuAI

# Initialize client
client = ZhipuAI(api_key="your_api_key")

# Call model
response = client.chat.completions.create(
    model="GLM-4.7-Flash",
    messages=[
        {"role": "user", "content": "Hello, please introduce yourself"}
    ],
    temperature=0.7,
    max_tokens=2048
)

# Get response
print(response.choices[0].message.content)
```

#### 8.5.3 System Usage

```python
# Usage in Intent Planner
from zhipuai import ZhipuAI

class IntentPlanner:
    def __init__(self, api_key):
        self.client = ZhipuAI(api_key=api_key)
    
    def plan(self, user_input, device_capabilities):
        """Plan task"""
        prompt = self._build_prompt(user_input, device_capabilities)
        
        response = self.client.chat.completions.create(
            model="GLM-4.7-Flash",
            messages=[
                {"role": "system", "content": "You are a smart home task planning assistant"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        
        task_plan = self._parse_response(response.choices[0].message.content)
        return task_plan
```

### 8.6 Performance Optimization

#### 8.6.1 Performance Metrics

| Metric | Target Value | Actual Value | Status |
|--------|--------------|--------------|--------|
| Intent Recognition Accuracy | ≥ 95% | 100% | ✅ |
| Task Execution Accuracy | ≥ 90% | 98.6% | ✅ |
| LLM Inference Time | < 10s | 8.7s | ✅ |
| Token Efficiency | < 25ms | 22.1ms | ✅ |
| End-to-end Latency | < 10s | 9.2s | ✅ |

#### 8.6.2 Optimization Strategies

**1. Prompt Optimization**:
- Use clear and concise instructions
- Provide sufficient context information
- Use JSON format to constrain output

**2. Caching Strategy**:
- Cache common intent recognition results
- Cache device capability descriptions
- Cache user preference settings

**3. Concurrent Processing**:
- Asynchronously call LLM API
- Parallelly execute device control tasks
- Use thread pool to manage concurrency

**4. Resource Management**:
- Limit dialog history length
- Reasonably set token limits
- Release resources timely

### 8.7 Troubleshooting

#### 8.7.1 Common Issues

**Q: LLM API Call Failed?**

- Check if API Key is correct
- Verify if network connection is normal
- Check Zhipu AI service status
- Check if API quota is sufficient

**Q: Intent Recognition Inaccurate?**

- Optimize prompt content
- Increase context information
- Adjust Temperature parameter
- Enrich device capability description

**Q: Slow Response Speed?**

- Check network latency
- Reduce dialog history length
- Lower MAX_TOKENS setting
- Consider using streaming output

**Q: Token Consumption Too Fast?**

- Optimize prompt length
- Limit dialog context rounds
- Compress device capability description
- Use caching strategy

#### 8.7.2 Debugging Tools

**Enable Verbose Logging**:

```python
# Set in ai_agent_config.txt
[LOGGING]
LEVEL = DEBUG
FILE = ai_agent.log
```

**View API Call Logs**:

```bash
tail -f Python/Gate/ai_agent.log
```

### 8.8 Extension Development

#### 8.8.1 Adding New LLM Models

```python
# Modify Intent Planner to support other models
class IntentPlanner:
    def __init__(self, model_config):
        if model_config["provider"] == "zhipuai":
            self.client = ZhipuAI(api_key=model_config["api_key"])
        elif model_config["provider"] == "openai":
            self.client = OpenAI(api_key=model_config["api_key"])
        # ... other models
    
    def plan(self, user_input, device_capabilities):
        # Unified interface, supports multiple models
        pass
```

#### 8.8.2 Custom Dialog Strategy

```python
# Modify Dialog Manager to implement custom strategy
class CustomDialogManager(DialogManager):
    def handle_user_input(self, user_input):
        # Custom processing logic
        context = self.get_context()
        intent = self.intent_planner.plan(user_input, context)
        # ... custom logic
```

### 8.9 Best Practices

1. **Security Protection**:
   - Do not hardcode API Key in code
   - Use environment variables to store sensitive information
   - Validate user input to prevent injection attacks

2. **Error Handling**:
   - Catch API call exceptions
   - Provide friendly error messages
   - Implement retry mechanism

3. **User Experience**:
   - Maintain coherent dialog context
   - Provide clear operation feedback
   - Support natural interruption and recovery

4. **Performance Monitoring**:
   - Record API call latency
   - Track Token consumption
   - Monitor task execution success rate

---

## 9. Development Guide

### 9.1 Adding New Devices

#### Step 1: Create Device Firmware

1. **Copy Existing Device Code**
   ```bash
   cp -r "Device Unit code/esp8266_airconditioner_unit" \
         "Device Unit code/esp8266_new_device"
   ```

2. **Modify Device ID**
   ```cpp
   // config.h
   #define DEVICE_ID "A1_new_device"
   ```

3. **Add Sensor Code**
   - Add library according to sensor type
   - Implement data collection function
   - Update JSON data format

4. **Upload to ESP8266**

#### Step 2: Update Gateway Configuration

1. **Add Device to Allowed List**
   - Add in database server
   - Test mode: Modify default list in `gate_test.py`

   ```python
   # gate_test.py:142
   return ["A1_tem_hum", "A1_curtain", "A1_security", "A1_new_device"]
   ```

2. **Restart Gateway**

#### Step 3: Test New Device

```bash
# Test using device simulator
python Python/scripts/simulator_device.py
```

### 9.2 Adding New Sensors

#### Adding Sensors on Device Side

1. **Include Sensor Library**
   ```cpp
   #include <SensorLibrary.h>
   ```

2. **Initialize Sensor**
   ```cpp
   Sensor sensor(SENSOR_PIN);
   void setup() {
     sensor.begin();
   }
   ```

3. **Collect Data**
   ```cpp
   float getSensorData() {
     return sensor.read();
   }
   ```

4. **Add to JSON Data**
   ```cpp
   void sendMsgToGate() {
     StaticJsonDocument<200> msg;
     msg["device_id"] = device_id;
     msg["NewSensor"] = getSensorData();
     // ...
   }
   ```

#### Adding Fields on Gateway Side

1. **Define Field Constants**
   ```python
   # common/constants.py
   FIELD_NEW_SENSOR = "NewSensor"
   
   DEFAULT_SENSOR_DATA = {
       # ...
       FIELD_NEW_SENSOR: 0.0,
   }
   ```

2. **Update Database Table**
   ```sql
   ALTER TABLE gate_local_data
   ADD COLUMN new_sensor FLOAT(5) NULL;
   ```

### 9.3 Adding New Control Commands

#### Adding Commands on Android Side

1. **Add Button UI**
   ```xml
   <Button
       android:id="@+id/btn_new_control"
       android:layout_width="wrap_content"
       android:layout_height="wrap_content"
       android:text="New Control" />
   ```

2. **Add Click Event**
   ```java
   btnNewControl.setOnClickListener(v -> {
       sendControl("new_control_op", "1");
   });
   ```

3. **Send Command**
   ```java
   void sendControl(String op, String data) {
       JSONObject json = new JSONObject();
       json.put("op", op);
       json.put("data", data);
       json.put("status", "1");
       // Send to gateway...
   }
   ```

#### Adding Processing on Gateway Side

1. **Add Operation Code Processing**
   ```python
   # android_handler.py
   elif operation == "new_control_op":
       # Handle new command
       logger.info("Received new control command: %s", operation_value)
       # Update status or threshold
   ```

#### Adding Control on Device Side

1. **Receive Control Data**
   ```cpp
   void getMsgFromGate() {
       if(client.available()){
           StaticJsonDocument<200> msg;
           String jsonStr = client.readStringUntil('\n');
           deserializeJson(msg, jsonStr);
           
           // Receive new control field
           int newControl = msg["NewControl"];
           Serial.println("RECV:" + jsonStr);
       }
   }
   ```

2. **Execute Control**
   ```cpp
   void controlDevice() {
       if(newControl == 1) {
           digitalWrite(NEW_PIN, HIGH);
       } else {
           digitalWrite(NEW_PIN, LOW);
       }
   }
   ```

### 9.4 Modifying Communication Frequency

#### Modifying Device Send Frequency

```cpp
// config.h
#define SEND_INTERVAL 3  // Change to 3 seconds

// Or modify in code
SendTicker.attach(SEND_INTERVAL, sendMsgToGate);
```

#### Modifying Gateway Receive Frequency

```python
# common/constants.py
SENSOR_RECV_INTERVAL = 3  # Change to 3 seconds
SENSOR_SEND_INTERVAL = 3
```

#### Modifying Android Receive Frequency

```python
# common/constants.py
ANDROID_SEND_INTERVAL = 3  # Change to 3 seconds
```

### 9.5 Debugging Tips

#### Python Gateway Debugging

1. **Enable Verbose Logging**
   ```python
   # log_setup.py
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **View Log Files**
   ```bash
   tail -f Python/Gate/gate.log
   ```

3. **Use Test Mode**
   ```bash
   python gate_test.py --test
   ```

#### Device Side Debugging

1. **Use Serial Monitor**
   - Baud rate: 115200
   - Observe output information

2. **Add Debug Output**
   ```cpp
   Serial.println("Debug: current value = " + String(value));
   ```

#### Android Side Debugging

1. **View Logcat**
   ```bash
   adb logcat | grep MyApplication
   ```

2. **Add Logs**
   ```java
   Log.d("MyTag", "Debug message");
   ```

---

## 10. API Reference

### 10.1 Python Gateway API

#### Core Modules

##### gateway_state.py

```python
class GatewayState:
    """Gateway shared state management"""
    
    def __init__(self):
        """Initialize state"""
        
    def update_data(self, data: dict) -> None:
        """Update sensor data"""
        
    def set_threshold(self, field: str, value) -> None:
        """Set threshold"""
        
    def get_data_snapshot(self) -> dict:
        """Get data snapshot"""
        
    def is_device_permitted(self, device_id: str) -> bool:
        """Check if device is allowed to connect"""
```

##### sensor_handler.py

```python
def sensor_handler(gate_config, state: GatewayState) -> None:
    """Device node communication main listening thread"""
    
def sensor_client_handler(cs: socket.socket, state: GatewayState) -> None:
    """Handle connection of single device node"""
```

##### android_handler.py

```python
class AndroidHandler:
    """Mobile application communication handler"""
    
    def __init__(self, db_socket: socket.socket, config_dir):
        """Initialize handler"""
        
    def android_handler(self, gate_network_config, state: GatewayState) -> None:
        """Mobile application communication main listening thread"""
```

##### database.py

```python
def init_gate_database(db_config: GateDbConfig) -> MySQLConnection:
    """Initialize gateway local database"""
    
def save_sensor_data(conn: MySQLConnection, data: dict) -> None:
    """Save sensor data to local database"""
```

#### Communication Protocol API

```python
from common.protocol import send_json, recv_json, send_line, recv_line

def send_json(sock: socket.socket, obj: Any) -> None:
    """Send JSON data"""
    
def recv_json(sock: socket.socket, bufsize: int = 4096) -> Any:
    """Receive JSON data"""
    
def send_line(sock: socket.socket, message: str) -> None:
    """Send text line"""
    
def recv_line(sock: socket.socket, bufsize: int = 4096) -> str:
    """Receive text line"""
```

### 10.2 Device Side API

#### Core Functions

```cpp
// WiFi initialization
void wifiInit(const char *ssid, const char *password);

// Door access listening
void listen_door_secur_access();

// Send data to gateway
void sendMsgToGate();

// Receive data from gateway
void getMsgFromGate();

// Control device
void controlDevice();

// Temperature and humidity collection
void getTemperature_Humidity();

// Light status acquisition
void getLightStatus();
```

#### Configuration Macros

```cpp
#define DEVICE_ID "A1_tem_hum"
#define GATEWAY_IP "192.168.1.107"
#define GATEWAY_PORT 9300
#define WIFI_SSID "your_wifi_ssid"
#define WIFI_PASSWORD "your_wifi_password"

// Sensor configuration
#define DHT_PIN D7
#define DHT_TYPE DHT11
#define LED_PIN D6
#define SEND_INTERVAL 3
#define RECV_INTERVAL 3
```

### 10.3 Android Side API

#### Network Communication

```java
public class GatewayClient {
    // Connect to gateway
    public boolean connect(String ip, int port);
    
    // Send login request
    public boolean login(String username, String password);
    
    // Send control command
    public void sendControl(String operation, String data);
    
    // Receive sensor data
    public JSONObject receiveSensorData();
    
    // Disconnect
    public void disconnect();
}
```

#### Configuration Management

```java
public class ConfigManager {
    // Read configuration
    public Properties loadConfig(Context context);
    
    // Save configuration
    public void saveConfig(Context context, String ip, int port);
}
```

---

## 11. Troubleshooting

### 11.1 Common Issues

#### Gateway Cannot Start

**Symptom**: Python script fails to run

**Possible Causes**:
1. Port occupied
2. Configuration file error
3. Database connection failed

**Solution**:
```bash
# Check port occupation
netstat -ano | findstr "9300"
netstat -ano | findstr "9301"

# Check configuration file
cat Python/Gate/GateConfig.txt

# Check database connection
mysql -u root -p1234 -e "USE gate_database; SELECT * FROM gate_local_data LIMIT 1;"
```

#### Device Cannot Connect to Gateway

**Symptom**: ESP8266 displays "Gateway connection failed"

**Possible Causes**:
1. WiFi connection failed
2. Gateway IP error
3. Port error
4. Gateway not started

**Solution**:
```cpp
// Check WiFi connection
Serial.print("WiFi status: ");
Serial.println(WiFi.status());  // WL_CONNECTED = 3

// Check gateway IP
Serial.print("Gateway IP: ");
Serial.println(GATEWAY_IP);

// Check port
Serial.print("Gateway port: ");
Serial.println(GATEWAY_PORT);
```

#### Android Cannot Connect to Gateway

**Symptom**: Connection timeout or connection refused

**Possible Causes**:
1. Network not reachable
2. IP or port error
3. Gateway not started
4. Firewall blocking

**Solution**:
```bash
# Test network connectivity
ping 192.168.1.107

# Test if port is open
telnet 192.168.1.107 9301

# Check firewall
# Windows
netsh advfirewall firewall show rule name=all

# Linux
sudo iptables -L
```

#### Database Connection Failed

**Symptom**: "Database connection failed" error

**Possible Causes**:
1. MySQL service not started
2. Username or password error
3. Database does not exist

**Solution**:
```bash
# Check MySQL service
# Windows
sc query MySQL

# Linux
sudo systemctl status mysql

# Test connection
mysql -u root -p1234 -e "SHOW DATABASES;"

# Create database
mysql -u root -p1234 -e "CREATE DATABASE IF NOT EXISTS gate_database;"
```

### 11.2 Log Analysis

#### Gateway Log Locations

```
Python/Gate/gate.log
Python/Gate/gate_test.log
```

#### Key Log Information

**Device Connection**:
```
INFO Device node communication port opened: 192.168.1.107:9300
INFO Device node connected: ('192.168.1.108', 12345)
INFO Device node 'A1_tem_hum' connected to gateway
```

**Android Connection**:
```
INFO Mobile application communication port opened: 192.168.1.107:9301
INFO Mobile application connected: ('192.168.1.109', 54321)
INFO User 'Jiang' logged in successfully
```

**Error Logs**:
```
ERROR Device node receive data connection disconnected: [Errno 10054] An existing connection was forcibly closed by the remote host
ERROR Mobile application send connection disconnected: [Errno 10053] An established connection was aborted by the software in your host
ERROR JSON parsing failed: Expecting property name enclosed in double quotes
```

### 11.3 Debugging Tools

#### Integration Testing Tool

```bash
# Run integration tests
python Python/scripts/run_integration_test.py
```

#### Health Check Tool

```bash
# Run health check
python Python/scripts/health_check.py
```

#### Device Simulator

```bash
# Simulate device connection
python Python/scripts/simulator_device.py

# Simulate Android connection
python Python/scripts/simulator_android.py
```

---

## 12. Appendix

### 12.1 Configuration File Templates

#### GateConfig.txt Template

```
192.168.1.107
192.168.1.107
9300
9301
9302
root
1234
gate_database
```

#### UserConfig.txt Template

```
Jiang
pwd
A1
```

#### config.h Template

```cpp
#ifndef CONFIG_H
#define CONFIG_H

// Device configuration
#define DEVICE_ID "A1_tem_hum"
#define GATEWAY_IP "192.168.1.107"
#define GATEWAY_PORT 9300

// WiFi configuration
#define WIFI_SSID "your_wifi_ssid"
#define WIFI_PASSWORD "your_wifi_password"

// Sensor configuration
#define DHT_PIN D7
#define DHT_TYPE DHT11
#define LED_PIN D6

// Communication interval (seconds)
#define SEND_INTERVAL 3
#define RECV_INTERVAL 3

// OLED configuration
#define OLED_SDA_PIN D2
#define OLED_SCL_PIN D1
#define OLED_RESET_PIN -1

#endif
```

### 12.2 Database Table Structure

#### gate_local_data Table

```sql
CREATE TABLE IF NOT EXISTS `gate_local_data` (
  `timestamp` datetime NOT NULL,
  `light_th` int NULL,
  `temperature` float(5) NULL,
  `humidity` float(5) NULL,
  `light_cu` int NULL,
  `brightness` float(5) NULL,
  `curtain_status` int NULL
);
```

### 12.3 Constant Definitions

```python
# common/constants.py

# TCP ports
PORT_SENSOR = 9300
PORT_ANDROID = 9301
PORT_DB_SERVER = 9302

# Message terminator
MSG_TERMINATOR = "\n"

# Buffer size
BUFFER_SIZE_SMALL = 1024
BUFFER_SIZE_MEDIUM = 10240
BUFFER_SIZE_LARGE = 4096

# Listen queue length
LISTEN_BACKLOG = 128

# Database
DB_HOST = "localhost"
DB_PORT = 3306

# Communication interval (seconds)
SENSOR_SEND_INTERVAL = 3
SENSOR_RECV_INTERVAL = 3
ANDROID_SEND_INTERVAL = 3
ANDROID_RECV_INTERVAL = 3
ALIYUN_UPLOAD_INTERVAL = 5

# MQTT port
ALIYUN_MQTT_PORT = 1883

# Door access status
DOOR_DENIED = 0
DOOR_GRANTED = 1

# Data fields
FIELD_DOOR_CARD_ID = "Door_Secur_Card_id"
FIELD_DOOR_STATUS = "Door_Security_Status"
FIELD_LIGHT_TH = "Light_TH"
FIELD_TEMPERATURE = "Temperature"
FIELD_HUMIDITY = "Humidity"
FIELD_LIGHT_CU = "Light_CU"
FIELD_BRIGHTNESS = "Brightness"
FIELD_CURTAIN_STATUS = "Curtain_status"
FIELD_DEVICE_KEY = "device_key"

# Default data
DEFAULT_SENSOR_DATA = {
    FIELD_DOOR_CARD_ID: "",
    FIELD_DOOR_STATUS: 0,
    FIELD_LIGHT_TH: 0,
    FIELD_TEMPERATURE: 0,
    FIELD_HUMIDITY: 0,
    FIELD_LIGHT_CU: 0,
    FIELD_BRIGHTNESS: 0,
    FIELD_CURTAIN_STATUS: 1,
}

DEFAULT_THRESHOLD_DATA = {
    FIELD_LIGHT_TH: 0,
    FIELD_TEMPERATURE: 30.0,
    FIELD_HUMIDITY: 65.0,
    FIELD_BRIGHTNESS: 500.0,
}
```

### 12.4 Related Documents

- [README.md](README.md) - Project Overview
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment Guide
- [GATEWAY_TEST_REPORT.md](GATEWAY_TEST_REPORT.md) - Test Report
- [OPTIMIZATION_REPORT.md](OPTIMIZATION_REPORT.md) - Optimization Report

### 12.5 Technical Support

**Issue Reporting**: Submit issues to the project repository  
**Documentation Updates**: Regularly update developer documentation  
**Version Release**: Follow semantic versioning specification

---

**Document Version**: v1.0  
**Last Updated**: April 6, 2026  
**Maintainer**: PandaKing
