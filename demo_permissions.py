"""
演示权限系统

展示如何为不同项目配置不同的权限
"""

import sys
import os
sys.path.insert(0, '/home/mamingchang/multi-agent-dev-system')

from src.permissions import get_permission_manager, PermissionLevel, Permission
from src.tools.base import get_tool_registry
from src.tools.file_tools import ReadTool, WriteTool
from src.tools.shell_tools import BashTool

# 注册工具
registry = get_tool_registry()
registry.register(ReadTool())
registry.register(WriteTool())
registry.register(BashTool())

# 获取权限管理器
perm_manager = get_permission_manager()

print("=" * 80)
print("权限系统演示")
print("=" * 80)

# 创建测试项目目录
project1_path = "/tmp/test_project1"
project2_path = "/tmp/test_project2"
os.makedirs(project1_path, exist_ok=True)
os.makedirs(project2_path, exist_ok=True)

# 场景1：只读项目
print(f"\n{'='*80}")
print("场景1：只读项目")
print(f"{'='*80}\n")

perm_manager.register_project(
    project_id="project1",
    project_path=project1_path,
    level=PermissionLevel.READ_ONLY
)

# 尝试读取文件（应该成功）
print("\n尝试读取文件...")
result = registry.execute_tool(
    "read_file",
    project_id="project1",
    file_path=os.path.join(project1_path, "test.txt")
)
print(f"状态: {result.status.value}")
if not result.is_success():
    print(f"错误: {result.error}")

# 尝试写入文件（应该失败）
print("\n尝试写入文件...")
result = registry.execute_tool(
    "write_file",
    project_id="project1",
    file_path=os.path.join(project1_path, "test.txt"),
    content="Hello World"
)
print(f"状态: {result.status.value}")
if not result.is_success():
    print(f"❌ 错误: {result.error}")

# 场景2：读写项目
print(f"\n{'='*80}")
print("场景2：读写项目")
print(f"{'='*80}\n")

perm_manager.register_project(
    project_id="project2",
    project_path=project2_path,
    level=PermissionLevel.READ_WRITE
)

# 尝试写入文件（应该成功）
print("\n尝试写入文件...")
result = registry.execute_tool(
    "write_file",
    project_id="project2",
    file_path=os.path.join(project2_path, "test.txt"),
    content="Hello World"
)
print(f"状态: {result.status.value}")
if result.is_success():
    print(f"✅ {result.output}")

# 尝试读取文件（应该成功）
print("\n尝试读取文件...")
result = registry.execute_tool(
    "read_file",
    project_id="project2",
    file_path=os.path.join(project2_path, "test.txt")
)
print(f"状态: {result.status.value}")
if result.is_success():
    print(f"✅ 内容: {result.output}")

# 尝试执行命令（应该失败，因为没有execute权限）
print("\n尝试执行命令...")
result = registry.execute_tool(
    "run_command",
    project_id="project2",
    command="ls -la"
)
print(f"状态: {result.status.value}")
if not result.is_success():
    print(f"❌ 错误: {result.error}")

# 场景3：完全控制项目
print(f"\n{'='*80}")
print("场景3：完全控制项目")
print(f"{'='*80}\n")

perm_manager.register_project(
    project_id="project3",
    project_path=project2_path,  # 复用project2的目录
    level=PermissionLevel.FULL
)

# 尝试执行命令（应该成功）
print("\n尝试执行命令...")
result = registry.execute_tool(
    "run_command",
    project_id="project3",
    command=f"ls -la {project2_path}"
)
print(f"状态: {result.status.value}")
if result.is_success():
    print(f"✅ 输出:\n{result.output}")

# 场景4：路径隔离
print(f"\n{'='*80}")
print("场景4：路径隔离（尝试访问项目外的文件）")
print(f"{'='*80}\n")

# 尝试读取项目外的文件（应该失败）
print("\n尝试读取项目外的文件...")
result = registry.execute_tool(
    "read_file",
    project_id="project2",
    file_path="/etc/passwd"  # 项目外的文件
)
print(f"状态: {result.status.value}")
if not result.is_success():
    print(f"❌ 错误: {result.error}")

# 场景5：自定义权限配置
print(f"\n{'='*80}")
print("场景5：自定义权限配置")
print(f"{'='*80}\n")

perm_manager.register_project(
    project_id="project4",
    project_path=project2_path,
    level=PermissionLevel.FULL,
    denied_paths=["secret"],  # 禁止访问secret目录
    allowed_commands=["ls", "cat", "python"]  # 只允许这些命令
)

# 创建secret目录
secret_path = os.path.join(project2_path, "secret")
os.makedirs(secret_path, exist_ok=True)

# 尝试访问secret目录（应该失败）
print("\n尝试访问禁止的目录...")
result = registry.execute_tool(
    "read_file",
    project_id="project4",
    file_path=os.path.join(secret_path, "secret.txt")
)
print(f"状态: {result.status.value}")
if not result.is_success():
    print(f"❌ 错误: {result.error}")

# 尝试执行允许的命令（应该成功）
print("\n尝试执行允许的命令...")
result = registry.execute_tool(
    "run_command",
    project_id="project4",
    command="ls"
)
print(f"状态: {result.status.value}")
if result.is_success():
    print(f"✅ 命令执行成功")

# 尝试执行不允许的命令（应该失败）
print("\n尝试执行不允许的命令...")
result = registry.execute_tool(
    "run_command",
    project_id="project4",
    command="rm -rf test.txt"
)
print(f"状态: {result.status.value}")
if not result.is_success():
    print(f"❌ 错误: {result.error}")

# 总结
print(f"\n{'='*80}")
print("权限系统总结")
print(f"{'='*80}\n")

print("✅ 权限级别:")
print("  - NONE: 无权限")
print("  - READ_ONLY: 只读（read, search）")
print("  - READ_WRITE: 读写（read, write, search）")
print("  - FULL: 完全控制（read, write, execute, delete, search）")

print("\n✅ 权限检查:")
print("  - 文件操作：检查文件路径是否在项目目录内")
print("  - 命令执行：检查命令是否在允许列表中")
print("  - 路径隔离：禁止访问项目外的文件")
print("  - 自定义配置：可以禁止特定目录、限制命令")

print("\n✅ 项目列表:")
for project_id in perm_manager.list_projects():
    info = perm_manager.get_project_info(project_id)
    print(f"  - {project_id}: {info['level']} @ {info['project_path']}")
