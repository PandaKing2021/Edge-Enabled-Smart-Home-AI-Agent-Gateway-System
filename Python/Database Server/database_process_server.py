"""数据库服务器主程序。

负责处理网关的数据库操作请求，包括用户注册、用户配置校验、设备查询等。
使用 MySQL 数据库进行持久化存储，通过 TCP Socket 与网关通信。
所有通信统一使用 JSON 格式。
"""

import json
import logging
import logging.handlers
import socket
import sys
import threading
from pathlib import Path

# 将项目根目录添加到 sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import mysql.connector
from MyComm import format_comm_data_string, decode_comm_data, decode_user_data, format_userdata_string
from common.constants import LISTEN_BACKLOG
from common.protocol import send_json, recv_json

logger = logging.getLogger(__name__)


class DatabaseServer:
    """数据库服务器。

    封装数据库连接、TCP 服务器和请求处理逻辑。

    Attributes:
        db: MySQL 连接对象。
        ip: 服务器监听 IP。
        port: 服务器监听端口。
    """

    def __init__(self, host: str, port: int) -> None:
        self.db = None
        self.ip = host
        self.port = port

    def init_database(self) -> None:
        """初始化 MySQL 数据库连接。

        Raises:
            mysql.connector.Error: 数据库连接失败。
        """
        try:
            self.db = mysql.connector.connect(
                host="localhost",
                port=3306,
                user="root",
                password="1234",
                database="user_test",
                charset="utf8",
            )
            logger.info("数据库连接成功")
        except mysql.connector.Error as error:
            logger.error("数据库连接失败: %s", error)
            raise

    def start(self) -> None:
        """启动数据库服务器。"""
        self.init_database()

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.ip, self.port))
        server_socket.listen(LISTEN_BACKLOG)
        logger.info("数据库通信服务器已启动: %s:%d", self.ip, self.port)

        try:
            while True:
                cs, addr = server_socket.accept()
                logger.info("网关 %s 已连接", addr)
                thread = threading.Thread(
                    target=self._client_handler, args=(cs,), daemon=True
                )
                thread.start()
        except KeyboardInterrupt:
            logger.info("服务器收到退出信号")
        except OSError as error:
            logger.error("服务器监听异常: %s", error)
        finally:
            server_socket.close()
            if self.db:
                self.db.close()

    def _client_handler(self, cs: socket.socket) -> None:
        """处理单个网关连接的请求。

        Args:
            cs: 网关的 TCP 套接字。
        """
        try:
            while True:
                recv_data = recv_json(cs)
                command_code, data_code, status_code = decode_comm_data(recv_data)

                if command_code == "check_userconfig_illegal":
                    logger.info("处理 check_userconfig_illegal 请求 (来自 %s)", cs.getpeername())
                    self._check_userconfig_illegal(cs, data_code)
                elif command_code == "add_new_user":
                    logger.info("处理 add_new_user 请求 (来自 %s)", cs.getpeername())
                    self._add_new_user(cs, data_code)
                elif command_code == "check_device_id":
                    logger.info("处理 check_device_id 请求 (来自 %s)", cs.getpeername())
                    self._check_device_id(cs, data_code)
                else:
                    logger.warning("未知指令码: %s", command_code)

        except (ConnectionError, ConnectionAbortedError) as error:
            logger.warning("网关 %s 连接断开: %s", cs.getpeername(), error)
        except (json.JSONDecodeError, ValueError) as error:
            logger.error("解析网关请求数据失败: %s", error)
        except Exception as error:
            logger.error("处理网关请求异常: %s", error)
        finally:
            cs.close()

    def _add_new_user(self, cs: socket.socket, data_code) -> None:
        """添加新用户。

        执行三条 SQL：
            1. INSERT 用户数据到 users_data 表
            2. UPDATE device_key 表的 owned_by_user 字段
            3. UPDATE device_key 表的 is_used 字段

        Args:
            cs: 网关的 TCP 套接字。
            data_code: 用户信息 dict（包含 username, password, device_key）。
        """
        send_op = "add_new_user"
        username, password, device_key = decode_user_data(data_code)

        cursor = self.db.cursor()
        try:
            # 命令行 1: 插入用户数据
            sql = "INSERT INTO users_data (username, password, owned_device_key) VALUES (%s, %s, %s)"
            cursor.execute(sql, (username, password, device_key))
            insert_status = cursor.rowcount

            # 命令行 2: 更新设备密钥归属
            sql = "UPDATE device_key SET owned_by_user = %s WHERE key_id = %s"
            cursor.execute(sql, (username, device_key))

            # 命令行 3: 标记密钥已使用
            sql = "UPDATE device_key SET is_used = 1 WHERE owned_by_user = %s"
            cursor.execute(sql, (username,))

            self.db.commit()

            if insert_status != 0:
                logger.info("新用户 '%s' 添加成功", username)
                send_json(cs, format_comm_data_string(send_op, "NULL", 1))
            else:
                logger.warning("新用户添加失败: 可能主键或唯一键冲突")
                send_json(cs, format_comm_data_string(send_op, "NULL", 0))

        except mysql.connector.Error as error:
            self.db.rollback()
            logger.error("添加用户失败: %s", error)
            send_json(cs, format_comm_data_string(send_op, str(error), 2))
        finally:
            cursor.close()

    def _check_userconfig_illegal(self, cs: socket.socket, data_code) -> None:
        """校验网关本地用户配置是否合法。

        如果配置非法，尝试自动纠正。

        Args:
            cs: 网关的 TCP 套接字。
            data_code: 用户信息 dict（包含 username, password, device_key）。
        """
        send_op = "check_userconfig_illegal"
        username, password, device_key = decode_user_data(data_code)

        cursor = self.db.cursor()
        try:
            sql = (
                "SELECT * FROM users_data "
                "WHERE username = %s AND password = %s AND owned_device_key = %s"
            )
            cursor.execute(sql, (username, password, device_key))
            result = cursor.fetchall()

            if result:
                logger.info("网关用户配置合法: %s", username)
                send_json(cs, format_comm_data_string(send_op, "NULL", 1))
            else:
                logger.warning("网关用户配置异常: %s", username)
                send_json(cs, format_comm_data_string(send_op, "NULL", 0))

                # 尝试纠正：按用户名查询
                sql = "SELECT * FROM users_data WHERE username = %s"
                cursor.execute(sql, (username,))
                result = cursor.fetchall()

                if result:
                    logger.info("检测到配置被非法修改，正在纠正用户 '%s'", username)
                    corr_user, corr_pwd, corr_key = result[0]
                    send_json(cs, format_comm_data_string(
                        send_op,
                        format_userdata_string(corr_user, corr_pwd, corr_key),
                        1,
                    ))
                    logger.info("网关配置纠正完成")
                else:
                    logger.warning("用户未注册: %s", username)
                    send_json(cs, format_comm_data_string(send_op, "NULL", 0))

        except mysql.connector.Error as error:
            logger.error("用户配置校验异常: %s", error)
            send_json(cs, format_comm_data_string(send_op, str(error), 2))
        finally:
            cursor.close()

    def _check_device_id(self, cs: socket.socket, data_code) -> None:
        """根据设备密钥查询设备名称列表。

        Args:
            cs: 网关的 TCP 套接字。
            data_code: 设备密钥。
        """
        send_op = "check_device_id"

        cursor = self.db.cursor()
        try:
            sql = "SELECT device_name FROM device_data WHERE bind_device_key = %s"
            cursor.execute(sql, (data_code,))
            results = cursor.fetchall()

            device_list = [row[0] for row in results]
            logger.info("查询到 %d 个设备", len(results))
            send_json(cs, format_comm_data_string(send_op, device_list, 1))

        except mysql.connector.Error as error:
            logger.error("设备查询异常: %s", error)
            send_json(cs, format_comm_data_string(send_op, str(error), 0))
        finally:
            cursor.close()


def setup_logging() -> None:
    """初始化数据库服务器日志系统。"""
    formatter = logging.Formatter(
        "[%(asctime)s][%(levelname)s][%(name)s][%(filename)s:%(lineno)d] %(message)s"
    )

    file_handler = logging.FileHandler(
        Path(__file__).parent / "serverLogs.log", encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def main():
    """数据库服务器主入口。"""
    setup_logging()

    from common.config import load_server_config

    server_dir = Path(__file__).resolve().parent
    config = load_server_config(config_dir=server_dir)

    server = DatabaseServer(host=config.ip, port=config.listen_port)
    server.start()


if __name__ == "__main__":
    main()
