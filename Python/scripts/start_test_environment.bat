@echo off
REM AI Agent 测试环境启动脚本 (Windows)
REM 用于快速启动测试所需的所有服务

chcp 65001 > nul
echo ==========================================
echo   AI Agent 测试环境启动脚本
echo ==========================================
echo.

REM 检查Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [√] Python 已安装
) else (
    echo [×] Python 未安装
    pause
    exit /b 1
)

REM 检查MySQL
mysql --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [√] MySQL 已安装
) else (
    echo [×] MySQL 未安装
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   步骤 1: 初始化数据库
echo ==========================================
echo.

echo 初始化数据库...
mysql -u root -p < "%~dp0..\Database Server\ai_agent_tables.sql" 2>nul
if %errorlevel% equ 0 (
    echo [√] 数据库初始化成功
) else (
    echo [!] 数据库初始化失败或已存在
)

echo.
echo ==========================================
echo   步骤 2: 启动数据库服务器
echo ==========================================
echo.

set DB_SERVER_DIR=%~dp0..\Database Server
echo 启动数据库服务器: %DB_SERVER_DIR%\db_server.py
cd /d "%DB_SERVER_DIR%"

REM 在后台启动数据库服务器
start "Database Server" python db_server.py

REM 等待数据库服务器启动
timeout /t 2 /nobreak > nul

echo [√] 数据库服务器已启动

echo.
echo ==========================================
echo   步骤 3: 启动网关
echo ==========================================
echo.

set GATE_DIR=%~dp0..\Gate
echo 启动网关: %GATE_DIR%\gate.py
cd /d "%GATE_DIR%"

REM 在后台启动网关
start "Gateway" python gate.py

REM 等待网关启动
timeout /t 3 /nobreak > nul

echo [√] 网关已启动

echo.
echo ==========================================
echo   测试环境启动完成
echo ==========================================
echo.
echo 现在可以运行测试:
echo   cd %~dp0
echo   python run_all_tests.py
echo.
echo 提示: 数据库服务器和网关会在单独的窗口中运行
echo       关闭这些窗口即可停止服务
echo.
pause
