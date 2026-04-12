#!/bin/bash
# AI Agent 测试环境启动脚本
# 用于快速启动测试所需的所有服务

echo "=========================================="
echo "  AI Agent 测试环境启动脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查命令是否存在
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 已安装"
        return 0
    else
        echo -e "${RED}✗${NC} $1 未安装"
        return 1
    fi
}

# 检查依赖
echo "检查依赖..."
check_command python3
check_command mysql
check_command nc

echo ""
echo "=========================================="
echo "  步骤 1: 启动数据库服务器"
echo "=========================================="
echo ""

# 检查MySQL是否运行
if pgrep -x "mysqld" > /dev/null; then
    echo -e "${GREEN}✓${NC} MySQL 服务正在运行"
else
    echo -e "${YELLOW}⚠${NC}  MySQL 服务未运行"
    echo "请启动 MySQL 服务:"
    echo "  sudo systemctl start mysql"
    echo "  或"
    echo "  sudo service mysql start"
fi

echo ""
echo "初始化数据库..."
mysql -u root -p < "$(dirname $0)/../Database Server/ai_agent_tables.sql" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} 数据库初始化成功"
else
    echo -e "${YELLOW}⚠${NC}  数据库初始化失败或已存在"
fi

echo ""
echo "=========================================="
echo "  步骤 2: 启动数据库服务器"
echo "=========================================="
echo ""

DB_SERVER_DIR="$(dirname $0)/../Database Server"
echo "启动数据库服务器: $DB_SERVER_DIR/db_server.py"
cd "$DB_SERVER_DIR"

# 在后台启动数据库服务器
python3 db_server.py &
DB_SERVER_PID=$!

# 等待数据库服务器启动
sleep 2

# 检查数据库服务器是否启动成功
if ps -p $DB_SERVER_PID > /dev/null; then
    echo -e "${GREEN}✓${NC} 数据库服务器已启动 (PID: $DB_SERVER_PID)"
else
    echo -e "${RED}✗${NC} 数据库服务器启动失败"
    exit 1
fi

echo ""
echo "=========================================="
echo "  步骤 3: 启动网关"
echo "=========================================="
echo ""

GATE_DIR="$(dirname $0)/../Gate"
echo "启动网关: $GATE_DIR/gate.py"
cd "$GATE_DIR"

# 在后台启动网关
python3 gate.py &
GATE_PID=$!

# 等待网关启动
sleep 3

# 检查网关是否启动成功
if ps -p $GATE_PID > /dev/null; then
    echo -e "${GREEN}✓${NC} 网关已启动 (PID: $GATE_PID)"
else
    echo -e "${RED}✗${NC} 网关启动失败"
    # 清理数据库服务器
    kill $DB_SERVER_PID 2>/dev/null
    exit 1
fi

echo ""
echo "=========================================="
echo "  测试环境启动完成"
echo "=========================================="
echo ""
echo "服务状态:"
echo "  - 数据库服务器: ${GREEN}运行中${NC} (PID: $DB_SERVER_PID)"
echo "  - 网关: ${GREEN}运行中${NC} (PID: $GATE_PID)"
echo ""
echo "端口状态:"
nc -z localhost 9300 && echo "  - 设备端口 (9300): ${GREEN}已监听${NC}" || echo "  - 设备端口 (9300): ${RED}未监听${NC}"
nc -z localhost 9301 && echo "  - Android端口 (9301): ${GREEN}已监听${NC}" || echo "  - Android端口 (9301): ${RED}未监听${NC}"
echo ""
echo "现在可以运行测试:"
echo "  cd $(dirname $0)"
echo "  python3 run_all_tests.py"
echo ""
echo "停止服务:"
echo "  kill $DB_SERVER_PID $GATE_PID"
echo ""
