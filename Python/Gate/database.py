"""网关本地数据库操作模块。

负责本地 MySQL 数据库的连接、初始化和数据存储。
"""

import logging
import mysql.connector
from mysql.connector import MySQLConnection
from common.config import GateDbConfig
from common.constants import DB_HOST, DB_PORT

logger = logging.getLogger(__name__)


def create_database_connection(db_config: GateDbConfig, database: str = None) -> MySQLConnection:
    """创建 MySQL 数据库连接。

    Args:
        db_config: 数据库连接配置（用户名、密码）。
        database: 数据库名，为 None 时不指定数据库。

    Returns:
        MySQLConnection 连接对象。

    Raises:
        mysql.connector.Error: 数据库连接失败。
    """
    kwargs = {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": db_config.user,
        "password": db_config.password,
        "charset": "utf8",
    }
    if database:
        kwargs["database"] = database

    conn = mysql.connector.connect(**kwargs)
    logger.info("MySQL 数据库连接成功: %s", database or "(无指定数据库)")
    return conn


def init_gate_database(db_config: GateDbConfig) -> MySQLConnection:
    """初始化网关本地数据库，创建数据库和表（如果不存在）。

    流程：
        1. 连接 MySQL 服务器（不指定数据库）
        2. 创建 gate_database 数据库
        3. 创建 gate_local_data 表
        4. 重新连接到 gate_database

    Args:
        db_config: 数据库连接配置。

    Returns:
        指向 gate_database 的 MySQLConnection。

    Raises:
        mysql.connector.Error: 数据库初始化失败。
    """
    # 第一次连接：创建数据库和表
    conn = create_database_connection(db_config, database=None)
    try:
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS `gate_database`;")
        cursor.execute("USE `gate_database`;")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS `gate_local_data` ("
            "`timestamp` datetime NOT NULL,"
            "`light_th` int NULL,"
            "`temperature` float(5) NULL,"
            "`humidity` float(5) NULL,"
            "`light_cu` int NULL,"
            "`brightness` float(5) NULL,"
            "`curtain_status` int NULL);"
        )
        conn.commit()
        logger.info("网关本地数据库和表初始化完成")
    finally:
        conn.close()

    # 第二次连接：连接到 gate_database
    conn = create_database_connection(db_config, database="gate_database")
    logger.info("网关本地数据库就绪")
    return conn


def save_sensor_data(conn: MySQLConnection, data: dict) -> None:
    """将传感器数据存入本地数据库。

    Args:
        conn: 数据库连接对象。
        data: 传感器数据字典，需包含以下键：
            Light_TH, Temperature, Humidity, Light_CU, Brightness, Curtain_status。
    """
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sql = (
        "INSERT INTO `gate_local_data` "
        "(`timestamp`, `light_th`, `temperature`, `humidity`, `light_cu`, `brightness`, `curtain_status`) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)"
    )
    params = (
        timestamp,
        data.get("Light_TH", 0),
        data.get("Temperature", 0),
        data.get("Humidity", 0),
        data.get("Light_CU", 0),
        data.get("Brightness", 0),
        data.get("Curtain_status", 1),
    )

    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        conn.commit()
    except Exception as error:
        logger.error("传感器数据存储失败: %s", error)
    finally:
        cursor.close()
