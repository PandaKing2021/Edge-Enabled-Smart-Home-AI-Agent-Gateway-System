/**
 * IoT 设备配置文件 - 智能空调单元（温湿度传感器）
 *
 * 此文件由 generate_device_config.py 自动生成
 * 请不要手动修改，如需修改请编辑 generate_device_config.py
 *
 * 生成时间: 2026-04-06 12:45:09
 */

#ifndef CONFIG_H
#define CONFIG_H

// ========================================
// WiFi 网络配置
// ========================================
#define WIFI_SSID           "3-205/E404"
#define WIFI_PASSWORD       "ieqyydxq2021"

// ========================================
// 网关服务器配置
// ========================================
#define GATEWAY_IP          "192.168.1.107"
#define GATEWAY_PORT        9300

// ========================================
// 设备身份配置
// ========================================
#define DEVICE_ID           "A1_tem_hum"

// ========================================
// 通信间隔配置（秒）
// ========================================
#define SEND_INTERVAL       3
#define RECV_INTERVAL       3

// ========================================
// 硬件引脚配置
// ========================================
// OLED 显示屏
#define OLED_SDA_PIN        D1
#define OLED_SCL_PIN        D2
#define OLED_RESET_PIN      -1

// LED指示灯
#define LED_PIN             LED_BUILTIN

// 温湿度传感器（空调单元专用）
#define DHT_PIN             D5
#define DHT_TYPE            DHT11

#endif // CONFIG_H
