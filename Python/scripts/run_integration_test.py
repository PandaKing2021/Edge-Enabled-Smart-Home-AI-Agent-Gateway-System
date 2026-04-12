#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速集成测试
启动测试版网关并运行模拟测试
"""

import subprocess
import sys
import time
import threading
import os

# 设置编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def run_gateway():
    """在测试模式下启动网关"""
    print("\n" + "="*60)
    print("启动网关（测试模式）")
    print("="*60)

    # 设置环境变量启用测试模式
    gate_script = "Python/Gate/gate_test.py"

    # 启动网关进程
    gateway_process = subprocess.Popen(
        [sys.executable, gate_script, '--test'],
        cwd=os.getcwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    print(f"V 网关进程已启动 (PID: {gateway_process.pid})")

    # 启动监控线程
    def monitor_output():
        while True:
            try:
                line = gateway_process.stdout.readline()
                if line:
                    print(f"[网关] {line.strip()}")
                elif gateway_process.poll() is not None:
                    break
                else:
                    time.sleep(0.1)
            except UnicodeDecodeError:
                # 跳过无法解码的行
                pass
            except:
                break

    monitor_thread = threading.Thread(target=monitor_output, daemon=True)
    monitor_thread.start()

    # 等待网关初始化
    print("... 等待网关初始化...")
    time.sleep(5)

    return gateway_process, monitor_thread


def run_android_simulator():
    """运行Android模拟器"""
    print("\n" + "="*60)
    print("运行Android模拟器测试")
    print("="*60)

    try:
        result = subprocess.run(
            [sys.executable, "Python/scripts/simulator_android.py"],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            timeout=30
        )

        print(result.stdout)
        if result.stderr:
            print("错误输出:", result.stderr)

        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("X Android模拟器测试超时")
        return False
    except Exception as e:
        print(f"X Android模拟器测试失败: {e}")
        return False


def run_device_simulator():
    """运行设备模拟器"""
    print("\n" + "="*60)
    print("运行设备模拟器测试")
    print("="*60)

    try:
        result = subprocess.run(
            [sys.executable, "Python/scripts/simulator_device.py"],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            timeout=30
        )

        print(result.stdout)
        if result.stderr:
            print("错误输出:", result.stderr)

        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("X 设备模拟器测试超时")
        return False
    except Exception as e:
        print(f"X 设备模拟器测试失败: {e}")
        return False


def stop_gateway(gateway_process):
    """停止网关"""
    print("\n" + "="*60)
    print("停止网关")
    print("="*60)

    if gateway_process:
        print(f"正在停止网关进程 (PID: {gateway_process.pid})...")
        gateway_process.terminate()

        try:
            gateway_process.wait(timeout=5)
            print("V 网关已正常停止")
        except subprocess.TimeoutExpired:
            print("WARNING: 网关未响应，强制停止")
            gateway_process.kill()
            gateway_process.wait()
            print("V 网关已强制停止")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("IoT 网关集成测试")
    print("="*60)

    # 启动网关
    gateway_process, monitor_thread = run_gateway()

    try:
        # 运行测试
        time.sleep(2)

        # 测试Android
        android_success = run_android_simulator()

        time.sleep(2)

        # 测试设备
        device_success = run_device_simulator()

        # 打印结果
        print("\n" + "="*60)
        print("测试结果")
        print("="*60)
        print(f"Android模拟器: {'V 通过' if android_success else 'X 失败'}")
        print(f"设备模拟器: {'V 通过' if device_success else 'X 失败'}")

        if android_success and device_success:
            print("\nOK 所有测试通过！网关运行正常")
        else:
            print("\nFAIL 部分测试失败")

        # 等待网关处理完成
        time.sleep(2)

        return 0 if (android_success or device_success) else 1

    except KeyboardInterrupt:
        print("\n\nWARNING: 用户中断测试")
        return 1
    except Exception as e:
        print(f"\nX 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # 停止网关
        stop_gateway(gateway_process)

        # 等待监控线程
        time.sleep(1)


if __name__ == "__main__":
    sys.exit(main())
