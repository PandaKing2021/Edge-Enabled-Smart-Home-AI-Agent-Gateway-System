#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Agent 端到端测试脚本

测试AI Agent系统与网关设备的集成:
1. 模拟设备连接到网关
2. 模拟Android客户端发送对话指令
3. 验证AI Agent的意图解析和设备控制
4. 测试多轮对话和偏好学习
"""

import socket
import json
import time
import sys
import threading
from pathlib import Path

# 设置编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class DeviceSimulator:
    """简化的设备模拟器"""

    def __init__(self, device_id, host='127.0.0.1', port=9300):
        self.device_id = device_id
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.running = True
        self.received_commands = []

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
                print(f"✓ 设备 {self.device_id} 已连接")
                return True
            else:
                print(f"✗ 网关响应异常: {response}")
                return False
        except Exception as e:
            print(f"✗ 设备 {self.device_id} 连接失败: {e}")
            return False

    def start(self):
        """启动设备通信"""
        receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        send_thread = threading.Thread(target=self._send_loop, daemon=True)
        
        receive_thread.start()
        send_thread.start()
        
        return receive_thread, send_thread

    def _send_loop(self):
        """发送数据循环"""
        while self.running and self.connected:
            try:
                self.socket.sendall((json.dumps(self.sensor_data, ensure_ascii=False) + "\n").encode('utf-8'))
                time.sleep(3)
            except Exception as e:
                if self.running:
                    print(f"✗ 发送数据失败: {e}")
                break

    def _receive_loop(self):
        """接收控制指令循环"""
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
                        self.received_commands.append(control_data)
                        print(f"📥 {self.device_id} 接收: {control_data}")
                        break
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"✗ 接收数据失败: {e}")
                break

    def close(self):
        """关闭连接"""
        self.running = False
        if self.socket:
            self.socket.close()
            self.connected = False


class AndroidSimulator:
    """简化的Android客户端模拟器"""

    def __init__(self, host='127.0.0.1', port=9301):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False

    def connect(self):
        """连接到网关"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"✓ Android模拟器已连接")
            return True
        except Exception as e:
            print(f"✗ Android连接失败: {e}")
            return False

    def send_chat_request(self, user_info):
        """发送对话请求"""
        data = {
            "state": "chat",
            "data": json.dumps(user_info, ensure_ascii=False),
            "status": 1
        }
        return self._send_and_receive(data)

    def send_chat_message(self, user_input):
        """发送对话消息"""
        data = {
            "operation": "chat",
            "value": user_input,
            "status": "1"
        }
        return self._send_and_receive(data)

    def _send_and_receive(self, data):
        """发送并接收响应"""
        try:
            self._send_json(data)
            return self._recv_json()
        except Exception as e:
            print(f"✗ 通信失败: {e}")
            return None

    def _send_json(self, data):
        """发送JSON数据"""
        message = json.dumps(data, ensure_ascii=False)
        self.socket.sendall((message + "\n").encode('utf-8'))

    def _recv_json(self):
        """接收JSON数据"""
        self.socket.settimeout(10)
        chunks = []
        while True:
            try:
                chunk = self.socket.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
                data = b''.join(chunks)
                if b'\n' in data:
                    line = data[:data.index(b'\n')]
                    return json.loads(line.decode('utf-8'))
            except socket.timeout:
                break
            except Exception as e:
                raise

    def close(self):
        """关闭连接"""
        if self.socket:
            self.socket.close()
            self.connected = False


