#!/bin/bash
# 本地启动脚本 - 无需Docker

set -e

echo "=========================================="
echo "Multi-Agent Dev System - 本地启动"
echo "=========================================="
echo ""

# 检查Python依赖
echo "1. 检查Python依赖..."
if ! python3 -c "import sqlalchemy" 2>/dev/null; then
    echo "❌ Python依赖未安装完成"
    echo "   请运行: python3 -m pip install --user -r requirements.txt"
    exit 1
fi
echo "✓ Python依赖已安装"
echo ""

# 初始化数据库
echo "2. 初始化数据库..."
if [ ! -f multi_agent_dev.db ]; then
    python3 -c "
from sqlalchemy import create_engine
from src.database.models import Base

engine = create_engine('sqlite:///./multi_agent_dev.db')
Base.metadata.create_all(engine)
print('✓ 数据库初始化成功')
"
else
    echo "✓ 数据库已存在"
fi
echo ""

# 检查环境变量
echo "3. 检查环境配置..."
if [ ! -f .env ]; then
    echo "⚠️  .env文件不存在，使用默认配置"
    cp .env.example .env
fi
echo "✓ 环境配置就绪"
echo ""

# 启动后端
echo "4. 启动后端服务..."
echo "   访问: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo ""

python3 -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
