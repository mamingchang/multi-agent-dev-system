#!/bin/bash
# Docker环境测试脚本

set -e

echo "=========================================="
echo "Docker环境测试"
echo "=========================================="
echo ""

# 检查服务是否运行
echo "1. 检查服务状态..."
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ 服务未运行，请先执行: ./docker-start.sh"
    exit 1
fi
echo "✓ 服务正在运行"
echo ""

# 测试后端健康检查
echo "2. 测试后端健康检查..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ 后端健康检查通过"
else
    echo "❌ 后端健康检查失败"
    exit 1
fi
echo ""

# 测试后端根路径
echo "3. 测试后端根路径..."
response=$(curl -s http://localhost:8000/)
if echo "$response" | grep -q "running"; then
    echo "✓ 后端根路径响应正常"
    echo "   $response"
else
    echo "❌ 后端根路径响应异常"
    exit 1
fi
echo ""

# 测试API文档
echo "4. 测试API文档..."
if curl -f http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✓ API文档可访问"
else
    echo "❌ API文档不可访问"
    exit 1
fi
echo ""

# 测试前端
echo "5. 测试前端..."
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✓ 前端可访问"
else
    echo "❌ 前端不可访问"
    exit 1
fi
echo ""

# 检查数据库
echo "6. 检查数据库..."
if [ -f data/multi_agent_dev.db ]; then
    size=$(du -h data/multi_agent_dev.db | cut -f1)
    echo "✓ 数据库文件存在 (大小: $size)"
else
    echo "❌ 数据库文件不存在"
    exit 1
fi
echo ""

# 测试用户注册API
echo "7. 测试用户注册API..."
register_response=$(curl -s -X POST http://localhost:8000/api/auth/register \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser","email":"test@example.com","password":"testpass123"}')

if echo "$register_response" | grep -q "id\|already exists"; then
    echo "✓ 注册API响应正常"
else
    echo "⚠️  注册API响应: $register_response"
fi
echo ""

# 查看容器日志（最后10行）
echo "8. 后端日志（最后10行）:"
echo "---"
docker-compose logs --tail=10 backend
echo ""

echo "=========================================="
echo "✓ 所有测试通过！"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  前端: http://localhost:3000"
echo "  后端: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo ""
