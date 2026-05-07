#!/bin/bash
# 停止服务脚本

echo "停止Multi-Agent Dev System..."

# 停止后端
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID
        echo "✓ 后端已停止"
    fi
    rm .backend.pid
fi

# 停止前端
if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID
        echo "✓ 前端已停止"
    fi
    rm .frontend.pid
fi

# 清理可能残留的进程
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "vite" 2>/dev/null

echo "✓ 所有服务已停止"
