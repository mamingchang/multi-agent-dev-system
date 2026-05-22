"""
演示Agent的完整调用过程

展示从任务创建到Agent处理的完整流程，包括：
1. 任务创建
2. Agent初始化
3. 工具调用循环
4. 记忆和产物保存
"""

import sys
import os
sys.path.insert(0, '/home/mamingchang/multi-agent-dev-system')

from src.agents.developer import DeveloperAgent
from src.workflow.task import Task, TaskStatus
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
project_path = "/tmp/agent_demo_project"
os.makedirs(project_path, exist_ok=True)

# 注册项目权限
perm_manager = get_permission_manager()
perm_manager.register_project(
    project_id="agent_demo",
    project_path=project_path,
    level=PermissionLevel.FULL
)

print("=" * 80)
print("Agent调用过程演示：Developer Agent")
print("=" * 80)

# ============================================================================
# 步骤1：创建任务
# ============================================================================
print(f"\n{'='*80}")
print("步骤1：创建任务")
print(f"{'='*80}\n")

task = Task(
    task_id="TASK-001",
    title="实现一个简单的计算器",
    description="创建一个Python计算器，支持加减乘除四则运算"
)

print(f"任务ID: {task.task_id}")
print(f"任务标题: {task.title}")
print(f"任务描述: {task.description}")
print(f"任务状态: {task.status.value}")

# 添加一些前置产物（模拟架构设计）
task.add_artifact(
    artifact_type="architecture_design",
    content={
        "technology_stack": {
            "backend": {
                "framework": "Python",
                "language": "Python 3.8+"
            }
        },
        "modules": [
            {
                "name": "calculator",
                "description": "计算器核心模块",
                "functions": ["add", "subtract", "multiply", "divide"]
            }
        ]
    },
    agent="Architect"
)

print(f"\n前置产物: {len(task.artifacts)}个")
for artifact in task.artifacts:
    print(f"  - {artifact['type']} (来自 {artifact['agent']})")

# ============================================================================
# 步骤2：初始化Agent
# ============================================================================
print(f"\n{'='*80}")
print("步骤2：初始化Developer Agent")
print(f"{'='*80}\n")

developer = DeveloperAgent()

print(f"Agent名称: {developer.name}")
print(f"Agent角色: {developer.role}")
print(f"LLM客户端: {'已初始化' if developer.llm_client else '未初始化（降级模式）'}")

print(f"\n可用工具: {len(developer.enabled_tools)}个")
for tool_name in developer.enabled_tools:
    print(f"  - {tool_name}")

# 设置项目上下文（用于权限检查）
developer.set_project_context("agent_demo")
print(f"\n项目上下文: agent_demo")

# ============================================================================
# 步骤3：Agent处理任务（不使用LLM，手动模拟）
# ============================================================================
print(f"\n{'='*80}")
print("步骤3：Agent处理任务（手动模拟工具调用）")
print(f"{'='*80}\n")

# 更新任务状态
task.update_status(TaskStatus.IN_DEVELOPMENT, developer.name)
print(f"任务状态: {task.status.value}")

