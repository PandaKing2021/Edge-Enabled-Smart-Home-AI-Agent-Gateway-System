#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android客户端模拟器
用于测试网关的Android通信功能
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


class AndroidSimulator:
    """Android客户端模拟器"""

    def __init__(self, host='192.168.1.107', port=9301):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.running = True

    def connect(self):
        """连接到网关"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"✓ Android模拟器已连接到网关 {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"✗ 连接失败: {e}")
            return False

    def send_login(self, username, password):
        """发送登录请求"""
        login_data = {
            "op": "login",
            "data": json.dumps({
                "account": username,
                "password": password,
                "device_Key": "A1"
            }),
            "status": 1
        }

        try:
            self._send_json(login_data)
            response = self._recv_json()
            print(f"📱 登录响应: {response}")
            return response.get("status") == 1
        except Exception as e:
            print(f"✗ 登录失败: {e}")
            return False

    def send_register(self, username, password, device_key):
        """发送注册请求"""
        register_data = {
            "op": "register",
            "data": json.dumps({
                "account": username,
                "password": password,
                "device_Key": device_key
            }),
            "status": 1
        }

        try:
            self._send_json(register_data)
            response = self._recv_json()
            print(f"📱 注册响应: {response}")
            return response.get("status") == 1
        except Exception as e:
            print(f"✗ 注册失败: {e}")
            return False

    def send_control(self, operation, value=None):
        """发送控制指令"""
        control_data = {
            "op": operation,
            "data": str(value) if value is not None else "1",
            "status": "1"
        }

        try:
            self._send_json(control_data)
            print(f"📤 发送控制指令: {operation} = {value}")
        except Exception as e:
            print(f"✗ 发送控制指令失败: {e}")

    def start_receiving(self):
        """启动接收数据线程"""
        def receive_thread():
            while self.running and self.connected:
                try:
                    data = self._recv_json(timeout=5)
                    if data:
                        print(f"📥 接收数据: {data}")
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"✗ 接收数据错误: {e}")
                    break

        thread = threading.Thread(target=receive_thread, daemon=True)
        thread.start()
        return thread

    def _send_json(self, data):
        """发送JSON数据"""
        message = json.dumps(data, ensure_ascii=False)
        self.socket.sendall((message + "\n").encode('utf-8'))

    def _recv_json(self, timeout=None):
        """接收JSON数据"""
        self.socket.settimeout(timeout)
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
                raise
            except Exception as e:
                raise

    def close(self):
        """关闭连接"""
        self.running = False
        if self.socket:
            self.socket.close()
            self.connected = False
            print("✓ Android模拟器已断开连接")


def test_login_scenario():
    """测试登录场景"""
    print("\n" + "="*60)
    print("测试场景1: 用户登录")
    print("="*60)

    simulator = AndroidSimulator()
    if not simulator.connect():
        return False

    # 启动接收线程
    receive_thread = simulator.start_receiving()

    # 测试登录
    success = simulator.send_login("Jiang", "pwd")

    if success:
        print("✓ 登录成功")
    else:
        print("✗ 登录失败")

    # 等待接收一些数据
    time.sleep(5)

    # 发送一些控制指令
    simulator.send_control("light_th_open")
    time.sleep(1)
    simulator.send_control("change_temperature_threshold", 25)
    time.sleep(1)
    simulator.send_control("change_humidity_threshold", 60)
    time.sleep(1)
    simulator.send_control("curtain_open")
    time.sleep(1)
    simulator.send_control("light_th_close")

    # 等待接收更多数据
    time.sleep(5)

    simulator.close()
    return success


def test_register_scenario():
    """测试注册场景"""
    print("\n" + "="*60)
    print("测试场景2: 用户注册")
    print("="*60)

    simulator = AndroidSimulator()
    if not simulator.connect():
        return False

    # 测试注册
    success = simulator.send_register("test_user", "test_password", "A1_test")

    if success:
        print("✓ 注册成功")
    else:
        print("✗ 注册失败")

    simulator.close()
    return success


def main():
    """主函数"""
    print("\n" + "="*60)
    print("Android客户端模拟器 - 网关测试工具")
    print("="*60)

    # 测试登录场景
    login_success = test_login_scenario()

    # 测试注册场景
    register_success = test_register_scenario()

    print("\n" + "="*60)
    print("测试结果摘要")
    print("="*60)
    print(f"登录测试: {'✓ 通过' if login_success else '✗ 失败'}")
    print(f"注册测试: {'✓ 通过' if register_success else '✗ 失败'}")


if __name__ == "__main__":
    main()
