#!/usr/bin/env python3
"""
完整系统功能测试 - 通过CLI测试Agent + MCP工具集成

测试场景：
1. 启动MCP系统
2. 创建一个Agent（配置使用MCP工具）
3. Agent处理任务（使用MCP工具）
4. 验证结果
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_mcp_system():
    """测试1: MCP系统启动"""
    print("\n" + "="*60)
    print("测试1: MCP系统启动")
    print("="*60)

    from src.mcp.mcp_server_manager import MCPServerManager
    from src.mcp.mcp_tool_wrapper import create_mcp_tools

    manager = MCPServerManager()
    manager.start_all_servers()

    mcp_tools = create_mcp_tools(manager)

    print(f"\n✓ MCP系统启动成功")
    print(f"  可用工具: {len(mcp_tools)} 个")

    status = manager.get_server_status()
    for server, info in status.items():
        print(f"  - {server}: {info['tool_count']} 个工具")

    return manager, mcp_tools


def test_tool_registry_integration(mcp_tools):
    """测试2: 工具注册表集成"""
    print("\n" + "="*60)
    print("测试2: 工具注册表集成")
    print("="*60)

    from src.registry.tool_registry import ToolRegistry

    registry = ToolRegistry()

    # 注册MCP工具
    print("\n注册MCP工具到工具注册表...")
    registered = 0
    skipped = 0
    for tool_name, tool in mcp_tools.items():
        # 检查是否已存在
        if registry.get(tool_name):
            skipped += 1
            continue

        metadata = {
            'name': tool_name,
            'display_name': tool.get_name(),
            'description': tool.get_description(),
            'type': 'mcp',
            'class_path': f'mcp.{tool.server_name}.{tool.tool_name}',
            'permission_level': tool.get_required_permission(),
            'dangerous': tool.is_dangerous(),
            'enabled': True,
            'tags': ['mcp', tool.server_name],
            'author': 'mcp',
            'mcp_server': tool.server_name,
            'mcp_tool': tool.tool_name
        }
        registry.register(tool_name, metadata)
        registered += 1

    # 验证注册
    all_tools = registry.list_all()
    mcp_tool_count = len([t for t in all_tools if t.get('type') == 'mcp'])

    print(f"\n✓ 工具注册成功")
    print(f"  新注册: {registered} 个")
    print(f"  已存在: {skipped} 个")
    print(f"  总工具数: {len(all_tools)}")
    print(f"  MCP工具数: {mcp_tool_count}")
    print(f"  内置工具数: {len(all_tools) - mcp_tool_count}")

    return registry


def test_agent_with_mcp_tools(mcp_tools):
    """测试3: Agent使用MCP工具"""
    print("\n" + "="*60)
    print("测试3: Agent使用MCP工具")
    print("="*60)

    from src.agents.generic_agent import GenericAgent
    from src.workflow.task import Task

    # 创建Agent配置
    agent_config = {
        'name': 'file_agent',
        'role': '文件处理专家',
        'description': '专注于文件读写和处理',
        'system_prompt': '''你是一个文件处理专家。

你的职责：
1. 读取和分析文件
2. 搜索文件
3. 获取文件信息

你可以使用以下MCP工具：
- mcp__filesystem__read_file: 读取文件
- mcp__filesystem__list_directory: 列出目录
- mcp__filesystem__search_files: 搜索文件

请根据任务需求使用合适的工具。

输出格式（JSON）：
{
    "analysis": "任务分析",
    "tool_calls": [
        {
            "tool": "工具名称",
            "parameters": {...}
        }
    ],
    "output": "执行结果",
    "next_agent": null
}
''',
        'capabilities': ['文件读取', '文件搜索'],
        'tools': {
            'inherit_global': False,
            'whitelist': [
                'mcp__filesystem__read_file',
                'mcp__filesystem__list_directory',
                'mcp__filesystem__search_files'
            ]
        },
        'llm': {
            'provider': 'anthropic',
            'model': 'claude-sonnet-4-5'
        }
    }

    print("\n创建Agent...")
    agent = GenericAgent(
        name='file_agent',
        config=agent_config
    )

    # 手动添加MCP工具到Agent的工具注册表
    print("\n添加MCP工具到Agent...")
    added_count = 0
    for tool_name in agent_config['tools']['whitelist']:
        if tool_name in mcp_tools:
            tool = mcp_tools[tool_name]
            # 直接添加到Agent的tool_registry
            if hasattr(agent, 'tool_registry') and agent.tool_registry:
                agent.tool_registry.tools[tool_name] = tool
                added_count += 1

    print(f"✓ Agent创建成功")
    print(f"  添加MCP工具: {added_count} 个")
    if hasattr(agent, 'tool_registry') and agent.tool_registry:
        print(f"  可用工具总数: {len(agent.tool_registry.tools)} 个")
        for tool_name in list(agent.tool_registry.tools.keys())[:5]:
            print(f"    - {tool_name}")

    return agent


def test_agent_task_execution(agent):
    """测试4: Agent执行任务"""
    print("\n" + "="*60)
    print("测试4: Agent执行任务")
    print("="*60)

    from src.workflow.task import Task

    # 创建任务：读取README文件
    task = Task(
        task_id='test_001',
        title='读取项目README文件',
        description='请读取项目根目录的README.md文件，并告诉我文件的主要内容'
    )

    print(f"\n任务: {task.title}")
    print(f"描述: {task.description}")

    # 模拟Agent处理（不调用LLM，直接构造工具调用）
    print("\n模拟Agent决策：使用 mcp__filesystem__read_file 工具")

    # 直接调用工具
    if hasattr(agent, 'tool_registry') and agent.tool_registry:
        tool = agent.tool_registry.tools.get('mcp__filesystem__read_file')
    else:
        tool = None

    if not tool:
        print("✗ 工具不可用")
        return False

    result = tool.execute(path='README.md')

    if result.success:
        content = result.output
        print(f"\n✓ 工具执行成功")
        print(f"  文件长度: {len(content)} 字符")
        print(f"\n文件内容（前300字符）:")
        print("-"*60)
        print(content[:300])
        print("...")
        print("-"*60)
        return True
    else:
        print(f"\n✗ 工具执行失败: {result.error}")
        return False


def test_multiple_tool_calls(agent):
    """测试5: 多个工具调用"""
    print("\n" + "="*60)
    print("测试5: 多个工具调用（搜索+读取）")
    print("="*60)

    # 任务1: 搜索Python文件
    print("\n步骤1: 搜索src/mcp目录下的Python文件")
    if hasattr(agent, 'tool_registry') and agent.tool_registry:
        search_tool = agent.tool_registry.tools.get('mcp__filesystem__search_files')
    else:
        search_tool = None

    if search_tool:
        result = search_tool.execute(path='src/mcp', pattern='*.py', recursive=False)
        if result.success:
            files = result.output.split('\n')
            print(f"✓ 找到 {len(files)} 个文件")
            for i, f in enumerate(files[:3], 1):
                if f.strip():
                    print(f"  {i}. {f}")
        else:
            print(f"✗ 搜索失败: {result.error}")
            return False
    else:
        print("✗ 搜索工具不可用")
        return False

    # 任务2: 读取第一个文件
    if files and files[0].strip():
        first_file = files[0].strip()
        print(f"\n步骤2: 读取第一个文件: {first_file}")

        if hasattr(agent, 'tool_registry') and agent.tool_registry:
            read_tool = agent.tool_registry.tools.get('mcp__filesystem__read_file')
        else:
            read_tool = None

        if read_tool:
            # 提取相对路径
            if 'multi-agent-dev-system/' in first_file:
                rel_path = first_file.split('multi-agent-dev-system/')[1]
            else:
                rel_path = first_file

            result = read_tool.execute(path=rel_path)
            if result.success:
                content = result.output
                print(f"✓ 读取成功")
                print(f"  文件长度: {len(content)} 字符")
                print(f"\n前200字符:")
                print("-"*60)
                print(content[:200])
                print("...")
                print("-"*60)
                return True
            else:
                print(f"✗ 读取失败: {result.error}")
                return False
        else:
            print("✗ 读取工具不可用")
            return False

    return False


def test_tool_permissions(agent):
    """测试6: 工具权限控制"""
    print("\n" + "="*60)
    print("测试6: 工具权限控制")
    print("="*60)

    # 尝试使用不在白名单中的工具
    print("\n尝试使用未授权的工具: mcp__filesystem__write_file")

    if hasattr(agent, 'tool_registry') and agent.tool_registry:
        write_tool = agent.tool_registry.tools.get('mcp__filesystem__write_file')
    else:
        write_tool = None

    if write_tool:
        print("✗ 权限控制失败：Agent可以访问未授权的工具")
        return False
    else:
        print("✓ 权限控制正常：Agent无法访问未授权的工具")

    # 验证只能使用白名单中的工具
    print("\n验证白名单工具:")
    whitelist = ['mcp__filesystem__read_file', 'mcp__filesystem__list_directory', 'mcp__filesystem__search_files']

    if not hasattr(agent, 'tool_registry') or not agent.tool_registry:
        print("  ✗ Agent没有tool_registry")
        return False

    for tool_name in whitelist:
        if tool_name in agent.tool_registry.tools:
            print(f"  ✓ {tool_name} - 可访问")
        else:
            print(f"  ✗ {tool_name} - 不可访问")
            return False

    return True


def main():
    """主函数"""
    print("\n" + "🧪"*30)
    print("完整系统功能测试 - Agent + MCP工具集成")
    print("🧪"*30)

    manager = None
    success_count = 0
    total_tests = 6

    try:
        # 测试1: MCP系统启动
        manager, mcp_tools = test_mcp_system()
        success_count += 1

        # 测试2: 工具注册表集成
        registry = test_tool_registry_integration(mcp_tools)
        success_count += 1

        # 测试3: Agent使用MCP工具
        agent = test_agent_with_mcp_tools(mcp_tools)
        success_count += 1

        # 测试4: Agent执行任务
        if test_agent_task_execution(agent):
            success_count += 1

        # 测试5: 多个工具调用
        if test_multiple_tool_calls(agent):
            success_count += 1

        # 测试6: 工具权限控制
        if test_tool_permissions(agent):
            success_count += 1

        # 总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        print(f"\n通过: {success_count}/{total_tests} 个测试")

        if success_count == total_tests:
            print("\n✓ 所有测试通过！系统功能正常")
            return 0
        else:
            print(f"\n⚠️  {total_tests - success_count} 个测试失败")
            return 1

    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # 清理
        if manager:
            print("\n正在关闭MCP系统...")
            manager.shutdown_all_servers()
            print("✓ MCP系统已关闭")


if __name__ == '__main__':
    sys.exit(main())
