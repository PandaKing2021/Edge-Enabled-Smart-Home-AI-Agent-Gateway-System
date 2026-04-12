/**
 * IoT 设备单元统一配置模板
 * 
 * 使用说明：
 * 1. 复制此文件为 config.h
 * 2. 根据实际网络环境修改配置
 * 3. 上传到对应的ESP8266设备
 */

#ifndef CONFIG_H
#define CONFIG_H

// ========================================
// WiFi 网络配置
// ========================================
#define WIFI_SSID           "你的WiFi名称"
#define WIFI_PASSWORD       "你的WiFi密码"

// ========================================
// 网关服务器配置
// ========================================
#define GATEWAY_IP          "192.168.1.107"
#define GATEWAY_PORT        9300

// ========================================
// 设备身份配置
// ========================================
// 空调单元: "A1_tem_hum"
// 窗帘单元: "A1_curtain"
// 门禁单元: "A1_security"
#define DEVICE_ID           "A1_tem_hum"

// ========================================
// 通信间隔配置（秒）
// ========================================
#define SEND_INTERVAL       3
#define RECV_INTERVAL       3

// ========================================
// 硬件引脚配置（根据具体设备修改）
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

// 光照度传感器（窗帘单元专用）
#define BH1750_ADDR         0x23

// 窗帘控制引脚（窗帘单元专用）
#define CURTAIN_PIN1        D3
#define CURTAIN_PIN2        D4

// 蜂鸣器（窗帘单元专用）
#define BUZZER_PIN          D5

#endif // CONFIG_H
