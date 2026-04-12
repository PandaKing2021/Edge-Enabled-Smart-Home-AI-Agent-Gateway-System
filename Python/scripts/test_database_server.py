#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库服务器和网关连接测试脚本
测试数据库服务器的启动、连接和功能
"""

import subprocess
import sys
import time
import socket
import json
from pathlib import Path

# 设置编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "Python"))
sys.path.insert(0, str(PROJECT_ROOT / "Python/Gate"))

from common.config import load_server_config, load_gate_config
from MyComm import format_comm_data_string, decode_comm_data, decode_user_data, format_userdata_string

def test_database_connection():
    """测试数据库连接"""
    print("\n" + "="*60)
    print("测试1: 数据库连接")
    print("="*60)
    
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="1234",
            charset="utf8",
        )
        
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES LIKE 'user_test'")
        result = cursor.fetchone()
        
        if result:
            print("✓ 数据库 'user_test' 存在")
            
            cursor.execute("USE user_test")
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"✓ 找到 {len(tables)} 个表:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("✗ 数据库 'user_test' 不存在")
            print("  请运行: mysql -u root -p1234 < Python/Database\\ Server/init_database.sql")
            return False
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        print("  请检查:")
        print("  1. MySQL服务是否启动")
        print("  2. 用户名和密码是否正确 (root/1234)")
        return False

def start_database_server():
    """启动数据库服务器"""
    print("\n" + "="*60)
    print("测试2: 启动数据库服务器")
    print("="*60)
    
    try:
        config = load_server_config(config_dir=PROJECT_ROOT / "Python/Database Server")
        print(f"✓ 配置加载成功:")
        print(f"  - 服务器IP: {config.ip}")
        print(f"  - 监听端口: {config.listen_port}")
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        return None
    
    # 启动数据库服务器进程
    try:
        server_script = "Python/Database Server/database_process_server.py"
        server_process = subprocess.Popen(
            [sys.executable, server_script],
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print(f"✓ 数据库服务器进程已启动 (PID: {server_process.pid})")
        print("  等待服务器初始化...")
        time.sleep(2)
        
        # 检查服务器是否仍在运行
        if server_process.poll() is not None:
            print("✗ 数据库服务器启动失败")
            output = server_process.stdout.read()
            if output:
                print("  错误输出:")
                for line in output.split('\n'):
                    if line.strip():
                        print(f"    {line}")
            return None
        
        print("✓ 数据库服务器启动成功")
        return server_process
        
    except Exception as e:
        print(f"✗ 数据库服务器启动失败: {e}")
        return None

def test_server_connection():
    """测试数据库服务器连接"""
    print("\n" + "="*60)
    print("测试3: 数据库服务器连接")
    print("="*60)
    
    try:
        config = load_server_config(config_dir=PROJECT_ROOT / "Python/Database Server")
        
        # 使用 localhost 连接，而不是 0.0.0.0
        connect_ip = "127.0.0.1" if config.ip == "0.0.0.0" else config.ip
        
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((connect_ip, config.listen_port))
        print(f"✓ 成功连接到数据库服务器 {connect_ip}:{config.listen_port}")
        client.close()
        return True
        
    except Exception as e:
        print(f"✗ 连接数据库服务器失败: {e}")
        return False

def send_and_receive_json(sock, obj):
    """发送JSON并接收响应"""
    message = json.dumps(obj, ensure_ascii=False) + "\n"
    sock.sendall(message.encode('utf-8'))
    
    chunks = []
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("连接已关闭")
        chunks.append(chunk)
        if b'\n' in chunk:
            break
    
    response = b''.join(chunks)
    return json.loads(response.decode('utf-8'))

def test_check_device_id():
    """测试查询设备列表"""
    print("\n" + "="*60)
    print("测试4: 查询设备列表 (check_device_id)")
    print("="*60)
    
    try:
        config = load_server_config(config_dir=PROJECT_ROOT / "Python/Database Server")
        
        # 使用 localhost 连接
        connect_ip = "127.0.0.1" if config.ip == "0.0.0.0" else config.ip
        
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((connect_ip, config.listen_port))
        
        # 发送查询请求
        request = format_comm_data_string("check_device_id", "A1", 1)
        print(f"→ 发送请求: {request}")
        
        response = send_and_receive_json(client, request)
        print(f"← 收到响应: {response}")
        
        op, data, status = decode_comm_data(response)
        print(f"  操作码: {op}")
        print(f"  状态码: {status}")
        
        if status == 1:
            print(f"  设备列表: {data}")
            print("✓ 查询设备列表成功")
            return True
        else:
            print(f"✗ 查询失败: {data}")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False
    finally:
        try:
            client.close()
        except:
            pass

def test_check_userconfig():
    """测试用户配置校验"""
    print("\n" + "="*60)
    print("测试5: 用户配置校验 (check_userconfig_illegal)")
    print("="*60)
    
    try:
        config = load_server_config(config_dir=PROJECT_ROOT / "Python/Database Server")
        
        # 使用 localhost 连接
        connect_ip = "127.0.0.1" if config.ip == "0.0.0.0" else config.ip
        
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((connect_ip, config.listen_port))
        
        # 发送校验请求
        user_data = format_userdata_string("Jiang", "pwd", "A1")
        request = format_comm_data_string("check_userconfig_illegal", user_data, 1)
        print(f"→ 发送请求: {request}")
        
        response = send_and_receive_json(client, request)
        print(f"← 收到响应: {response}")
        
        op, data, status = decode_comm_data(response)
        print(f"  操作码: {op}")
        print(f"  状态码: {status}")
        
        if status == 1:
            print(f"✓ 用户配置校验成功")
            return True
        else:
            print(f"✗ 校验失败: {data}")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False
    finally:
        try:
            client.close()
        except:
            pass

def test_add_new_user():
    """测试添加新用户"""
    print("\n" + "="*60)
    print("测试6: 添加新用户 (add_new_user)")
    print("="*60)
    
    try:
        config = load_server_config(config_dir=PROJECT_ROOT / "Python/Database Server")
        
        # 使用 localhost 连接
        connect_ip = "127.0.0.1" if config.ip == "0.0.0.0" else config.ip
        
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((connect_ip, config.listen_port))
        
        # 发送注册请求
        user_data = format_userdata_string("test_user", "test_password", "A2")
        request = format_comm_data_string("add_new_user", user_data, 1)
        print(f"→ 发送请求: {request}")
        
        response = send_and_receive_json(client, request)
        print(f"← 收到响应: {response}")
        
        op, data, status = decode_comm_data(response)
        print(f"  操作码: {op}")
        print(f"  状态码: {status}")
        
        if status == 1:
            print(f"✓ 添加用户成功")
            return True
        elif status == 0:
            print(f"⚠ 添加用户失败: 可能用户已存在")
            return True
        else:
            print(f"✗ 添加用户失败: {data}")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False
    finally:
        try:
            client.close()
        except:
            pass

def stop_server(server_process):
    """停止数据库服务器"""
    print("\n" + "="*60)
    print("停止数据库服务器")
    print("="*60)
    
    if server_process:
        print(f"正在停止数据库服务器进程 (PID: {server_process.pid})...")
        server_process.terminate()
        
        try:
            server_process.wait(timeout=5)
            print("✓ 数据库服务器已正常停止")
        except subprocess.TimeoutExpired:
            print("⚠ 数据库服务器未响应，强制停止")
            server_process.kill()
            server_process.wait()
            print("✓ 数据库服务器已强制停止")

def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("数据库服务器和网关连接测试")
    print("="*60)
    
    # 测试1: 数据库连接
    db_ok = test_database_connection()
    if not db_ok:
        print("\n❌ 数据库连接失败，无法继续测试")
        return 1
    
    # 测试2: 启动数据库服务器
    server_process = start_database_server()
    if server_process is None:
        print("\n❌ 数据库服务器启动失败，无法继续测试")
        return 1
    
    try:
        # 测试3: 服务器连接
        conn_ok = test_server_connection()
        if not conn_ok:
            print("\n⚠ 无法连接到数据库服务器")
        
        # 测试4-6: 功能测试
        test1 = test_check_device_id()
        time.sleep(1)
        
        test2 = test_check_userconfig()
        time.sleep(1)
        
        test3 = test_add_new_user()
        time.sleep(1)
        
        # 打印测试结果
        print("\n" + "="*60)
        print("测试结果汇总")
        print("="*60)
        print(f"数据库连接: {'✓ 通过' if db_ok else '✗ 失败'}")
        print(f"服务器启动: {'✓ 通过' if server_process else '✗ 失败'}")
        print(f"服务器连接: {'✓ 通过' if conn_ok else '✗ 失败'}")
        print(f"查询设备列表: {'✓ 通过' if test1 else '✗ 失败'}")
        print(f"用户配置校验: {'✓ 通过' if test2 else '✗ 失败'}")
        print(f"添加新用户: {'✓ 通过' if test3 else '✗ 失败'}")
        
        if db_ok and server_process and test1 and test2:
            print("\n✅ 核心测试通过！数据库服务器运行正常")
            return 0
        else:
            print("\n⚠ 部分测试失败，请检查配置")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠ 用户中断测试")
        return 1
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # 停止服务器
        stop_server(server_process)
        time.sleep(1)

if __name__ == "__main__":
    sys.exit(main())
