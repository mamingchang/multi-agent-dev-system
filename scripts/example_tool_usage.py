"""
工具系统使用示例

演示如何在Agent中使用工具系统
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def example_agent_with_tools():
    """示例：创建带工具的Agent"""
    print("="*60)
    print("示例：创建带工具的Agent")
    print("="*60)

    from src.agents.generic_agent import GenericAgent

    # Agent配置
    config = {
        'name': 'file_processor',
        'role': '文件处理专家',
        'description': '专注于文件读写和处理',
        'system_prompt': '''你是一个文件处理专家。

你的职责：
1. 读取和分析文件
2. 处理文件内容
3. 生成新文件

请使用可用的工具来完成任务。''',
        'capabilities': ['文件读取', '文件写入', '文件搜索'],
        'tools': {
            'inherit_global': True,
            'inherit_role_permissions': False,
            'whitelist': ['read_file', 'write_file', 'search_files'],
            'blacklist': [],
            'groups': [],
            'tool_configs': {}
        },
        'llm': {
            'provider': 'anthropic',
            'model': 'claude-sonnet-4-5'
        }
    }

    # 创建Agent
    agent = GenericAgent(
        name='file_processor',
        config=config
    )

    print(f"\n✓ Agent创建成功")
    print(f"  可用工具: {len(agent.tool_registry.list_tools())}个")

    # 显示System Prompt（包含工具说明）
    system_prompt = agent._build_system_prompt()
    print(f"\n生成的System Prompt长度: {len(system_prompt)}字符")
    print(f"\n前300字符:")
    print("-" * 60)
    print(system_prompt[:300])
    print("...")
    print("-" * 60)


def example_tool_call_simulation():
    """示例：模拟工具调用"""
    print("\n" + "="*60)
    print("示例：模拟工具调用")
    print("="*60)

    from src.tools.tool_loader import ToolLoader
    from src.llm.tool_call_parser import ToolCallParser
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

    # 模拟LLM输出（包含工具调用）
    llm_output = {
        'analysis': '需要创建一个测试文件并读取它',
        'tool_calls': [
            {
                'tool': 'write_file',
                'parameters': {
                    'file_path': '/tmp/test_tool_system.txt',
                    'content': 'Hello from tool system!'
                }
            },
            {
                'tool': 'read_file',
                'parameters': {
                    'file_path': '/tmp/test_tool_system.txt'
                }
            }
        ],
        'output': '已创建并读取测试文件'
    }

    # 解析工具调用
    parser = ToolCallParser()
    parse_result = parser.parse_tool_calls(llm_output)

    print(f"\n解析结果:")
    print(f"  成功: {parse_result.success}")
    print(f"  工具调用数: {len(parse_result.tool_calls)}")

    # 执行工具调用
    print(f"\n执行工具调用:")
    tool_results = []

    for i, tool_call in enumerate(parse_result.tool_calls, 1):
        print(f"\n  {i}. {tool_call.tool_name}")
        print(f"     参数: {tool_call.parameters}")

        result = tool_registry.execute_tool(
            tool_call.tool_name,
            **tool_call.parameters
        )

        print(f"     成功: {result.success}")
        if result.success:
            print(f"     输出: {result.output}")
        else:
            print(f"     错误: {result.error}")

        tool_results.append({
            'tool': tool_call.tool_name,
            'success': result.success,
            'output': result.output,
            'error': result.error
        })

    # 清理
    if os.path.exists('/tmp/test_tool_system.txt'):
        os.remove('/tmp/test_tool_system.txt')

    print(f"\n✓ 工具调用完成")


def example_role_permissions():
    """示例：角色权限"""
    print("\n" + "="*60)
    print("示例：角色权限")
    print("="*60)

    from src.tools.tool_loader import ToolLoader

    # 开发者：全部权限
    developer_config = {
        'role': '开发者',
        'tools': {
            'inherit_global': True,
            'inherit_role_permissions': True,
            'whitelist': [],
            'blacklist': []
        }
    }

    # 代码审查员：只读
    reviewer_config = {
        'role': '代码审查员',
        'tools': {
            'inherit_global': True,
            'inherit_role_permissions': True,
            'whitelist': [],
            'blacklist': []
        }
    }

    loader = ToolLoader()

    developer_tools = loader.load_tools_for_agent(developer_config)
    reviewer_tools = loader.load_tools_for_agent(reviewer_config)

    print(f"\n开发者可用工具: {len(developer_tools.list_tools())}个")
    for tool in developer_tools.list_tools():
        print(f"  - {tool.get_name()}")

    print(f"\n代码审查员可用工具: {len(reviewer_tools.list_tools())}个")
    for tool in reviewer_tools.list_tools():
        print(f"  - {tool.get_name()}")

    print(f"\n✓ 角色权限正常工作")


def main():
    """运行所有示例"""
    print("\n" + "📚"*30)
    print("工具系统使用示例")
    print("📚"*30 + "\n")

    try:
        example_agent_with_tools()
        example_tool_call_simulation()
        example_role_permissions()

        print("\n" + "="*60)
        print("✓ 所有示例运行成功")
        print("="*60)

    except Exception as e:
        print(f"\n✗ 示例运行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
