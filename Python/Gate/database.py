"""Gateway local database operation module.

Responsible for local MySQL database connection, initialization, and data storage.
"""

import logging
import mysql.connector
from mysql.connector import MySQLConnection
from common.config import GateDbConfig
from common.constants import DB_HOST, DB_PORT

logger = logging.getLogger(__name__)


def create_database_connection(db_config: GateDbConfig, database: str = None) -> MySQLConnection:
    """Create MySQL database connection.

    Args:
        db_config: Database connection configuration (username, password).
        database: Database name, if None then no specific database.

    Returns:
        MySQLConnection connection object.

    Raises:
        mysql.connector.Error: Database connection failed.
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
    logger.info("MySQL database connection successful: %s", database or "(no database specified)")
    return conn


def init_gate_database(db_config: GateDbConfig) -> MySQLConnection:
    """Initialize gateway local database, create database and tables (if not exist).

    Process:
        1. Connect to MySQL server (no database specified)
        2. Create gate_database database
        3. Create gate_local_data table
        4. Reconnect to gate_database

    Args:
        db_config: Database connection configuration.

    Returns:
        MySQLConnection pointing to gate_database.

    Raises:
        mysql.connector.Error: Database initialization failed.
    """
    # First connection: create database and tables
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
        logger.info("Gateway local database and table initialization complete")
    finally:
        conn.close()

    # Second connection: connect to gate_database
    conn = create_database_connection(db_config, database="gate_database")
    logger.info("Gateway local database ready")
    return conn


def save_sensor_data(conn: MySQLConnection, data: dict) -> None:
    """Save sensor data to local database.

    Args:
        conn: Database connection object.
        data: Sensor data dictionary, must contain following keys:
            Light_TH, Temperature, Humidity, Light_CU, Brightness, Curtain_status.
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
        logger.error("Sensor data storage failed: %s", error)
    finally:
        cursor.close()
