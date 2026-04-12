#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备单元配置生成器
用于根据统一配置模板生成各个设备的配置文件
"""

import sys
import os
from pathlib import Path

# 设置控制台输出编码为UTF-8（Windows兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 统一配置
UNIFIED_CONFIG = {
    "wifi": {
        "ssid": "3-205/E404",
        "password": "ieqyydxq2021"
    },
    "gateway": {
        "ip": "192.168.1.107",
        "port": 9300
    },
    "communication": {
        "send_interval": 3,
        "recv_interval": 3
    }
}

# 设备特定配置
DEVICE_CONFIGS = {
    "airconditioner": {
        "device_id": "A1_tem_hum",
        "description": "智能空调单元（温湿度传感器）"
    },
    "curtain": {
        "device_id": "A1_curtain",
        "description": "智能窗帘单元（光照度传感器）"
    },
    "doorsecurity": {
        "device_id": "A1_security",
        "description": "智能门禁单元（RFID读卡器）"
    }
}

def generate_config_header(device_type: str, output_path: Path) -> None:
    """生成设备的配置头文件

    Args:
        device_type: 设备类型 (airconditioner/curtain/doorsecurity)
        output_path: 输出文件路径
    """
    if device_type not in DEVICE_CONFIGS:
        raise ValueError(f"未知设备类型: {device_type}")

    device_config = DEVICE_CONFIGS[device_type]

    config_content = f'''/**
 * IoT 设备配置文件 - {device_config['description']}
 *
 * 此文件由 generate_device_config.py 自动生成
 * 请不要手动修改，如需修改请编辑 generate_device_config.py
 *
 * 生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 */

#ifndef CONFIG_H
#define CONFIG_H

// ========================================
// WiFi 网络配置
// ========================================
#define WIFI_SSID           "{UNIFIED_CONFIG['wifi']['ssid']}"
#define WIFI_PASSWORD       "{UNIFIED_CONFIG['wifi']['password']}"

// ========================================
// 网关服务器配置
// ========================================
#define GATEWAY_IP          "{UNIFIED_CONFIG['gateway']['ip']}"
#define GATEWAY_PORT        {UNIFIED_CONFIG['gateway']['port']}

// ========================================
// 设备身份配置
// ========================================
#define DEVICE_ID           "{device_config['device_id']}"

// ========================================
// 通信间隔配置（秒）
// ========================================
#define SEND_INTERVAL       {UNIFIED_CONFIG['communication']['send_interval']}
#define RECV_INTERVAL       {UNIFIED_CONFIG['communication']['recv_interval']}

// ========================================
// 硬件引脚配置
// ========================================
// OLED 显示屏
#define OLED_SDA_PIN        D1
#define OLED_SCL_PIN        D2
#define OLED_RESET_PIN      -1

// LED指示灯
#define LED_PIN             LED_BUILTIN

'''

    # 根据设备类型添加特定配置
    if device_type == "airconditioner":
        config_content += '''// 温湿度传感器（空调单元专用）
#define DHT_PIN             D5
#define DHT_TYPE            DHT11

'''
    elif device_type == "curtain":
        config_content += '''// 光照度传感器（窗帘单元专用）
#define BH1750_ADDR         0x23

// 窗帘控制引脚（窗帘单元专用）
#define CURTAIN_PIN1        D3
#define CURTAIN_PIN2        D4

// 蜂鸣器（窗帘单元专用）
#define BUZZER_PIN          D5

'''
    elif device_type == "doorsecurity":
        config_content += '''// RFID读卡器（门禁单元专用）
#define SS_PIN              D3
#define RST_PIN             D4

'''
    else:
        raise ValueError(f"未知设备类型: {device_type}")

    config_content += '''#endif // CONFIG_H
'''

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(config_content)

    print(f"✓ 配置文件已生成: {output_path}")


def main():
    """主函数"""
    print("=" * 60)
    print("IoT 设备单元配置生成器")
    print("=" * 60)

    # 设备单元代码目录
    device_code_dir = Path(__file__).parent.parent.parent / "Device Unit code"

    # 生成各设备的配置文件
    for device_type, config in DEVICE_CONFIGS.items():
        print(f"\n正在生成 {config['description']} 配置...")

        # 确定输出目录
        if device_type == "airconditioner":
            output_dir = device_code_dir / "esp8266_airconditioner_unit"
        elif device_type == "curtain":
            output_dir = device_code_dir / "esp8266_curtain_unit"
        elif device_type == "doorsecurity":
            output_dir = device_code_dir / "esp8266_doorsecurity_unit"
        else:
            continue

        output_path = output_dir / "config.h"
        generate_config_header(device_type, output_path)

    print("\n" + "=" * 60)
    print("所有配置文件生成完成！")
    print("=" * 60)
    print("\n配置汇总:")
    print(f"  WiFi SSID: {UNIFIED_CONFIG['wifi']['ssid']}")
    print(f"  网关IP: {UNIFIED_CONFIG['gateway']['ip']}")
    print(f"  网关端口: {UNIFIED_CONFIG['gateway']['port']}")
    print(f"  通信间隔: 发送{UNIFIED_CONFIG['communication']['send_interval']}秒 / 接收{UNIFIED_CONFIG['communication']['recv_interval']}秒")
    print("\n如需修改配置，请编辑此文件中的 UNIFIED_CONFIG 字典，然后重新运行。")


if __name__ == "__main__":
    main()
