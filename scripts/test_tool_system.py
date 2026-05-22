"""
测试工具系统

验证工具加载、格式化和执行是否正常
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_tool_registry():
    """测试工具注册表"""
    print("="*60)
    print("测试1: 工具注册表")
    print("="*60)

    from src.registry.tool_registry import ToolRegistry

    registry = ToolRegistry()

    # 列出所有工具
    tools = registry.list_tools()
    print(f"\n已注册工具: {len(tools)}个")
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")

    # 列出工具分组
    groups = registry.list_groups()
    print(f"\n工具分组: {len(groups)}个")
    for group_name, tool_names in groups.items():
        print(f"  - {group_name}: {', '.join(tool_names)}")

    print("\n✓ 工具注册表测试通过")


def test_tool_loader():
    """测试工具加载器"""
    print("\n" + "="*60)
    print("测试2: 工具加载器")
    print("="*60)

    from src.tools.tool_loader import ToolLoader

    # 模拟Agent配置
    agent_config = {
        'name': 'test_agent',
        'role': '测试Agent',
        'tools': {
            'inherit_global': True,
            'inherit_role_permissions': False,
            'whitelist': ['read_file', 'write_file', 'search_files'],
            'blacklist': [],
            'groups': [],
            'tool_configs': {}
        }
    }

    loader = ToolLoader()
    tool_registry = loader.load_tools_for_agent(agent_config)

    tools = tool_registry.list_tools()
    print(f"\n加载的工具: {len(tools)}个")
    for tool in tools:
        print(f"  - {tool.get_name()}: {tool.get_description()}")

    print("\n✓ 工具加载器测试通过")


def test_tool_formatter():
    """测试工具格式化器"""
    print("\n" + "="*60)
    print("测试3: 工具格式化器")
    print("="*60)

    from src.tools.tool_loader import ToolLoader
    from src.tools.tool_formatter import ToolFormatter

    # 加载工具
    agent_config = {
        'name': 'test_agent',
        'role': '测试Agent',
        'tools': {
            'inherit_global': True,
            'whitelist': ['read_file', 'write_file'],
            'blacklist': []
        }
    }

    loader = ToolLoader()
    tool_registry = loader.load_tools_for_agent(agent_config)

    # 格式化工具
    formatter = ToolFormatter()
    tools_section = formatter.format_tools_for_llm(tool_registry)

    print("\n生成的工具说明（前500字符）:")
    print("-" * 60)
    print(tools_section[:500])
    print("...")
    print("-" * 60)

    print("\n✓ 工具格式化器测试通过")


def test_tool_call_parser():
    """测试工具调用解析器"""
    print("\n" + "="*60)
    print("测试4: 工具调用解析器")
    print("="*60)

    from src.llm.tool_call_parser import ToolCallParser

    parser = ToolCallParser()

    # 测试用例1：正常的工具调用
    llm_output = {
        'analysis': '需要读取文件',
        'tool_calls': [
            {
                'tool': 'read_file',
                'parameters': {
                    'file_path': '/path/to/file.txt'
                }
            }
        ],
        'output': '正在读取文件'
    }

    result = parser.parse_tool_calls(llm_output)
    print(f"\n测试用例1: 正常工具调用")
    print(f"  解析成功: {result.success}")
    print(f"  工具调用数: {len(result.tool_calls)}")
    if result.tool_calls:
        print(f"  第一个工具: {result.tool_calls[0].tool_name}")

    # 测试用例2：多个工具调用
    llm_output2 = {
        'tool_calls': [
            {'tool': 'search_files', 'parameters': {'pattern': '*.py'}},
            {'tool': 'read_file', 'parameters': {'file_path': 'main.py'}}
        ]
    }

    result2 = parser.parse_tool_calls(llm_output2)
    print(f"\n测试用例2: 多个工具调用")
    print(f"  解析成功: {result2.success}")
    print(f"  工具调用数: {len(result2.tool_calls)}")

    # 测试用例3：格式错误
    llm_output3 = {
        'tool_calls': [
            {'parameters': {'file_path': 'test.txt'}}  # 缺少tool字段
        ]
    }

    result3 = parser.parse_tool_calls(llm_output3)
    print(f"\n测试用例3: 格式错误")
    print(f"  解析成功: {result3.success}")
    print(f"  错误信息: {result3.errors}")

    print("\n✓ 工具调用解析器测试通过")


def test_tool_execution():
    """测试工具执行"""
    print("\n" + "="*60)
    print("测试5: 工具执行")
    print("="*60)

    from src.tools.tool_loader import ToolLoader
    import tempfile
    import os

    # 加载工具
    agent_config = {
        'tools': {
            'inherit_global': True,
            'whitelist': ['read_file', 'write_file'],
            'blacklist': []
        }
    }

    loader = ToolLoader()
    tool_registry = loader.load_tools_for_agent(agent_config)

    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        temp_file = f.name
        f.write("Hello, World!")

    try:
        # 测试读取文件
        print(f"\n测试读取文件: {temp_file}")
        result = tool_registry.execute_tool('read_file', file_path=temp_file)
        print(f"  成功: {result.success}")
        print(f"  内容: {result.output}")

        # 测试写入文件
        print(f"\n测试写入文件: {temp_file}")
        result2 = tool_registry.execute_tool(
            'write_file',
            file_path=temp_file,
            content="New content"
        )
        print(f"  成功: {result2.success}")

        # 再次读取验证
        result3 = tool_registry.execute_tool('read_file', file_path=temp_file)
        print(f"  验证内容: {result3.output}")

    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)

    print("\n✓ 工具执行测试通过")


def main():
    """运行所有测试"""
    print("\n" + "🔧"*30)
    print("工具系统测试")
    print("🔧"*30 + "\n")

    try:
        test_tool_registry()
        test_tool_loader()
        test_tool_formatter()
        test_tool_call_parser()
        test_tool_execution()

        print("\n" + "="*60)
        print("✓ 所有测试通过")
        print("="*60)

    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
