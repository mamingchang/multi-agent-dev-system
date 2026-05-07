#!/bin/bash
# Docker快速启动脚本

set -e

echo "=========================================="
echo "Multi-Agent Dev System - Docker启动"
echo "=========================================="
echo ""

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose未安装，请先安装docker-compose"
    exit 1
fi

echo "✓ Docker已安装"
echo ""

# 创建数据目录
mkdir -p data
echo "✓ 创建数据目录"

# 检查.env.docker
if [ ! -f .env.docker ]; then
    echo "⚠️  .env.docker不存在，使用默认配置"
    echo "   如需配置API密钥，请编辑 .env.docker"
fi

# 构建镜像
echo ""
echo "正在构建Docker镜像..."
docker-compose build

# 初始化数据库
echo ""
echo "正在初始化数据库..."
docker-compose run --rm db-init

# 启动服务
echo ""
echo "正在启动服务..."
docker-compose up -d

# 等待服务启动
echo ""
echo "等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "服务状态:"
docker-compose ps

echo ""
echo "=========================================="
echo "✓ 启动完成！"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  前端: http://localhost:3000"
echo "  后端: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  查看状态: docker-compose ps"
echo ""
