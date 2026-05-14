#!/bin/bash
# 一键启动脚本 - 同时启动前后端

echo "=========================================="
echo "Multi-Agent Dev System - 一键启动"
echo "=========================================="
echo ""

# 检查依赖
echo "检查环境..."

# 检查Python依赖
if ! python3 -c "import sqlalchemy" 2>/dev/null; then
    echo "❌ Python依赖未安装"
    echo "   运行: python3 -m pip install --user -r requirements.txt"
    exit 1
fi

# 检查前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo "❌ 前端依赖未安装"
    echo "   运行: cd frontend && npm install"
    exit 1
fi

echo "✓ 环境检查通过"
echo ""

# 初始化数据库
if [ ! -f multi_agent_dev.db ]; then
    echo "初始化数据库..."
    python3 -c "
from sqlalchemy import create_engine
from src.database.models import Base
engine = create_engine('sqlite:///./multi_agent_dev.db')
Base.metadata.create_all(engine)
print('✓ 数据库初始化完成')
"
    echo ""
fi

# 启动后端（后台）
echo "启动后端服务..."
python3 -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "✓ 后端已启动 (PID: $BACKEND_PID)"
echo "  日志: backend.log"
echo ""

# 等待后端启动
echo "等待后端就绪..."
sleep 3

# 启动前端（后台）
echo "启动前端服务..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "✓ 前端已启动 (PID: $FRONTEND_PID)"
echo "  日志: frontend.log"
echo ""

# 保存PID
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

echo "=========================================="
echo "✓ 启动完成！"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  前端: http://localhost:3000"
echo "  后端: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo ""
echo "查看日志:"
echo "  后端: tail -f backend.log"
echo "  前端: tail -f frontend.log"
echo ""
echo "停止服务:"
echo "  ./stop.sh"
echo ""
