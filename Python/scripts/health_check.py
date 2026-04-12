#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IoT 网关系统健康检查工具
检查配置文件、端口配置、依赖项等
"""

import sys
import socket
import os
from pathlib import Path
from typing import Dict, List, Tuple

# 设置控制台输出编码为UTF-8（Windows兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "Python"))

# ANSI 颜色代码
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class HealthChecker:
    """健康检查器"""

    def __init__(self):
        self.issues = []
        self.warnings = []
        self.successes = []

    def print_result(self, status: str, message: str) -> None:
        """打印检查结果

        Args:
            status: 状态 (success/warning/error)
            message: 消息
        """
        if status == "success":
            print(f"{Colors.GREEN}✓{Colors.RESET} {message}")
            self.successes.append(message)
        elif status == "warning":
            print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")
            self.warnings.append(message)
        elif status == "error":
            print(f"{Colors.RED}✗{Colors.RESET} {message}")
            self.issues.append(message)

    def check_config_files(self) -> None:
        """检查配置文件"""
        print(f"\n{Colors.BOLD}📁 配置文件检查{Colors.RESET}")
        print("-" * 50)

        # 检查 Python 网关配置
        gate_config_path = PROJECT_ROOT / "Python/Gate/GateConfig.txt"
        if gate_config_path.exists():
            try:
                from common.config import load_gate_config
                config = load_gate_config(gate_config_path.parent)
                self.print_result("success", f"网关配置文件存在且格式正确")
                self.print_result("success", f"  网关IP: {config.gate_network.ip}")
                self.print_result("success", f"  设备端口: {config.gate_network.source_port}")
                self.print_result("success", f"  Android端口: {config.gate_network.android_port}")
                self.print_result("success", f"  数据库服务器: {config.db_server.ip}:{config.db_server.db_server_port}")
            except Exception as e:
                self.print_result("error", f"网关配置文件格式错误: {e}")
        else:
            self.print_result("error", f"网关配置文件不存在: {gate_config_path}")

        # 检查 Android 配置
        android_config_path = PROJECT_ROOT / "Android IoT APP/app/src/main/assets/config.properties"
        if android_config_path.exists():
            with open(android_config_path, 'r') as f:
                lines = f.readlines()
                config_dict = {}
                for line in lines:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        config_dict[key.strip()] = value.strip()

                android_ip = config_dict.get('ip', '')
                android_port = config_dict.get('port', '')

                if android_ip and android_port:
                    self.print_result("success", f"Android配置文件存在")
                    self.print_result("success", f"  IP: {android_ip}")
                    self.print_result("success", f"  端口: {android_port}")

                    # 检查端口是否与网关配置一致
                    if config.gate_network.android_port == int(android_port):
                        self.print_result("success", f"  ✓ Android端口与网关配置一致")
                    else:
                        self.print_result("error", f"  ✗ Android端口({android_port})与网关配置({config.gate_network.android_port})不一致")
                else:
                    self.print_result("error", f"Android配置文件缺少必要配置")
        else:
            self.print_result("error", f"Android配置文件不存在: {android_config_path}")

    def check_device_configs(self) -> None:
        """检查设备单元配置"""
        print(f"\n{Colors.BOLD}🔧 设备单元配置检查{Colors.RESET}")
        print("-" * 50)

        device_units = [
            ("空调单元", PROJECT_ROOT / "Device Unit code/esp8266_airconditioner_unit/esp8266_airconditioner_unit.ino", "A1_tem_hum"),
            ("窗帘单元", PROJECT_ROOT / "Device Unit code/esp8266_curtain_unit/esp8266_curtain_unit.ino", "A1_curtain"),
        ]

        for name, ino_path, expected_device_id in device_units:
            if ino_path.exists():
                with open(ino_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查是否包含正确的配置文件引用
                if '#include "config.h"' in content:
                    self.print_result("success", f"{name}使用配置文件")

                    # 检查config.h是否存在并读取
                    config_h_path = ino_path.parent / "config.h"
                    if config_h_path.exists():
                        self.print_result("success", f"  config.h存在")

                        # 读取config.h内容
                        with open(config_h_path, 'r', encoding='utf-8') as cf:
                            config_content = cf.read()

                        # 从config.h中提取网关IP
                        if '#define GATEWAY_IP' in config_content:
                            import re
                            ip_match = re.search(r'#define GATEWAY_IP\s+"([^"]+)"', config_content)
                            if ip_match:
                                gateway_ip = ip_match.group(1)
                                self.print_result("success", f"  网关IP: {gateway_ip}")
                            else:
                                self.print_result("warning", f"  无法从config.h读取网关IP")

                        # 从config.h中提取网关端口
                        if '#define GATEWAY_PORT' in config_content:
                            import re
                            port_match = re.search(r'#define GATEWAY_PORT\s+(\d+)', config_content)
                            if port_match:
                                gateway_port = port_match.group(1)
                                self.print_result("success", f"  网关端口: {gateway_port}")
                            else:
                                self.print_result("warning", f"  无法从config.h读取网关端口")
                    else:
                        self.print_result("warning", f"  config.h不存在，请运行配置生成器")

                    # 检查是否使用旧的硬编码方式
                    if 'const char* ssid' in content and 'const char* password' in content:
                        self.print_result("warning", f"  代码中仍有硬编码的WiFi配置，建议使用配置文件")
                else:
                    self.print_result("warning", f"{name}未使用配置文件，建议升级")

                # 检查设备ID
                if expected_device_id in content:
                    self.print_result("success", f"  设备ID: {expected_device_id}")
            else:
                self.print_result("error", f"{name}代码文件不存在")

    def check_port_consistency(self) -> None:
        """检查端口配置一致性"""
        print(f"\n{Colors.BOLD}🔌 端口配置一致性检查{Colors.RESET}")
        print("-" * 50)

        # 预期的端口配置
        expected_ports = {
            "设备单元端口": 9300,
            "Android端口": 9301,
            "数据库服务器端口": 9302,
        }

        self.print_result("success", f"预期端口配置:")
        for name, port in expected_ports.items():
            self.print_result("success", f"  {name}: {port}")

    def check_dependencies(self) -> None:
        """检查Python依赖"""
        print(f"\n{Colors.BOLD}📦 Python依赖检查{Colors.RESET}")
        print("-" * 50)

        try:
            import json
            self.print_result("success", "json")
        except ImportError:
            self.print_result("error", "json 缺失")

        try:
            import socket
            self.print_result("success", "socket")
        except ImportError:
            self.print_result("error", "socket 缺失")

        try:
            import threading
            self.print_result("success", "threading")
        except ImportError:
            self.print_result("error", "threading 缺失")

        # 检查requirements.txt
        requirements_path = PROJECT_ROOT / "Python/requirements.txt"
        if requirements_path.exists():
            self.print_result("success", f"requirements.txt存在")
        else:
            self.print_result("warning", f"requirements.txt不存在")

    def check_network_connectivity(self) -> None:
        """检查网络连通性"""
        print(f"\n{Colors.BOLD}🌐 网络连通性检查{Colors.RESET}")
        print("-" * 50)

        try:
            from common.config import load_gate_config
            config = load_gate_config(PROJECT_ROOT / "Python/Gate")

            # 检查本地端口是否可监听
            ports_to_check = [
                config.gate_network.source_port,
                config.gate_network.android_port,
            ]

            for port in ports_to_check:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.bind(('0.0.0.0', 0))  # 测试绑定任意端口
                    self.print_result("success", f"端口 {port} 可用")
                except Exception as e:
                    self.print_result("error", f"端口 {port} 不可用: {e}")

        except Exception as e:
            self.print_result("error", f"无法加载配置: {e}")

    def print_summary(self) -> None:
        """打印检查摘要"""
        print(f"\n{Colors.BOLD}📊 检查摘要{Colors.RESET}")
        print("=" * 50)
        print(f"{Colors.GREEN}成功: {len(self.successes)}{Colors.RESET}")
        print(f"{Colors.YELLOW}警告: {len(self.warnings)}{Colors.RESET}")
        print(f"{Colors.RED}错误: {len(self.issues)}{Colors.RESET}")

        if self.issues:
            print(f"\n{Colors.RED}需要修复的问题:{Colors.RESET}")
            for issue in self.issues:
                print(f"  • {issue}")

        if self.warnings:
            print(f"\n{Colors.YELLOW}建议改进:{Colors.RESET}")
            for warning in self.warnings:
                print(f"  • {warning}")

        if not self.issues and not self.warnings:
            print(f"\n{Colors.GREEN}✓ 所有检查通过！系统配置良好。{Colors.RESET}")

    def run(self) -> None:
        """运行所有检查"""
        print(f"{Colors.BOLD}IoT 网关系统健康检查{Colors.RESET}")
        print("=" * 60)

        self.check_config_files()
        self.check_device_configs()
        self.check_port_consistency()
        self.check_dependencies()
        self.check_network_connectivity()
        self.print_summary()


def main():
    """主函数"""
    checker = HealthChecker()
    checker.run()


if __name__ == "__main__":
    main()
