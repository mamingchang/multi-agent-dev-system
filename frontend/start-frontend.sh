#!/bin/bash
# 前端启动脚本

set -e

echo "=========================================="
echo "Multi-Agent Dev System - 前端启动"
echo "=========================================="
echo ""

# 检查node_modules
echo "1. 检查前端依赖..."
if [ ! -d "node_modules" ]; then
    echo "⚠️  前端依赖未安装"
    echo "   正在安装..."
    npm install
else
    echo "✓ 前端依赖已安装"
fi
echo ""

# 启动前端
echo "2. 启动前端服务..."
echo "   访问: http://localhost:3000"
echo ""

npm run dev
