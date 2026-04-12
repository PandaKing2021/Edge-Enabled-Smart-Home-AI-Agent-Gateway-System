"""Database server main program.

Responsible for handling gateway database operation requests, including user registration, user configuration validation, device queries, etc.
Uses MySQL database for persistent storage, communicates with gateway via TCP Socket.
All communication uniformly uses JSON format.
"""

import json
import logging
import logging.handlers
import socket
import sys
import threading
from pathlib import Path

# Add project root directory to sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import mysql.connector
from MyComm import format_comm_data_string, decode_comm_data, decode_user_data, format_userdata_string
from common.constants import LISTEN_BACKLOG
from common.protocol import send_json, recv_json

logger = logging.getLogger(__name__)


class DatabaseServer:
    """Database server.

    Encapsulates database connection, TCP server and request handling logic.

    Attributes:
        db: MySQL connection object.
        ip: Server listening IP.
        port: Server listening port.
    """

    def __init__(self, host: str, port: int) -> None:
        self.db = None
        self.ip = host
        self.port = port

    def init_database(self) -> None:
        """Initialize MySQL database connection.

        Raises:
            mysql.connector.Error: Database connection failed.
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
            logger.info("Database connection successful")
        except mysql.connector.Error as error:
            logger.error("Database connection failed: %s", error)
            raise

    def start(self) -> None:
        """Start database server."""
        self.init_database()

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.ip, self.port))
        server_socket.listen(LISTEN_BACKLOG)
        logger.info("Database communication server started: %s:%d", self.ip, self.port)

        try:
            while True:
                cs, addr = server_socket.accept()
                logger.info("Gateway %s connected", addr)
                thread = threading.Thread(
                    target=self._client_handler, args=(cs,), daemon=True
                )
                thread.start()
        except KeyboardInterrupt:
            logger.info("Server received exit signal")
        except OSError as error:
            logger.error("Server listening exception: %s", error)
        finally:
            server_socket.close()
            if self.db:
                self.db.close()

    def _client_handler(self, cs: socket.socket) -> None:
        """Handle requests from a single gateway connection.

        Args:
            cs: Gateway's TCP socket.
        """
        try:
            while True:
                recv_data = recv_json(cs)
                command_code, data_code, status_code = decode_comm_data(recv_data)

                if command_code == "check_userconfig_illegal":
                    logger.info("Processing check_userconfig_illegal request (from %s)", cs.getpeername())
                    self._check_userconfig_illegal(cs, data_code)
                elif command_code == "add_new_user":
                    logger.info("Processing add_new_user request (from %s)", cs.getpeername())
                    self._add_new_user(cs, data_code)
                elif command_code == "check_device_id":
                    logger.info("Processing check_device_id request (from %s)", cs.getpeername())
                    self._check_device_id(cs, data_code)
                else:
                    logger.warning("Unknown command code: %s", command_code)

        except (ConnectionError, ConnectionAbortedError) as error:
            logger.warning("Gateway %s connection lost: %s", cs.getpeername(), error)
        except (json.JSONDecodeError, ValueError) as error:
            logger.error("Failed to parse gateway request data: %s", error)
        except Exception as error:
            logger.error("Gateway request handling exception: %s", error)
        finally:
            cs.close()

    def _add_new_user(self, cs: socket.socket, data_code) -> None:
        """Add new user.

        Execute three SQL statements:
            1. INSERT user data into users_data table
            2. UPDATE owned_by_user field in device_key table
            3. UPDATE is_used field in device_key table

        Args:
            cs: Gateway TCP socket.
            data_code: User information dict (containing username, password, device_key).
        """
        send_op = "add_new_user"
        username, password, device_key = decode_user_data(data_code)

        cursor = self.db.cursor()
        try:
            # Command line 1: Insert user data
            sql = "INSERT INTO users_data (username, password, owned_device_key) VALUES (%s, %s, %s)"
            cursor.execute(sql, (username, password, device_key))
            insert_status = cursor.rowcount

            # Command line 2: Update device key ownership
            sql = "UPDATE device_key SET owned_by_user = %s WHERE key_id = %s"
            cursor.execute(sql, (username, device_key))

            # Command line 3: Mark key as used
            sql = "UPDATE device_key SET is_used = 1 WHERE owned_by_user = %s"
            cursor.execute(sql, (username,))

            self.db.commit()

            if insert_status != 0:
                logger.info("New user '%s' added successfully", username)
                send_json(cs, format_comm_data_string(send_op, "NULL", 1))
            else:
                logger.warning("Failed to add new user: Possible primary key or unique key conflict")
                send_json(cs, format_comm_data_string(send_op, "NULL", 0))

        except mysql.connector.Error as error:
            self.db.rollback()
            logger.error("Failed to add user: %s", error)
            send_json(cs, format_comm_data_string(send_op, str(error), 2))
        finally:
            cursor.close()

    def _check_userconfig_illegal(self, cs: socket.socket, data_code) -> None:
        """Check if gateway local user configuration is valid.

        If configuration is invalid, attempt automatic correction.

        Args:
            cs: Gateway TCP socket.
            data_code: User information dict (containing username, password, device_key).
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
                logger.info("Gateway user configuration is valid: %s", username)
                send_json(cs, format_comm_data_string(send_op, "NULL", 1))
            else:
                logger.warning("Gateway user configuration is abnormal: %s", username)
                send_json(cs, format_comm_data_string(send_op, "NULL", 0))

                # Attempt correction: Query by username
                sql = "SELECT * FROM users_data WHERE username = %s"
                cursor.execute(sql, (username,))
                result = cursor.fetchall()

                if result:
                    logger.info("Detected configuration was illegally modified, correcting user '%s'", username)
                    corr_user, corr_pwd, corr_key = result[0]
                    send_json(cs, format_comm_data_string(
                        send_op,
                        format_userdata_string(corr_user, corr_pwd, corr_key),
                        1,
                    ))
                    logger.info("Gateway configuration correction completed")
                else:
                    logger.warning("User not registered: %s", username)
                    send_json(cs, format_comm_data_string(send_op, "NULL", 0))

        except mysql.connector.Error as error:
            logger.error("User configuration verification exception: %s", error)
            send_json(cs, format_comm_data_string(send_op, str(error), 2))
        finally:
            cursor.close()

    def _check_device_id(self, cs: socket.socket, data_code) -> None:
        """Query device name list based on device key.

        Args:
            cs: Gateway TCP socket.
            data_code: Device key.
        """
        send_op = "check_device_id"

        cursor = self.db.cursor()
        try:
            sql = "SELECT device_name FROM device_data WHERE bind_device_key = %s"
            cursor.execute(sql, (data_code,))
            results = cursor.fetchall()

            device_list = [row[0] for row in results]
            logger.info("Queried %d devices", len(results))
            send_json(cs, format_comm_data_string(send_op, device_list, 1))

        except mysql.connector.Error as error:
            logger.error("Device query exception: %s", error)
            send_json(cs, format_comm_data_string(send_op, str(error), 0))
        finally:
            cursor.close()


def setup_logging() -> None:
    """Initialize database server logging system."""
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
    """Database server main entry."""
    setup_logging()

    from common.config import load_server_config

    server_dir = Path(__file__).resolve().parent
    config = load_server_config(config_dir=server_dir)

    server = DatabaseServer(host=config.ip, port=config.listen_port)
    server.start()


if __name__ == "__main__":
    main()
