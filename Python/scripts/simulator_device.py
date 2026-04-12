#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备单元模拟器
用于测试网关的设备通信功能
"""

import socket
import json
import threading
import time
import sys

# 设置编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class DeviceSimulator:
    """设备单元模拟器"""

    def __init__(self, device_id, host='192.168.1.107', port=9300):
        self.device_id = device_id
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.running = True

        # 传感器数据
        self.sensor_data = {
            "device_id": device_id,
            "Light_TH": 0,
            "Temperature": 25.0,
            "Humidity": 60.0,
            "Light_CU": 0,
            "Brightness": 500.0,
            "Curtain_status": 1
        }

    def connect(self):
        """连接到网关"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))

            # 发送设备ID
            self.socket.sendall((self.device_id + "\n").encode('utf-8'))

            # 等待网关响应
            response = self.socket.recv(1024).decode('utf-8').strip()
            if response == "start":
                self.connected = True
                print(f"✓ 设备 {self.device_id} 已连接到网关 {self.host}:{self.port}")
                return True
            else:
                print(f"✗ 网关响应异常: {response}")
                return False

        except Exception as e:
            print(f"✗ 连接失败: {e}")
            return False

    def start_communication(self):
        """启动通信线程"""
        receive_thread = threading.Thread(target=self._receive_data, daemon=True)
        send_thread = threading.Thread(target=self._send_data, daemon=True)

        receive_thread.start()
        send_thread.start()

        return receive_thread, send_thread

    def _send_data(self):
        """发送传感器数据线程"""
        while self.running and self.connected:
            try:
                self.socket.sendall((json.dumps(self.sensor_data, ensure_ascii=False) + "\n").encode('utf-8'))
                print(f"📤 设备 {self.device_id} 发送数据: {self.sensor_data}")

                # 更新模拟数据
                self._update_sensor_data()

                time.sleep(3)  # 3秒发送间隔
            except Exception as e:
                if self.running:
                    print(f"✗ 发送数据失败: {e}")
                break

    def _receive_data(self):
        """接收控制指令线程"""
        self.socket.settimeout(5)
        while self.running and self.connected:
            try:
                chunks = []
                while True:
                    chunk = self.socket.recv(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    data = b''.join(chunks)
                    if b'\n' in data:
                        line = data[:data.index(b'\n')]
                        control_data = json.loads(line.decode('utf-8'))
                        self._process_control(control_data)
                        break
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"✗ 接收数据失败: {e}")
                break

    def _process_control(self, control_data):
        """处理控制指令"""
        print(f"📥 设备 {self.device_id} 接收控制: {control_data}")

        # 根据设备类型处理控制指令
        if "Temperature" in control_data:
            self.sensor_data["Temperature"] = control_data["Temperature"]

        if "Humidity" in control_data:
            self.sensor_data["Humidity"] = control_data["Humidity"]

        if "Light_TH" in control_data:
            self.sensor_data["Light_TH"] = control_data["Light_TH"]
            print(f"💡 空调灯状态: {'开' if control_data['Light_TH'] == 1 else '关'}")

        if "Light_CU" in control_data:
            self.sensor_data["Light_CU"] = control_data["Light_CU"]

        if "Brightness" in control_data:
            self.sensor_data["Brightness"] = control_data["Brightness"]

        if "Curtain_status" in control_data:
            self.sensor_data["Curtain_status"] = control_data["Curtain_status"]
            print(f"🪟 窗帘状态: {'开' if control_data['Curtain_status'] == 1 else '关'}")

    def _update_sensor_data(self):
        """更新模拟传感器数据"""
        import random

        # 温度波动
        temp_change = random.uniform(-0.5, 0.5)
        self.sensor_data["Temperature"] = max(15, min(35, self.sensor_data["Temperature"] + temp_change))

        # 湿度波动
        hum_change = random.uniform(-2, 2)
        self.sensor_data["Humidity"] = max(30, min(90, self.sensor_data["Humidity"] + hum_change))

        # 光照度波动
        if self.device_id == "A1_curtain":
            bright_change = random.uniform(-50, 50)
            self.sensor_data["Brightness"] = max(100, min(1000, self.sensor_data["Brightness"] + bright_change))

    def close(self):
        """关闭连接"""
        self.running = False
        if self.socket:
            self.socket.close()
            self.connected = False
            print(f"✓ 设备 {self.device_id} 已断开连接")


def test_airconditioner_scenario():
    """测试空调设备场景"""
    print("\n" + "="*60)
    print("测试场景: 智能空调设备连接")
    print("="*60)

    device = DeviceSimulator("A1_tem_hum")
    if not device.connect():
        return False

    receive_thread, send_thread = device.start_communication()

    # 运行15秒
    time.sleep(15)

    device.close()
    return True


def test_curtain_scenario():
    """测试窗帘设备场景"""
    print("\n" + "="*60)
    print("测试场景: 智能窗帘设备连接")
    print("="*60)

    device = DeviceSimulator("A1_curtain")
    if not device.connect():
        return False

    receive_thread, send_thread = device.start_communication()

    # 运行15秒
    time.sleep(15)

    device.close()
    return True


def test_multiple_devices():
    """测试多设备同时连接场景"""
    print("\n" + "="*60)
    print("测试场景: 多设备同时连接")
    print("="*60)

    devices = []

    # 创建并连接多个设备
    for device_id in ["A1_tem_hum", "A1_curtain", "A1_security"]:
        device = DeviceSimulator(device_id)
        if device.connect():
            device.start_communication()
            devices.append(device)
        else:
            print(f"✗ 设备 {device_id} 连接失败")

    # 运行20秒
    time.sleep(20)

    # 关闭所有设备
    for device in devices:
        device.close()

    return len(devices) > 0


def main():
    """主函数"""
    print("\n" + "="*60)
    print("设备单元模拟器 - 网关测试工具")
    print("="*60)

    # 测试单个设备
    ac_success = test_airconditioner_scenario()
    time.sleep(2)

    curtain_success = test_curtain_scenario()
    time.sleep(2)

    # 测试多设备
    multi_success = test_multiple_devices()

    print("\n" + "="*60)
    print("测试结果摘要")
    print("="*60)
    print(f"空调设备测试: {'✓ 通过' if ac_success else '✗ 失败'}")
    print(f"窗帘设备测试: {'✓ 通过' if curtain_success else '✗ 失败'}")
    print(f"多设备测试: {'✓ 通过' if multi_success else '✗ 失败'}")


if __name__ == "__main__":
    main()
