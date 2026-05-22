"""
演示改进后的记忆系统

展示：
1. 自动记忆触发（检测纠正、确认、偏好）
2. Markdown格式记忆
3. 记忆索引（MEMORY.md）
4. 双轨记忆架构（内存+文件）
"""

import sys
import os
sys.path.insert(0, '/home/mamingchang/multi-agent-dev-system')

from src.agents.developer import DeveloperAgent
from src.permissions import get_permission_manager, PermissionLevel
from src.tools.base import get_tool_registry
from src.tools.file_tools import ReadTool, WriteTool, EditTool
from src.tools.search_tools import GlobTool, GrepTool
from src.tools.shell_tools import BashTool

# 注册工具
registry = get_tool_registry()
registry.register(ReadTool())
registry.register(WriteTool())
registry.register(EditTool())
registry.register(GlobTool())
registry.register(GrepTool())
registry.register(BashTool())

# 创建测试项目
project_path = "/tmp/memory_demo_project"
os.makedirs(project_path, exist_ok=True)

# 注册项目权限
perm_manager = get_permission_manager()
perm_manager.register_project(
    project_id="memory_demo",
    project_path=project_path,
    level=PermissionLevel.FULL
)

print("=" * 80)
print("改进后的记忆系统演示")
print("=" * 80)

# 创建Developer Agent
developer = DeveloperAgent()
developer.set_project_context("memory_demo")

# ============================================================================
# 场景1：自动记忆触发 - 用户纠正
# ============================================================================
print(f"\n{'='*80}")
print("场景1：自动记忆触发 - 用户纠正")
print(f"{'='*80}\n")

user_message = "不要使用Flask，应该用FastAPI"
agent_context = {
    'response': "我建议使用Flask框架",
    'action': "选择Flask作为后端框架"
}

print(f"用户消息: {user_message}")
print(f"Agent上下文: {agent_context}")

# 自动处理用户消息
saved_memories = developer.process_user_message(user_message, agent_context)

print(f"\n自动保存的记忆: {len(saved_memories)}个")
for memory in saved_memories:
    if memory:
        print(f"  ✅ {memory.get('output', 'N/A')}")

# ============================================================================
# 场景2：自动记忆触发 - 用户确认
# ============================================================================
print(f"\n{'='*80}")
print("场景2：自动记忆触发 - 用户确认")
print(f"{'='*80}\n")

user_message = "是的，这个方案可以，继续"
agent_context = {
    'action': "使用单体架构而不是微服务"
}

print(f"用户消息: {user_message}")
print(f"Agent上下文: {agent_context}")

saved_memories = developer.process_user_message(user_message, agent_context)

print(f"\n自动保存的记忆: {len(saved_memories)}个")
for memory in saved_memories:
    if memory:
        print(f"  ✅ {memory.get('output', 'N/A')}")

# ============================================================================
# 场景3：自动记忆触发 - 用户偏好
# ============================================================================
print(f"\n{'='*80}")
print("场景3：自动记忆触发 - 用户偏好")
print(f"{'='*80}\n")

user_message = "我喜欢使用TypeScript而不是JavaScript"

print(f"用户消息: {user_message}")

saved_memories = developer.process_user_message(user_message)

print(f"\n自动保存的记忆: {len(saved_memories)}个")
for memory in saved_memories:
    if memory:
        print(f"  ✅ {memory.get('output', 'N/A')}")

# ============================================================================
# 场景4：明确的记忆请求
# ============================================================================
print(f"\n{'='*80}")
print("场景4：明确的记忆请求")
print(f"{'='*80}\n")

user_message = "记住：这个项目的数据库使用PostgreSQL，不要用MySQL"

print(f"用户消息: {user_message}")

saved_memories = developer.process_user_message(user_message)

print(f"\n自动保存的记忆: {len(saved_memories)}个")
for memory in saved_memories:
    if memory:
        print(f"  ✅ {memory.get('output', 'N/A')}")

# ============================================================================
# 场景5：手动保存Markdown记忆
# ============================================================================
print(f"\n{'='*80}")
print("场景5：手动保存Markdown记忆")
print(f"{'='*80}\n")

result = developer.save_memory_as_markdown(
    name="code_style_preference",
    description="用户偏好的代码风格",
    content={
        'content': "用户要求所有代码必须有详细注释，函数必须有docstring",
        'reason': "提高代码可读性和可维护性",
        'how_to_apply': "在编写代码时，为每个函数添加docstring，为复杂逻辑添加注释"
    },
    memory_type="user",
    importance="high",
    tags=["code_style", "documentation"]
)

print(f"保存结果: {result['output']}")

# ============================================================================
# 场景6：保存项目记忆
# ============================================================================
print(f"\n{'='*80}")
print("场景6：保存项目记忆")
print(f"{'='*80}\n")

result = developer.save_memory_as_markdown(
    name="project_architecture_decision",
    description="项目架构决策：使用单体架构",
    content={
        'content': "团队决定使用单体架构而不是微服务",
        'reason': "团队规模小，单体架构更简单，维护成本低",
        'context': "讨论了微服务的优缺点，考虑到当前团队只有3人",
        'how_to_apply': "所有模块放在同一个代码库，使用模块化设计"
    },
    memory_type="project",
    importance="critical",
    tags=["architecture", "decision"]
)

print(f"保存结果: {result['output']}")

# ============================================================================
# 场景7：保存反馈记忆
# ============================================================================
print(f"\n{'='*80}")
print("场景7：保存反馈记忆")
print(f"{'='*80}\n")