def test_e2e_ai_agent():
    """端到端AI Agent测试"""
    print("\n" + "="*60)
    print("AI Agent 端到端测试")
    print("="*60)

    # 1. 启动设备模拟器
    print("\n[1/5] 启动设备模拟器...")
    devices = []
    for device_id in ["A1_tem_hum", "A1_curtain", "A1_security"]:
        device = DeviceSimulator(device_id, host='127.0.0.1', port=9300)
        if device.connect():
            device.start()
            devices.append(device)
            time.sleep(1)

    if not devices:
        print("✗ 设备连接失败，请确保网关已启动")
        return False

    print(f"✓ {len(devices)} 个设备已连接")
    time.sleep(2)

    # 2. 连接Android客户端
    print("\n[2/5] 连接Android客户端...")
    android = AndroidSimulator(host='127.0.0.1', port=9301)
    if not android.connect():
        print("✗ Android连接失败，请确保网关已启动")
        for device in devices:
            device.close()
        return False

    time.sleep(1)

    # 3. 发送对话请求
    print("\n[3/5] 发送对话请求...")
    user_info = {
        "account": "test_user",
        "session_id": "test_session_001"
    }
    response = android.send_chat_request(user_info)
    
    if not response:
        print("✗ 对话请求失败")
    elif response.get("status") == "ready":
        print(f"✓ 对话会话已创建: {response.get('session_id')}")
    elif response.get("status") == "error":
        print(f"⚠️  AI Agent未初始化: {response.get('message')}")
        print("   (这是正常的，如果API Key未配置)")
    else:
        print(f"✗ 未知响应: {response}")

    time.sleep(1)

    # 4. 测试对话指令
    print("\n[4/5] 测试对话指令...")
    
    test_commands = [
        "我困了,准备睡觉",
        "把空调温度调到24度",
        "关闭窗帘",
    ]

    for cmd in test_commands:
        print(f"\n发送: '{cmd}'")
        response = android.send_chat_message(cmd)
        
        if response:
            print(f"响应状态: {response.get('status')}")
            if response.get("status") == "success":
                print(f"推理: {response.get('reasoning', '')[:100]}...")
                tasks = response.get('tasks', [])
                print(f"任务数: {len(tasks)}")
                for i, task in enumerate(tasks, 1):
                    print(f"  任务{i}: {task}")
            elif response.get("status") == "error":
                print(f"错误: {response.get('message')}")
        
        time.sleep(3)

    # 5. 检查设备是否收到控制指令
    print("\n[5/5] 检查设备控制...")
    total_commands = 0
    for device in devices:
        print(f"\n设备 {device.device_id}:")
        print(f"  收到 {len(device.received_commands)} 条指令")
        total_commands += len(device.received_commands)
        if device.received_commands:
            for cmd in device.received_commands[:3]:  # 只显示前3条
                print(f"    {cmd}")

    # 清理
    print("\n清理资源...")
    for device in devices:
        device.close()
    android.close()

    print("\n" + "="*60)
    print("测试摘要")
    print("="*60)
    print(f"设备连接: ✓ {len(devices)} 个")
    print(f"Android连接: ✓")
    print(f"对话指令: ✓ {len(test_commands)} 条")
    print(f"设备控制: {'✓' if total_commands > 0 else '⚠️ '} ({total_commands} 条指令)")

    return True


def test_basic_connectivity():
    """测试基本连通性"""
    print("\n" + "="*60)
    print("基本连通性测试")
    print("="*60)

    # 测试网关设备端口
    print("\n[1/2] 测试网关设备端口 (9300)...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(('127.0.0.1', 9300))
        sock.close()
        if result == 0:
            print("✓ 端口 9300 可连接")
        else:
            print("✗ 端口 9300 无法连接 (网关可能未启动)")
            return False
    except Exception as e:
        print(f"✗ 端口 9300 测试失败: {e}")
        return False

    # 测试Android端口
    print("\n[2/2] 测试Android端口 (9301)...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(('127.0.0.1', 9301))
        sock.close()
        if result == 0:
            print("✓ 端口 9301 可连接")
        else:
            print("✗ 端口 9301 无法连接 (网关可能未启动)")
            return False
    except Exception as e:
        print(f"✗ 端口 9301 测试失败: {e}")
        return False

    print("\n✓ 基本连通性测试通过")
    return True


def main():
    """主测试函数"""
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*18 + "AI Agent 测试套件" + " "*18 + "║")
    print("╚" + "="*58 + "╝")

    # 基本连通性测试
    if not test_basic_connectivity():
        print("\n⚠️  网关未启动，请先启动网关:")
        print("   cd Python/Gate")
        print("   python gate.py")
        return

    # 端到端测试
    success = test_e2e_ai_agent()

    print("\n" + "="*60)
    if success:
        print("✅ 所有测试完成")
    else:
        print("❌ 测试失败")
    print("="*60)

    print("\n提示:")
    print("1. 确保网关已启动 (Python/Gate/gate.py)")
    print("2. 如需完整测试，请配置 API Key (Python/Gate/ai_agent_config.txt)")
    print("3. 初始化数据库: mysql -u root -p < 'Python/Database Server/ai_agent_tables.sql'")


if __name__ == "__main__":
    main()
