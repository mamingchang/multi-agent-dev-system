"""
演示工具架构方案3：混合方案

展示：
1. 基础工具层：所有Agent都有read/write/search能力
2. 抽象接口层：统一的save_memory、save_artifact等方法
3. 专业工具层：特定Agent的专业工具（edit_file、run_command）
"""

import sys
import os
sys.path.insert(0, '/home/mamingchang/multi-agent-dev-system')

from src.agents.requester import RequesterAgent
from src.agents.developer import DeveloperAgent
from src.agents.code_reviewer import CodeReviewerAgent
from src.agents.tester import TesterAgent
from src.permissions import get_permission_manager, PermissionLevel
from src.tools.base import get_tool_registry
from src.tools.file_tools import ReadTool, WriteTool, EditTool
from src.tools.search_tools import GlobTool, GrepTool
from src.tools.shell_tools import BashTool

# 注册所有工具
registry = get_tool_registry()
registry.register(ReadTool())
registry.register(WriteTool())
registry.register(EditTool())
registry.register(GlobTool())
registry.register(GrepTool())
registry.register(BashTool())

# 创建测试项目
project_path = "/tmp/demo_project"
os.makedirs(project_path, exist_ok=True)

# 注册项目权限
perm_manager = get_permission_manager()
perm_manager.register_project(
    project_id="demo",
    project_path=project_path,
    level=PermissionLevel.FULL
)

print("=" * 80)
print("工具架构方案3演示：混合方案")
print("=" * 80)

# ============================================================================
# 场景1：Requester使用基础工具 + 抽象接口
# ============================================================================
print(f"\n{'='*80}")
print("场景1：Requester - 基础工具 + 抽象接口")
print(f"{'='*80}\n")

requester = RequesterAgent()
requester.set_project_context("demo")

print("1. Requester的可用工具:")
for tool in requester.get_available_tools():
    print(f"   - {tool['name']}")

