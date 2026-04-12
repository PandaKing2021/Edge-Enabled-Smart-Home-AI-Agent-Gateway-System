#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动测试工具
1. 启动网关（测试模式）
2. 询问用户选择测试类型
"""

import subprocess
import sys
import os

# 设置编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def print_menu():
    """打印菜单"""
    print("\n" + "="*60)
    print("IoT 网关测试菜单")
    print("="*60)
    print("1. 启动网关（测试模式）")
    print("2. 运行Android模拟器测试")
    print("3. 运行设备模拟器测试")
    print("4. 运行完整集成测试")
    print("0. 退出")
    print("="*60)


def start_gateway():
    """启动网关"""
    print("\n启动网关...")
    gate_script = "Python/Gate/gate_test.py"

    # 直接运行，不使用subprocess
    print("注意: 网关将在前台运行，按Ctrl+C停止")
    print("=============================================")
    os.execv(sys.executable, [sys.executable, gate_script, '--test'])


def run_android_test():
    """运行Android测试"""
    print("\n运行Android模拟器测试...")
    result = subprocess.run(
        [sys.executable, "Python/scripts/simulator_android.py"],
        cwd=os.getcwd(),
    )
    return result.returncode


def run_device_test():
    """运行设备测试"""
    print("\n运行设备模拟器测试...")
    result = subprocess.run(
        [sys.executable, "Python/scripts/simulator_device.py"],
        cwd=os.getcwd(),
    )
    return result.returncode


def run_integration_test():
    """运行集成测试"""
    print("\n运行集成测试...")
    result = subprocess.run(
        [sys.executable, "Python/scripts/run_integration_test.py"],
        cwd=os.getcwd(),
    )
    return result.returncode


def main():
    """主函数"""
    print("="*60)
    print("IoT 网关手动测试工具")
    print("="*60)

    while True:
        print_menu()
        choice = input("\n请选择操作 (0-4): ").strip()

        if choice == "0":
            print("退出测试工具")
            break
        elif choice == "1":
            start_gateway()
        elif choice == "2":
            ret = run_android_test()
            print(f"Android测试完成，返回码: {ret}")
        elif choice == "3":
            ret = run_device_test()
            print(f"设备测试完成，返回码: {ret}")
        elif choice == "4":
            ret = run_integration_test()
            print(f"集成测试完成，返回码: {ret}")
        else:
            print("无效选择，请重试")


if __name__ == "__main__":
    main()
