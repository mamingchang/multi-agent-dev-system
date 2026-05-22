#!/bin/bash
# 三层隔离架构演示脚本

echo "=========================================="
echo "三层隔离架构演示"
echo "用户 → 项目 → Agent"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}第1步：创建用户${NC}"
echo "----------------------------------------"
echo "命令: ./mas user init --username alice --email alice@example.com"
echo ""

./mas user init --username alice --email alice@example.com

echo ""
read -p "按Enter继续..."
echo ""

echo -e "${BLUE}第2步：查看当前用户${NC}"
echo "----------------------------------------"
echo "命令: ./mas user whoami"
echo ""

./mas user whoami

echo ""
read -p "按Enter继续..."
echo ""

echo -e "${BLUE}第3步：创建项目${NC}"
echo "----------------------------------------"
echo "命令: ./mas project create --name todo-app --description 'Todo待办事项应用'"
echo ""

./mas project create --name todo-app --description "Todo待办事项应用"

echo ""
read -p "按Enter继续..."
echo ""

echo -e "${BLUE}第4步：查看项目列表${NC}"
echo "----------------------------------------"
echo "命令: ./mas project list"
echo ""

./mas project list

echo ""
read -p "按Enter继续..."
echo ""

echo -e "${BLUE}第5步：查看项目详情${NC}"
echo "----------------------------------------"
echo "命令: ./mas project show todo-app"
echo ""

./mas project show todo-app

echo ""
read -p "按Enter继续..."
echo ""

echo -e "${BLUE}第6步：查看目录结构${NC}"
echo "----------------------------------------"
echo "三层隔离的目录结构："
echo ""

tree -L 4 users/ 2>/dev/null || find users/ -type d | head -20

echo ""
read -p "按Enter继续..."
echo ""

echo -e "${BLUE}第7步：创建第二个项目${NC}"
echo "----------------------------------------"
echo "命令: ./mas project create --name blog-system --description '博客系统'"
echo ""

./mas project create --name blog-system --description "博客系统"

echo ""
echo "命令: ./mas project list"
echo ""

./mas project list

echo ""
read -p "按Enter继续..."
echo ""

echo -e "${BLUE}第8步：切换项目${NC}"
echo "----------------------------------------"
echo "命令: ./mas project use todo-app"
echo ""

./mas project use todo-app

echo ""
echo "命令: ./mas project current"
echo ""

./mas project current

echo ""
read -p "按Enter继续..."
echo ""

echo -e "${GREEN}=========================================="
echo "演示完成！"
echo "==========================================${NC}"
echo ""

echo "三层隔离架构已建立："
echo ""
echo "users/"
echo "  └── user_alice/"
echo "      ├── profile.yaml          # 用户配置"
echo "      ├── agents/               # Alice的Agent"
echo "      └── projects/             # Alice的项目"
echo "          ├── todo-app/         # 项目1（完全隔离）"
echo "          │   ├── project.yaml"
echo "          │   ├── sessions/     # 该项目的会话"
echo "          │   ├── workspace/    # 该项目的代码"
echo "          │   ├── artifacts/    # 该项目的产物"
echo "          │   └── docs/         # 该项目的文档"
echo "          └── blog-system/      # 项目2（完全隔离）"
echo "              ├── project.yaml"
echo "              ├── sessions/"
echo "              └── workspace/"
echo ""

echo "下一步："
echo "  1. 注册Agent: ./mas agent register --method template --name my_pm --template product_manager"
echo "  2. 运行工作流: ./mas workflow run --project todo-app --title '添加功能'"
echo "  3. 查看会话: ./mas project sessions todo-app"
echo ""

echo "更多信息："
echo "  - 架构文档: docs/ISOLATION_ARCHITECTURE.md"
echo "  - CLI指南: docs/CLI_GUIDE.md"
echo ""
