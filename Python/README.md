# IoT 智能网关系统

物联网(IoT)智能网关系统，采用网关-数据库服务器的双层架构，支持设备节点数据采集、移动端(Android)远程控制、以及阿里云 IoT 平台数据上传。

## 项目结构

```
Python/
├── MyComm.py                          # 网关与数据库服务器的通信协议编解码
├── requirements.txt                   # Python 依赖清单
├── common/                            # 公共模块
│   ├── config.py                      # 配置管理
│   ├── models.py                      # 线程安全状态模型
│   └── constants.py                   # 常量定义
├── Gate/                              # 网关程序
│   ├── gate.py                        # 网关主入口
│   ├── sensor_handler.py              # 设备节点通信
│   ├── android_handler.py             # 移动应用通信
│   ├── aliyun_handler.py              # 阿里云 IoT 通信
│   ├── database.py                    # 本地数据库操作
│   ├── GateConfig.txt                 # 网关配置文件
│   └── UserConfig.txt                 # 本地授权用户信息
└── Database Server/                   # 数据库服务器
    ├── database_process_server.py     # 数据库服务器主程序
    └── serverConfig.txt               # 服务器配置文件
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动数据库服务器

```bash
cd "Database Server"
python database_process_server.py
```

### 启动网关

```bash
cd Gate
python gate.py
```

## 通信协议

### 网关与数据库服务器

通信格式：`指令码|数据码|状态码`，通信单元分隔符 `|`

- 网关→服务器 存储新用户：`add_new_user|{username+password+deviceKey}|1`
- 服务器→网关 成功：`add_new_user|NULL|1`  失败：`add_new_user|NULL|0`
- 网关→服务器 检查用户配置：`check_userconfig_illegal|{username+password+deviceKey}|1`
- 网关→服务器 查询设备：`check_device_id|{deviceKey}|1`

### 网关与设备节点

- TCP 端口：3000
- 数据格式：JSON（设备→网关），Python dict str + `\n`（网关→设备）

### 网关与移动应用

- TCP 端口：3001
- 通信格式：`指令码|数据码|状态码`

## 配置文件

### GateConfig.txt（每行一个配置项）

```
网关IP
数据库服务器IP
设备节点通信端口
移动应用通信端口
数据库服务器端口
MySQL用户名
MySQL密码
数据库名
```

### UserConfig.txt（三行）

```
用户名
密码
设备密钥
```

### serverConfig.txt（两行）

```
数据库服务器IP
监听端口
```
