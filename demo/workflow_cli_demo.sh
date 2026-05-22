#!/bin/bash
# 交互式工作流演示脚本

echo "=========================================="
echo "交互式工作流CLI演示"
echo "=========================================="
echo ""

echo "这个演示将展示如何使用交互式工作流CLI"
echo ""

echo "1. 查看workflow命令帮助"
echo "   命令: ./mas workflow --help"
echo ""
./mas workflow --help
echo ""

read -p "按Enter继续..."
echo ""

echo "2. 查看run命令详细帮助"
echo "   命令: ./mas workflow run --help"
echo ""
./mas workflow run --help
echo ""

read -p "按Enter继续..."
echo ""

echo "3. 运行交互式工作流（演示）"
echo ""
echo "你可以使用以下命令启动交互式工作流："
echo ""
echo "  ./mas workflow run \\"
echo "    --title \"开发Todo应用\" \\"
echo "    --description \"开发一个简单的Todo待办事项管理应用，用户可以添加、完成、删除待办事项\""
echo ""
echo "或者使用交互式输入："
echo ""
echo "  ./mas workflow run"
echo ""
echo "系统会提示你输入任务标题和需求描述。"
echo ""

read -p "是否现在运行？(y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "启动交互式工作流..."
    echo ""

    # 使用预定义的需求
    ./mas workflow run \
        --title "开发Todo应用" \
        --description "开发一个简单的Todo待办事项管理应用。

需求：
1. 单用户使用，无需登录
2. 待办事项包含：标题、描述、创建时间、完成状态
3. 用户可以添加待办事项
4. 用户可以标记待办事项为完成/未完成
5. 用户可以删除待办事项
6. 用户可以查看所有待办事项列表
7. 使用Web界面，响应式设计

技术栈：
- 后端：Python Flask
- 前端：HTML + JavaScript + Bootstrap
- 数据库：SQLite

非功能需求：
- 界面简洁美观
- 操作响应快速
- 数据持久化存储"
else
    echo ""
    echo "跳过运行。你可以稍后手动运行："
    echo "  ./mas workflow run"
fi

echo ""
echo "=========================================="
echo "演示完成"
echo "=========================================="
echo ""
echo "更多信息请查看文档："
echo "  docs/workflow_cli_guide.md"
echo ""
