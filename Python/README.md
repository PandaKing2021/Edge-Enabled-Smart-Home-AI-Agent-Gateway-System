# IoT Smart Gateway System

IoT smart gateway system, adopting a gateway-database server dual-layer architecture, supporting device node data collection, mobile terminal (Android) remote control, and Aliyun IoT platform data upload.

## Project Structure

```
Python/
├── MyComm.py                          # Gateway-database server communication protocol codec
├── requirements.txt                   # Python dependency list
├── common/                            # Common modules
│   ├── config.py                      # Configuration management
│   ├── models.py                      # Thread-safe state models
│   └── constants.py                   # Constant definitions
├── Gate/                              # Gateway program
│   ├── gate.py                        # Gateway main entry
│   ├── sensor_handler.py              # Device node communication
│   ├── android_handler.py             # Mobile application communication
│   ├── aliyun_handler.py              # Aliyun IoT communication
│   ├── database.py                    # Local database operations
│   ├── GateConfig.txt                 # Gateway configuration file
│   └── UserConfig.txt                 # Local authorized user information
└── Database Server/                   # Database server
    ├── database_process_server.py     # Database server main program
    └── serverConfig.txt               # Server configuration file
```

## Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Start Database Server

```bash
cd "Database Server"
python database_process_server.py
```

### Start Gateway

```bash
cd Gate
python gate.py
```

## Communication Protocol

### Gateway-Database Server

Communication format: `command code|data code|status code`, communication unit separator `|`

- Gateway→Server Store new user: `add_new_user|{username+password+deviceKey}|1`
- Server→Gateway Success: `add_new_user|NULL|1`  Failure: `add_new_user|NULL|0`
- Gateway→Server Check user config: `check_userconfig_illegal|{username+password+deviceKey}|1`
- Gateway→Server Query device: `check_device_id|{deviceKey}|1`

### Gateway-Device Node

- TCP Port: 3000
- Data format: JSON (device→gateway), Python dict str + `\n` (gateway→device)

### Gateway-Mobile Application

- TCP Port: 3001
- Communication format: `command code|data code|status code`

## Configuration Files

### GateConfig.txt (one configuration item per line)

```
Gateway IP
Database server IP
Device node communication port
Mobile application communication port
Database server port
MySQL username
MySQL password
Database name
```

### UserConfig.txt (three lines)

```
Username
Password
Device key
```

### serverConfig.txt (two lines)

```
Database server IP
Listening port
```
