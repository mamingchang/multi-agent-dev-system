"""
演示工具调用能力

展示Agent如何使用工具来完成任务
"""

import sys
sys.path.insert(0, '/home/mamingchang/multi-agent-dev-system')

# 注册工具
from src.tools.base import get_tool_registry
from src.tools.file_tools import ReadTool, WriteTool, EditTool
from src.tools.shell_tools import BashTool
from src.tools.search_tools import GlobTool, GrepTool

# 注册所有工具
registry = get_tool_registry()
registry.register(ReadTool())
registry.register(WriteTool())
registry.register(EditTool())
registry.register(BashTool())
registry.register(GlobTool())
registry.register(GrepTool())

print("=" * 80)
print("工具调用演示")
print("=" * 80)

print(f"\n已注册工具: {registry.list_tools()}")

# 演示1：读取文件
print(f"\n{'='*80}")
print("演示1：读取文件")
print(f"{'='*80}\n")

result = registry.execute_tool(
    "read_file",
    file_path="/home/mamingchang/multi-agent-dev-system/README.md"
)

print(f"状态: {result.status.value}")
if result.is_success():
    print(f"内容长度: {len(result.output)} 字符")
    print(f"前100字符: {result.output[:100]}...")
else:
    print(f"错误: {result.error}")

# 演示2：搜索文件
print(f"\n{'='*80}")
print("演示2：搜索Python文件")
print(f"{'='*80}\n")

result = registry.execute_tool(
    "search_files",
    pattern="*.py",
    path="/home/mamingchang/multi-agent-dev-system/src/agents"
)

print(f"状态: {result.status.value}")
if result.is_success():
    print(f"找到 {len(result.output)} 个文件:")
    for file in result.output[:5]:
        print(f"  - {file}")
    if len(result.output) > 5:
        print(f"  ... 还有 {len(result.output) - 5} 个文件")
else:
    print(f"错误: {result.error}")

# 演示3：搜索代码
print(f"\n{'='*80}")
print("演示3：搜索代码中的'def process'")
print(f"{'='*80}\n")

result = registry.execute_tool(
    "search_code",
    pattern="def process",
    path="/home/mamingchang/multi-agent-dev-system/src/agents",
    file_pattern="*.py",
    max_results=5
)

print(f"状态: {result.status.value}")
if result.is_success():
    print(f"找到 {len(result.output)} 个匹配:")
    for match in result.output:
        print(f"  {match['file']}:{match['line']}")
        print(f"    {match['content']}")
else:
    print(f"错误: {result.error}")

# 演示4：写入文件
print(f"\n{'='*80}")
print("演示4：写入测试文件")
print(f"{'='*80}\n")

test_content = """# 测试文件

这是一个由工具系统创建的测试文件。

## 功能
- 读取文件
- 写入文件
- 搜索代码
"""

result = registry.execute_tool(
    "write_file",
    file_path="/tmp/tool_test.md",
    content=test_content
)

print(f"状态: {result.status.value}")
if result.is_success():
    print(f"输出: {result.output}")
    print(f"元数据: {result.metadata}")
else:
    print(f"错误: {result.error}")

# 演示5：编辑文件
print(f"\n{'='*80}")
print("演示5：编辑文件")
print(f"{'='*80}\n")

result = registry.execute_tool(
    "edit_file",
    file_path="/tmp/tool_test.md",
    old_string="测试文件",
    new_string="演示文件"
)

print(f"状态: {result.status.value}")
if result.is_success():
    print(f"输出: {result.output}")
    print(f"替换次数: {result.metadata['replacements']}")
else:
    print(f"错误: {result.error}")

# 验证编辑结果
result = registry.execute_tool(
    "read_file",
    file_path="/tmp/tool_test.md"
)

if result.is_success():
    print(f"\n编辑后的内容:")
    print(result.output)

# 演示6：执行命令
print(f"\n{'='*80}")
print("演示6：执行Shell命令")
print(f"{'='*80}\n")

result = registry.execute_tool(
    "run_command",
    command="ls -la /tmp/tool_test.md"
)

print(f"状态: {result.status.value}")
if result.is_success():
    print(f"输出:\n{result.output}")
else:
    print(f"错误: {result.error}")

print(f"\n{'='*80}")
print("演示完成！")
print(f"{'='*80}\n")

print("工具系统已就绪，Agent现在可以：")
print("  ✅ 读取文件")
print("  ✅ 写入文件")
print("  ✅ 编辑文件")
print("  ✅ 搜索文件")
print("  ✅ 搜索代码")
print("  ✅ 执行命令")
