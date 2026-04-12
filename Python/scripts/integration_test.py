#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网关集成测试
自动启动网关并运行模拟测试
"""

import sys
import time
import subprocess
import threading
import os

# 设置编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class GatewayTester:
    """网关集成测试器"""

    def __init__(self):
        self.gateway_process = None
        self.test_results = {}

    def start_gateway(self):
        """启动网关程序"""
        print("\n" + "="*60)
        print("启动网关程序")
        print("="*60)

        try:
            # 检查数据库服务器是否需要启动
            print("⚠️  注意: 请确保数据库服务器已启动")
            print("⚠️  如果需要，请先运行: cd 'Database Server' && python database_process_server.py")

            # 启动网关
            gate_script = "Python/Gate/gate.py"
            if not os.path.exists(gate_script):
                print(f"✗ 网关脚本不存在: {gate_script}")
                return False

            # 设置环境变量以确保Python能找到模块
            env = os.environ.copy()
            env['PYTHONPATH'] = "Python"

            # 启动网关进程
            self.gateway_process = subprocess.Popen(
                [sys.executable, gate_script],
                cwd=os.getcwd(),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            print(f"✓ 网关进程已启动 (PID: {self.gateway_process.pid})")

            # 等待网关初始化
            print("⏳ 等待网关初始化...")
            time.sleep(3)

            # 检查网关是否仍在运行
            if self.gateway_process.poll() is not None:
                # 网关已经退出，读取输出
                output = self.gateway_process.stdout.read()
                print(f"✗ 网关启动失败:")
                print(output)
                return False

            print("✓ 网关启动成功")
            return True

        except Exception as e:
            print(f"✗ 启动网关失败: {e}")
            return False

    def monitor_gateway(self, duration=60):
        """监控网关输出"""
        def monitor():
            try:
                for line in self.gateway_process.stdout:
                    print(f"[网关] {line.strip()}")
            except:
                pass

        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        return monitor_thread

    def run_device_tests(self):
        """运行设备测试"""
        print("\n" + "="*60)
        print("运行设备测试")
        print("="*60)

        try:
            # 导入设备模拟器
            from simulator_device import test_airconditioner_scenario, test_curtain_scenario, test_multiple_devices

            # 运行测试
            ac_success = test_airconditioner_scenario()
            time.sleep(2)

            curtain_success = test_curtain_scenario()
            time.sleep(2)

            multi_success = test_multiple_devices()

            self.test_results["device_tests"] = {
                "airconditioner": ac_success,
                "curtain": curtain_success,
                "multiple": multi_success
            }

            return all([ac_success, curtain_success, multi_success])

        except Exception as e:
            print(f"✗ 设备测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_android_tests(self):
        """运行Android测试"""
        print("\n" + "="*60)
        print("运行Android测试")
        print("="*60)

        try:
            # 导入Android模拟器
            from simulator_android import test_login_scenario, test_register_scenario

            # 运行测试
            login_success = test_login_scenario()
            time.sleep(2)

            register_success = test_register_scenario()

            self.test_results["android_tests"] = {
                "login": login_success,
                "register": register_success
            }

            return login_success

        except Exception as e:
            print(f"✗ Android测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def stop_gateway(self):
        """停止网关"""
        print("\n" + "="*60)
        print("停止网关程序")
        print("="*60)

        if self.gateway_process:
            print(f"正在停止网关进程 (PID: {self.gateway_process.pid})...")
            self.gateway_process.terminate()

            try:
                # 等待进程结束
                self.gateway_process.wait(timeout=5)
                print("✓ 网关已正常停止")
            except subprocess.TimeoutExpired:
                # 强制杀死进程
                print("⚠️  网关未响应，强制停止")
                self.gateway_process.kill()
                self.gateway_process.wait()
                print("✓ 网关已强制停止")

    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*60)
        print("测试摘要")
        print("="*60)

        if "device_tests" in self.test_results:
            print("\n📱 设备测试:")
            device_tests = self.test_results["device_tests"]
            print(f"  空调设备: {'✓ 通过' if device_tests['airconditioner'] else '✗ 失败'}")
            print(f"  窗帘设备: {'✓ 通过' if device_tests['curtain'] else '✗ 失败'}")
            print(f"  多设备: {'✓ 通过' if device_tests['multiple'] else '✗ 失败'}")

        if "android_tests" in self.test_results:
            print("\n🤖 Android测试:")
            android_tests = self.test_results["android_tests"]
            print(f"  登录功能: {'✓ 通过' if android_tests['login'] else '✗ 失败'}")
            print(f"  注册功能: {'✓ 通过' if android_tests['register'] else '✗ 失败'}")

        # 总体评估
        all_passed = True
        for category, tests in self.test_results.items():
            if not all(tests.values()):
                all_passed = False
                break

        print("\n" + "="*60)
        if all_passed:
            print("✅ 所有测试通过！网关运行正常")
        else:
            print("❌ 部分测试失败，请检查日志")
        print("="*60)

    def run_all_tests(self):
        """运行所有测试"""
        print("="*60)
        print("网关集成测试套件")
        print("="*60)

        # 启动网关
        if not self.start_gateway():
            print("\n✗ 无法启动网关，测试终止")
            return False

        # 监控网关输出
        monitor_thread = self.monitor_gateway()

        try:
            # 运行设备测试
            device_success = self.run_device_tests()

            # 运行Android测试
            android_success = self.run_android_tests()

            # 等待网关处理完成
            time.sleep(2)

            # 打印摘要
            self.print_summary()

            return device_success or android_success

        except KeyboardInterrupt:
            print("\n\n⚠️  用户中断测试")
            return False
        except Exception as e:
            print(f"\n✗ 测试过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # 停止网关
            self.stop_gateway()

            # 等待监控线程结束
            if monitor_thread.is_alive():
                time.sleep(1)


def main():
    """主函数"""
    tester = GatewayTester()
    success = tester.run_all_tests()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
