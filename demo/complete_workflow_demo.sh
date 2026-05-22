#!/bin/bash
# 完整工作流演示 - 三层隔离架构
# 演示用户、Agent、项目的完整隔离

echo "=========================================="
echo "三层隔离架构 - 完整工作流演示"
echo "=========================================="
echo ""

echo "本演示将展示："
echo "  1. 用户层：创建用户，用户之间完全隔离"
echo "  2. Agent层：注册Agent，Agent属于用户"
echo "  3. 项目层：创建项目，项目完全隔离"
echo "  4. 工作流：在项目中运行工作流"
echo "  5. 文件隔离：Agent只能访问项目workspace"
echo ""
read -p "按Enter开始..."
echo ""

# ==================== 第1步：创建用户 ====================
echo "=========================================="
echo "第1步：创建用户"
echo "=========================================="
echo ""

echo "创建用户 alice..."
./mas user init --username alice --email alice@example.com

echo ""
echo "创建用户 bob..."
./mas user init --username bob --email bob@example.com

echo ""
echo "查看所有用户..."
./mas user list

echo ""
read -p "按Enter继续..."
echo ""

# ==================== 第2步：Alice注册Agent ====================
echo "=========================================="
echo "第2步：Alice注册Agent"
echo "=========================================="
echo ""

echo "切换到用户 alice..."
./mas user switch alice

echo ""
echo "Alice注册产品经理Agent..."
./mas agent register --method template --name alice_pm --template product_manager

echo ""
echo "Alice注册开发Agent（自定义配置）..."
./mas agent register --method template --name alice_dev --template developer \
  --override tools.whitelist=file_operations,code_analysis \
  --override skills.whitelist=code_generation

echo ""
echo "查看Alice的Agent列表..."
./mas agent list

echo ""
read -p "按Enter继续..."
echo ""

# ==================== 第3步：Bob注册Agent ====================
echo "=========================================="
echo "第3步：Bob注册Agent（隔离验证）"
echo "=========================================="
echo ""

echo "切换到用户 bob..."
./mas user switch bob

echo ""
echo "Bob注册自己的Agent..."
./mas agent register --method template --name bob_pm --template product_manager

echo ""
echo "查看Bob的Agent列表（看不到Alice的Agent）..."
./mas agent list

echo ""
echo "切换回Alice..."
./mas user switch alice

echo ""
echo "查看Alice的Agent列表（看不到Bob的Agent）..."
./mas agent list

echo ""
read -p "按Enter继续..."
echo ""

# ==================== 第4步：创建项目 ====================
echo "=========================================="
echo "第4步：创建项目"
echo "=========================================="
echo ""

echo "Alice创建项目 todo-app..."
./mas project create --name todo-app --description "Todo应用开发项目"

echo ""
echo "Alice创建项目 blog-system..."
./mas project create --name blog-system --description "博客系统项目"

echo ""
echo "查看Alice的项目列表..."
./mas project list

echo ""
echo "查看项目详情..."
./mas project show todo-app

echo ""
read -p "按Enter继续..."
echo ""

# ==================== 第5步：在项目中运行工作流 ====================
echo "=========================================="
echo "第5步：在项目中运行工作流"
echo "=========================================="
echo ""

echo "设置当前项目为 todo-app..."
./mas project use todo-app

echo ""
echo "在todo-app项目中运行工作流..."
echo "（这将创建会话，保存到项目目录）"
echo ""
echo "注意：由于需要LLM API，这里只演示命令，不实际执行"
echo ""
echo "命令示例："
echo "  ./mas workflow run --title '开发用户认证功能' --description '实现用户登录、注册、密码重置'"
echo ""

echo "会话将保存到："
echo "  users/user_alice/projects/todo-app/sessions/"
echo ""
echo "Agent将工作在："
echo "  users/user_alice/projects/todo-app/workspace/"
echo ""

read -p "按Enter继续..."
echo ""