# 3.1 使用基础工具：写入代码文件
print(f"\n[迭代1] 使用write_file创建calculator.py")
code_path = os.path.join(project_path, "calculator.py")
result = developer.call_tool(
    'write_file',
    file_path=code_path,
    content="""\"\"\"
简单的计算器模块
\"\"\"

def add(a, b):
    \"\"\"加法\"\"\"
    return a + b

def subtract(a, b):
    \"\"\"减法\"\"\"
    return a - b

def multiply(a, b):
    \"\"\"乘法\"\"\"
    return a * b

def divide(a, b):
    \"\"\"除法\"\"\"
    if b == 0:
        raise ValueError("除数不能为0")
    return a / b
"""
)
print(f"  状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
if result['success']:
    print(f"  输出: {result['output']}")
    print(f"  元数据: {result['metadata']}")

# 3.2 使用基础工具：读取刚写入的文件
print(f"\n[迭代2] 使用read_file读取calculator.py")
result = developer.call_tool('read_file', file_path=code_path)
print(f"  状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
if result['success']:
    print(f"  文件大小: {result['metadata']['size']} 字节")
    print(f"  文件行数: {result['metadata']['lines']} 行")
    print(f"  内容预览: {result['output'][:100]}...")

# 3.3 使用专业工具：编辑代码（添加main函数）
print(f"\n[迭代3] 使用edit_file添加main函数")
result = developer.call_tool(
    'edit_file',
    file_path=code_path,
    old_string='def divide(a, b):\n    """除法"""\n    if b == 0:\n        raise ValueError("除数不能为0")\n    return a / b',
    new_string='def divide(a, b):\n    """除法"""\n    if b == 0:\n        raise ValueError("除数不能为0")\n    return a / b\n\nif __name__ == "__main__":\n    print("计算器测试")\n    print(f"10 + 5 = {add(10, 5)}")\n    print(f"10 - 5 = {subtract(10, 5)}")\n    print(f"10 * 5 = {multiply(10, 5)}")\n    print(f"10 / 5 = {divide(10, 5)}")'
)
print(f"  状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
if result['success']:
    print(f"  输出: {result['output']}")
    print(f"  替换次数: {result['metadata']['replacements']}")

# 3.4 使用专业工具：运行代码测试
print(f"\n[迭代4] 使用run_command运行测试")
result = developer.call_tool(
    'run_command',
    command=f"python3 {code_path}"
)
print(f"  状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
if result['success']:
    print(f"  输出:\n{result['output']}")
else:
    print(f"  错误: {result['error']}")

# 3.5 使用基础工具：搜索代码
print(f"\n[迭代5] 使用search_code搜索函数定义")
result = developer.call_tool(
    'search_code',
    pattern=r'def \w+\(',
    path=project_path,
    file_pattern="*.py"
)
print(f"  状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
if result['success']:
    print(f"  找到 {result['metadata']['count']} 个匹配")
    for match in result['output'][:5]:
        print(f"    {match['file']}:{match['line']} - {match['content']}")

# ============================================================================
# 步骤4：使用抽象接口保存记忆和产物
# ============================================================================
print(f"\n{'='*80}")
print("步骤4：使用抽象接口保存记忆和产物")
print(f"{'='*80}\n")

# 4.1 保存实现记忆
print("[记忆] 保存实现细节")
result = developer.save_memory(
    memory_type="implementation_detail",
    content={
        "module": "calculator.py",
        "functions": ["add", "subtract", "multiply", "divide"],
        "decision": "使用简单的函数实现，添加了除零检查",
        "test_result": "所有测试通过"
    }
)
print(f"  状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
if result['success']:
    print(f"  保存位置: {result['output']}")

# 4.2 保存工作日志
print("\n[日志] 保存工作日志")
result = developer.save_work_log(
    action="implement_calculator",
    details={
        "task_id": task.task_id,
        "files_created": ["calculator.py"],
        "lines_of_code": 30,
        "duration": "15min"
    }
)
print(f"  状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
if result['success']:
    print(f"  保存位置: {result['output']}")

# 4.3 保存代码产物
print("\n[产物] 保存代码文档")
result = developer.save_artifact(
    artifact_type="code_documentation",
    content="""# Calculator Module

## 功能
- 加法 (add)
- 减法 (subtract)
- 乘法 (multiply)
- 除法 (divide)

## 使用示例
```python
from calculator import add, subtract, multiply, divide

result = add(10, 5)  # 15
result = divide(10, 5)  # 2.0
```

## 测试结果
所有测试通过 ✅
"""
)
print(f"  状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
if result['success']:
    print(f"  保存位置: {result['output']}")

# ============================================================================
# 步骤5：添加产物到任务
# ============================================================================
print(f"\n{'='*80}")
print("步骤5：添加产物到任务")
print(f"{'='*80}\n")

task.add_artifact(
    artifact_type="code",
    content={
        "files": [
            {
                "path": "calculator.py",
                "content": open(code_path).read()
            }
        ],
        "tests": [],
        "documentation": "计算器模块实现完成"
    },
    agent=developer.name
)

print(f"任务产物: {len(task.artifacts)}个")
for artifact in task.artifacts:
    print(f"  - {artifact['type']} (来自 {artifact['agent']})")

# ============================================================================
# 步骤6：查看生成的文件结构
# ============================================================================
print(f"\n{'='*80}")
print("步骤6：查看生成的文件结构")
print(f"{'='*80}\n")

def print_tree(path, prefix="", max_depth=3, current_depth=0):
    """打印目录树"""
    if current_depth >= max_depth:
        return

    try:
        items = sorted(os.listdir(path))
        for i, item in enumerate(items):
            item_path = os.path.join(path, item)
            is_last = i == len(items) - 1

            print(f"{prefix}{'└── ' if is_last else '├── '}{item}")

            if os.path.isdir(item_path):
                extension = "    " if is_last else "│   "
                print_tree(item_path, prefix + extension, max_depth, current_depth + 1)
    except PermissionError:
        pass

print(f"{project_path}/")
print_tree(project_path)

# ============================================================================
# 总结
# ============================================================================
print(f"\n{'='*80}")
print("调用过程总结")
print(f"{'='*80}\n")

print("✅ Agent调用流程:")
print("   1. 创建任务 (Task)")
print("   2. 初始化Agent (DeveloperAgent)")
print("   3. 设置项目上下文 (set_project_context)")
print("   4. 工具调用循环:")
print("      - write_file: 创建代码文件")
print("      - read_file: 读取文件内容")
print("      - edit_file: 编辑代码")
print("      - run_command: 运行测试")
print("      - search_code: 搜索代码")
print("   5. 使用抽象接口:")
print("      - save_memory(): 保存实现记忆")
print("      - save_work_log(): 保存工作日志")
print("      - save_artifact(): 保存代码文档")
print("   6. 添加产物到任务 (task.add_artifact)")
print()
print("✅ 权限检查:")
print("   - 每次工具调用都会检查项目权限")
print("   - 只能访问项目目录内的文件")
print("   - 危险命令会被拦截")
print()
print("✅ 三层架构:")
print("   - 基础工具层: read_file, write_file, search_files, search_code")
print("   - 抽象接口层: save_memory, save_work_log, save_artifact")
print("   - 专业工具层: edit_file, run_command")
print()
print("✅ 与LLM集成:")
print("   - 如果LLM可用，Agent会使用_execute_with_tools()进入工具调用循环")
print("   - LLM生成JSON格式的工具调用")
print("   - 系统执行工具并返回结果给LLM")
print("   - LLM根据结果决定下一步操作")
print("   - 循环直到任务完成或达到最大迭代次数")
