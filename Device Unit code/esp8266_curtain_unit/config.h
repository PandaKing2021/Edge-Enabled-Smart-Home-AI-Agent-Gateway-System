/**
 * IoT 设备配置文件 - 智能窗帘单元（光照度传感器）
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
#define DEVICE_ID           "A1_curtain"

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

// 光照度传感器（窗帘单元专用）
#define BH1750_ADDR         0x23

// 窗帘控制引脚（窗帘单元专用）
#define CURTAIN_PIN1        D3
#define CURTAIN_PIN2        D4

// 蜂鸣器（窗帘单元专用）
#define BUZZER_PIN          D5

#endif // CONFIG_H