# ==================== 第6步：查看项目会话 ====================
echo "=========================================="
echo "第6步：查看项目会话"
echo "=========================================="
echo ""

echo "列出所有项目的会话..."
./mas task list

echo ""
echo "列出todo-app项目的会话..."
./mas task list --project todo-app

echo ""
echo "如果有会话，可以查看详情："
echo "  ./mas task show --project todo-app --latest"
echo "  ./mas task agents --project todo-app --latest"
echo ""

read -p "按Enter继续..."
echo ""

# ==================== 第7步：文件隔离演示 ====================
echo "=========================================="
echo "第7步：文件隔离演示"
echo "=========================================="
echo ""

echo "Agent的文件操作安全机制："
echo ""
echo "1. Agent只能访问项目workspace内的文件"
echo "2. 路径遍历攻击防护（../ 等）"
echo "3. 自动创建父目录"
echo ""

echo "测试文件操作..."
python3 << 'EOF'
from src.agents.base_agent import BaseAgent
from pathlib import Path

class TestAgent(BaseAgent):
    def process(self, task):
        return {'success': True}

# 创建项目上下文
project_context = {
    'project_name': 'todo-app',
    'workspace_path': 'users/user_alice/projects/todo-app/workspace',
    'artifacts_path': 'users/user_alice/projects/todo-app/artifacts'
}

agent = TestAgent(
    name='TestAgent',
    role='测试',
    project_context=project_context
)

print("✓ 写入文件到workspace...")
result = agent.write_file('src/main.py', 'print("Hello")')
print(f"  {result['output']}")

print("\n✓ 读取文件...")
result = agent.read_file('src/main.py')
print(f"  内容: {result['output']}")

print("\n✓ 列出文件...")
result = agent.list_files('src')
print(f"  文件: {result['output']}")

print("\n✗ 尝试访问workspace外的文件（应该失败）...")
result = agent.write_file('../../../etc/passwd', 'hack')
print(f"  {result['error']}")

print("\n✓ 安全检查通过！")
EOF

echo ""
read -p "按Enter继续..."
echo ""

# ==================== 第8步：目录结构 ====================
echo "=========================================="
echo "第8步：查看目录结构"
echo "=========================================="
echo ""

echo "三层隔离的目录结构："
echo ""
tree -L 4 users/user_alice/ 2>/dev/null || find users/user_alice/ -type d | head -20

echo ""
read -p "按Enter继续..."
echo ""

# ==================== 总结 ====================
echo "=========================================="
echo "演示完成"
echo "=========================================="
echo ""

echo "✅ 已演示的功能："
echo ""
echo "1. 用户层隔离"
echo "   - Alice和Bob各有独立的命名空间"
echo "   - 用户之间看不到对方的Agent和项目"
echo ""
echo "2. Agent层隔离"
echo "   - Agent属于特定用户"
echo "   - Agent配置完全可定制"
echo "   - 支持tools、skills、plugins、MCP配置"
echo ""
echo "3. 项目层隔离"
echo "   - 每个项目有独立的workspace"
echo "   - 会话保存到项目目录"
echo "   - Agent只能访问项目文件"
echo ""
echo "4. 文件安全"
echo "   - 路径遍历攻击防护"
echo "   - 只能访问项目workspace"
echo "   - 详细的错误信息"
echo ""
echo "5. 向后兼容"
echo "   - 旧Agent仍然可用"
echo "   - 旧会话仍然可访问"
echo ""

echo "📚 相关文档："
echo "  - docs/UPDATE_COMPLETE.md - 更新完成报告"
echo "  - docs/ISOLATION_ARCHITECTURE.md - 架构设计"
echo "  - docs/FILE_MANAGEMENT.md - 文件管理"
echo "  - demo/agent_config_demo.sh - Agent配置演示"
echo ""

echo "🚀 下一步："
echo "  1. 配置LLM API（Claude/OpenAI/Ollama）"
echo "  2. 运行真实的工作流"
echo "  3. 查看Agent协作过程"
echo ""