result = developer.save_memory_as_markdown(
    name="testing_feedback",
    description="测试必须使用真实数据库",
    content={
        'content': "集成测试必须使用真实数据库，不要使用mock",
        'reason': "上次使用mock导致生产环境出现bug，mock和真实数据库行为不一致",
        'how_to_apply': "在编写测试时，使用Docker启动测试数据库，不要mock数据库调用"
    },
    memory_type="feedback",
    importance="high",
    tags=["testing", "database"]
)

print(f"保存结果: {result['output']}")

# ============================================================================
# 场景8：查看记忆索引
# ============================================================================
print(f"\n{'='*80}")
print("场景8：查看记忆索引（MEMORY.md）")
print(f"{'='*80}\n")

# 更新索引
developer.update_memory_index()

# 获取索引内容
index_content = developer.get_memory_index()

print("记忆索引内容:")
print("-" * 80)
print(index_content)
print("-" * 80)

# ============================================================================
# 场景9：搜索记忆
# ============================================================================
print(f"\n{'='*80}")
print("场景9：搜索记忆")
print(f"{'='*80}\n")

# 搜索所有feedback类型的记忆
print("搜索类型=feedback的记忆:")
memories = developer.search_markdown_memories(memory_type="feedback")
print(f"找到 {len(memories)} 个记忆")
for memory in memories:
    print(f"  - {memory.get('name')}: {memory.get('description')}")

# 搜索包含"数据库"的记忆
print("\n搜索包含'数据库'的记忆:")
memories = developer.search_markdown_memories(query="数据库")
print(f"找到 {len(memories)} 个记忆")
for memory in memories:
    print(f"  - {memory.get('name')}: {memory.get('description')}")

# ============================================================================
# 场景10：内存记忆（运行时）
# ============================================================================
print(f"\n{'='*80}")
print("场景10：内存记忆（运行时，快速检索）")
print(f"{'='*80}\n")

# 保存到内存
developer.remember(
    content="当前任务是实现用户登录功能",
    memory_type_str="working",
    importance="high",
    tags=["current_task", "login"]
)

developer.remember(
    content="用户要求登录失败3次后锁定账户",
    memory_type_str="short_term",
    importance="high",
    tags=["requirement", "security"]
)

print("已保存2条内存记忆")

# 回忆
print("\n回忆包含'登录'的记忆:")
memories = developer.recall(query="登录", limit=5)
print(f"找到 {len(memories)} 条记忆")
for memory in memories:
    print(f"  - [{memory.memory_type.value}] {memory.content}")

# ============================================================================
# 场景11：获取完整记忆摘要
# ============================================================================
print(f"\n{'='*80}")
print("场景11：获取完整记忆摘要（内存+文件）")
print(f"{'='*80}\n")

summary = developer.get_all_memories_summary()

print("完整记忆摘要:")
print("-" * 80)
print(summary)
print("-" * 80)

# ============================================================================
# 场景12：查看生成的文件
# ============================================================================
print(f"\n{'='*80}")
print("场景12：查看生成的记忆文件")
print(f"{'='*80}\n")

memory_dir = f".memory/{developer.name}"
if os.path.exists(memory_dir):
    print(f"记忆目录: {memory_dir}")
    print("\n文件列表:")
    for file_name in sorted(os.listdir(memory_dir)):
        file_path = os.path.join(memory_dir, file_name)
        file_size = os.path.getsize(file_path)
        print(f"  - {file_name} ({file_size} bytes)")

    # 查看一个Markdown文件的内容
    md_files = [f for f in os.listdir(memory_dir) if f.endswith('.md') and f != 'MEMORY.md']
    if md_files:
        print(f"\n查看文件内容: {md_files[0]}")
        print("-" * 80)
        with open(os.path.join(memory_dir, md_files[0]), 'r', encoding='utf-8') as f:
            print(f.read())
        print("-" * 80)

# ============================================================================
# 总结
# ============================================================================
print(f"\n{'='*80}")
print("改进后的记忆系统总结")
print(f"{'='*80}\n")

print("✅ 新增功能:")
print("   1. 自动记忆触发")
print("      - 检测用户纠正 → 自动保存feedback记忆")
print("      - 检测用户确认 → 自动保存feedback记忆")
print("      - 检测用户偏好 → 自动保存user记忆")
print("      - 检测明确请求 → 自动保存long_term记忆")
print()
print("   2. Markdown格式支持")
print("      - 使用Markdown + Frontmatter格式")
print("      - 人类可读，易于编辑")
print("      - 结构化元数据（name, description, type, importance, tags）")
print()
print("   3. 记忆索引（MEMORY.md）")
print("      - 自动生成索引文件")
print("      - 按类型分组")
print("      - 快速浏览所有记忆")
print()
print("   4. 双轨记忆架构")
print("      - 内存记忆：快速检索，会话级别")
print("      - 文件记忆：持久化，跨会话")
print()
print("✅ 借鉴Claude Code的优点:")
print("   - 自动触发（减少手动操作）")
print("   - Markdown格式（人类可读）")
print("   - 索引文件（快速浏览）")
print()
print("✅ 保留本项目的优点:")
print("   - 双轨架构（内存+文件）")
print("   - 结构化查询（按类型、标签、重要性）")
print("   - 多Agent支持（每个Agent独立记忆）")
print("   - 版本控制（时间戳）")