print("\n2. 使用抽象接口保存记忆:")
result = requester.save_memory(
    memory_type="requirement_analysis",
    content={
        "requirement": "构建Todo应用",
        "key_features": ["添加任务", "删除任务", "标记完成"],
        "clarity_score": 9
    }
)
print(f"   状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
if result['success']:
    print(f"   输出: {result['output']}")

print("\n3. 使用抽象接口保存工作日志:")
result = requester.save_work_log(
    action="analyze_requirement",
    details={"requirement_id": "REQ-001", "duration": "5min"}
)
print(f"   状态: {'✅ 成功' if result['success'] else '❌ 失败'}")

print("\n4. 使用抽象接口保存产物:")
result = requester.save_artifact(
    artifact_type="requirement_doc",
    content="# 需求文档\n\n## 功能需求\n- 添加任务\n- 删除任务\n- 标记完成"
)
print(f"   状态: {'✅ 成功' if result['success'] else '❌ 失败'}")

# ============================================================================
# 场景2：Developer使用基础工具 + 专业工具
# ============================================================================
print(f"\n{'='*80}")
print("场景2：Developer - 基础工具 + 专业工具")
print(f"{'='*80}\n")

developer = DeveloperAgent()
developer.set_project_context("demo")

print("1. Developer的可用工具:")
for tool in developer.get_available_tools():
    print(f"   - {tool['name']}")

print("\n2. 使用基础工具写入代码:")
code_path = os.path.join(project_path, "main.py")
result = developer.call_tool(
    'write_file',
    file_path=code_path,
    content="def hello():\n    print('Hello World')\n"
)
print(f"   状态: {'✅ 成功' if result['success'] else '❌ 失败'}")

print("\n3. 使用专业工具编辑代码:")
result = developer.call_tool(
    'edit_file',
    file_path=code_path,
    old_string="print('Hello World')",
    new_string="print('Hello, Todo App!')"
)
print(f"   状态: {'✅ 成功' if result['success'] else '❌ 失败'}")

print("\n4. 使用专业工具运行代码:")
result = developer.call_tool(
    'run_command',
    command=f"python {code_path}"
)
print(f"   状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
if result['success']:
    print(f"   输出: {result['output']}")

print("\n5. 使用抽象接口保存记忆:")
result = developer.save_memory(
    memory_type="implementation_detail",
    content={
        "module": "main.py",
        "decision": "使用简单的print输出",
        "reason": "演示目的"
    }
)
print(f"   状态: {'✅ 成功' if result['success'] else '❌ 失败'}")

# ============================================================================
# 场景3：CodeReviewer只有基础工具（只读）
# ============================================================================
print(f"\n{'='*80}")
print("场景3：CodeReviewer - 只有基础工具（主要用于读取）")
print(f"{'='*80}\n")

reviewer = CodeReviewerAgent()
reviewer.set_project_context("demo")

print("1. CodeReviewer的可用工具:")
for tool in reviewer.get_available_tools():
    print(f"   - {tool['name']}")

print("\n2. 使用基础工具读取代码:")
result = reviewer.call_tool('read_file', file_path=code_path)
print(f"   状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
if result['success']:
    print(f"   内容:\n{result['output']}")

print("\n3. 使用抽象接口保存审查结果:")
result = reviewer.save_artifact(
    artifact_type="code_review",
    content="# 代码审查报告\n\n## 审查结果\n- 代码规范：通过\n- 质量评分：8/10"
)
print(f"   状态: {'✅ 成功' if result['success'] else '❌ 失败'}")

print("\n4. 尝试使用edit_file（应该失败，因为未启用）:")
result = reviewer.call_tool(
    'edit_file',
    file_path=code_path,
    old_string="Hello",
    new_string="Hi"
)
print(f"   状态: {'❌ 失败' if not result['success'] else '✅ 成功'}")
if not result['success']:
    print(f"   错误: {result['error']}")

# ============================================================================
# 场景4：Tester使用基础工具 + run_command
# ============================================================================
print(f"\n{'='*80}")
print("场景4：Tester - 基础工具 + run_command")
print(f"{'='*80}\n")

tester = TesterAgent()
tester.set_project_context("demo")

print("1. Tester的可用工具:")
for tool in tester.get_available_tools():
    print(f"   - {tool['name']}")

print("\n2. 使用基础工具写入测试文件:")
test_path = os.path.join(project_path, "test_main.py")
result = tester.call_tool(
    'write_file',
    file_path=test_path,
    content="import main\n\ndef test_hello():\n    main.hello()\n    print('Test passed!')\n\nif __name__ == '__main__':\n    test_hello()\n"
)
print(f"   状态: {'✅ 成功' if result['success'] else '❌ 失败'}")

print("\n3. 使用专业工具运行测试:")
result = tester.call_tool(
    'run_command',
    command=f"cd {project_path} && python test_main.py"
)
print(f"   状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
if result['success']:
    print(f"   输出: {result['output']}")

print("\n4. 使用抽象接口保存测试结果:")
result = tester.save_artifact(
    artifact_type="test_report",
    content="# 测试报告\n\n## 测试结果\n- 测试用例数：1\n- 通过：1\n- 失败：0"
)
print(f"   状态: {'✅ 成功' if result['success'] else '❌ 失败'}")

# ============================================================================
# 总结
# ============================================================================
print(f"\n{'='*80}")
print("方案3总结：混合方案")
print(f"{'='*80}\n")

print("✅ 三层架构:")
print("   1. 基础工具层：所有Agent都有read_file、write_file、search能力")
print("   2. 抽象接口层：统一的save_memory()、save_artifact()、save_work_log()")
print("   3. 专业工具层：特定Agent的专业工具")
print()
print("✅ 工具分配:")
print("   - Requester: 基础工具（read, write, search）")
print("   - ProductManager: 基础工具")
print("   - Architect: 基础工具")
print("   - Developer: 基础工具 + edit_file + run_command")
print("   - CodeReviewer: 基础工具（主要用于读取）")
print("   - Tester: 基础工具 + run_command")
print("   - DevOps: 基础工具 + run_command")
print()
print("✅ 跨领域关注点:")
print("   - 记忆系统：所有Agent通过save_memory()统一保存")
print("   - 工作日志：所有Agent通过save_work_log()统一记录")
print("   - 产物管理：所有Agent通过save_artifact()统一保存")
print()
print("✅ 优点:")
print("   - 灵活性：Agent有底层工具的完整能力")
print("   - 一致性：通过高层抽象保证格式统一")
print("   - 扩展性：可以随时添加新的抽象方法")
print("   - 安全性：通过权限系统控制访问范围")

# 查看生成的文件
print(f"\n{'='*80}")
print("生成的文件:")
print(f"{'='*80}\n")

for root, dirs, files in os.walk(project_path):
    level = root.replace(project_path, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f"{subindent}{file}")
