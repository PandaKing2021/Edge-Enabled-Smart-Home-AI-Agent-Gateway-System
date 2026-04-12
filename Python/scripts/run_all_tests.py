#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Agent 完整测试套件

运行所有测试并生成测试报告:
1. 单元测试 (ai_agent_test.py)
2. 设备模拟器测试 (simulator_device.py)
3. Android模拟器测试 (simulator_android.py)
4. 端到端测试 (test_ai_agent_e2e.py)
"""

import sys
import subprocess
import time
from pathlib import Path

# 添加项目路径
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _PROJECT_ROOT / "scripts"


def run_test(test_name, script_path):
    """运行单个测试脚本"""
    print("\n" + "="*70)
    print(f"🧪 运行测试: {test_name}")
    print("="*70)
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(_SCRIPTS_DIR),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        success = result.returncode == 0
        print(f"\n{'✅ 通过' if success else '❌ 失败'}: {test_name}")
        return success
        
    except subprocess.TimeoutExpired:
        print(f"\n⏱️  超时: {test_name}")
        return False
    except Exception as e:
        print(f"\n❌ 执行失败: {test_name} - {e}")
        return False


def check_gateway_status():
    """检查网关是否运行"""
    print("\n" + "="*70)
    print("🔍 检查网关状态")
    print("="*70)
    
    import socket
    
    try:
        # 测试设备端口
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result1 = sock.connect_ex(('127.0.0.1', 9300))
        sock.close()
        
        # 测试Android端口
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result2 = sock.connect_ex(('127.0.0.1', 9301))
        sock.close()
        
        if result1 == 0 and result2 == 0:
            print("✅ 网关正在运行")
            return True
        else:
            print("⚠️  网关未运行或端口不可用")
            print("   请先启动网关: cd Python/Gate && python gate.py")
            return False
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False


def main():
    """运行完整测试套件"""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*20 + "AI Agent 完整测试套件" + " "*20 + "║")
    print("╚" + "="*68 + "╝")
    
    # 测试结果
    results = {}
    
    # 1. 检查网关状态
    gateway_running = check_gateway_status()
    results["网关状态"] = "✅ 通过" if gateway_running else "⚠️  警告"
    
    if not gateway_running:
        print("\n⚠️  警告: 网关未运行，部分测试将被跳过")
    
    # 2. 单元测试
    print("\n" + "-"*70)
    print("第一部分: 单元测试")
    print("-"*70)
    
    unit_test_success = run_test(
        "AI Agent 模块单元测试",
        _SCRIPTS_DIR / "ai_agent_test.py"
    )
    results["单元测试"] = "✅ 通过" if unit_test_success else "❌ 失败"
    
    time.sleep(2)
    
    # 3. 设备模拟器测试
    print("\n" + "-"*70)
    print("第二部分: 设备模拟器测试")
    print("-"*70)
    
    device_test_success = run_test(
        "设备模拟器测试",
        _SCRIPTS_DIR / "simulator_device.py"
    )
    results["设备模拟器测试"] = "✅ 通过" if device_test_success else "❌ 失败"
    
    time.sleep(2)
    
    # 4. Android模拟器测试
    print("\n" + "-"*70)
    print("第三部分: Android模拟器测试")
    print("-"*70)
    
    android_test_success = run_test(
        "Android模拟器测试",
        _SCRIPTS_DIR / "simulator_android.py"
    )
    results["Android模拟器测试"] = "✅ 通过" if android_test_success else "❌ 失败"
    
    time.sleep(2)
    
    # 5. 端到端测试 (需要网关运行)
    print("\n" + "-"*70)
    print("第四部分: 端到端测试")
    print("-"*70)
    
    if gateway_running:
        e2e_test_success = run_test(
            "AI Agent 端到端测试",
            _SCRIPTS_DIR / "test_ai_agent_e2e.py"
        )
        results["端到端测试"] = "✅ 通过" if e2e_test_success else "❌ 失败"
    else:
        print("⏭️  跳过: 网关未运行")
        results["端到端测试"] = "⏭️  跳过"
    
    # 生成测试报告
    print("\n" + "="*70)
    print("📊 测试报告")
    print("="*70)
    
    for test_name, status in results.items():
        print(f"{test_name:20s} : {status}")
    
    # 统计
    passed = sum(1 for v in results.values() if "✅" in v)
    failed = sum(1 for v in results.values() if "❌" in v)
    skipped = sum(1 for v in results.values() if "⏭️" in v)
    
    print("\n" + "-"*70)
    print(f"总计: {len(results)}  |  通过: {passed}  |  失败: {failed}  |  跳过: {skipped}")
    print("-"*70)
    
    if failed == 0:
        print("\n🎉 所有测试通过!")
        return 0
    else:
        print(f"\n⚠️  {failed} 个测试失败，请查看详细日志")
        return 1


if __name__ == "__main__":
    sys.exit(main())
