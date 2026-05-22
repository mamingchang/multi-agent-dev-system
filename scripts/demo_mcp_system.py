#!/usr/bin/env python3
"""
MCP工具系统交互式演示

展示如何使用MCP工具系统的各种功能。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

# 配置日志
logging.basicConfig(
    level=logging.WARNING,  # 只显示WARNING以上的日志
    format='%(levelname)s - %(message)s'
)


def demo_basic_usage():
    """演示基础使用"""
    print("="*60)
    print("演示1: 基础使用 - 启动MCP系统并列出工具")
    print("="*60)

    from src.mcp.mcp_server_manager import MCPServerManager
    from src.mcp.mcp_tool_wrapper import create_mcp_tools

    # 启动MCP系统
    print("\n正在启动MCP服务器...")
    manager = MCPServerManager()
    manager.start_all_servers()

    # 获取状态
    status = manager.get_server_status()
    print(f"\n服务器状态:")
    for server_name, server_status in status.items():
        print(f"  ✓ {server_name}: {server_status['tool_count']} 个工具")

    # 创建工具
    mcp_tools = create_mcp_tools(manager)
    print(f"\n总共可用: {len(mcp_tools)} 个MCP工具")

    return manager, mcp_tools


def demo_file_operations(mcp_tools):
    """演示文件操作"""
    print("\n" + "="*60)
    print("演示2: 文件操作")
    print("="*60)

    # 1. 读取文件
    print("\n1. 读取README.md:")
    read_tool = mcp_tools.get('mcp__filesystem__read_file')
    if read_tool:
        result = read_tool.execute(path='README.md')
        if result.success:
            print(f"   ✓ 成功读取 {len(result.output)} 字符")
            print(f"   前100字符: {result.output[:100]}...")
        else:
            print(f"   ✗ 失败: {result.error}")

    # 2. 列出目录
    print("\n2. 列出src/目录:")
    list_tool = mcp_tools.get('mcp__filesystem__list_directory')
    if list_tool:
        result = list_tool.execute(path='src')
        if result.success:
            print(f"   ✓ 成功列出目录")
            # 解析输出（简化显示）
            lines = result.output.split('\n')[:5]
            for line in lines:
                if line.strip():
                    print(f"   {line}")
        else:
            print(f"   ✗ 失败: {result.error}")

    # 3. 获取文件信息
    print("\n3. 获取README.md文件信息:")
    info_tool = mcp_tools.get('mcp__filesystem__get_file_info')
    if info_tool:
        result = info_tool.execute(path='README.md')
        if result.success:
            print(f"   ✓ 成功获取文件信息")
            print(f"   {result.output[:200]}...")
        else:
            print(f"   ✗ 失败: {result.error}")


def demo_search_operations(mcp_tools):
    """演示搜索操作"""
    print("\n" + "="*60)
    print("演示3: 搜索操作")
    print("="*60)

    # 搜索Python文件
    print("\n搜索src/目录下的Python文件:")
    search_tool = mcp_tools.get('mcp__filesystem__search_files')
    if search_tool:
        result = search_tool.execute(
            path='src',
            pattern='*.py',
            recursive=True
        )
        if result.success:
            print(f"   ✓ 搜索完成")
            # 显示前5个结果
            lines = result.output.split('\n')[:5]
            for line in lines:
                if line.strip():
                    print(f"   {line}")
        else:
            print(f"   ✗ 失败: {result.error}")


def demo_tool_list(mcp_tools):
    """演示工具列表"""
    print("\n" + "="*60)
    print("演示4: 所有可用工具")
    print("="*60)

    print(f"\n共 {len(mcp_tools)} 个工具:\n")

    # 按服务器分组
    by_server = {}
    for tool_name, tool in mcp_tools.items():
        server = tool.server_name
        if server not in by_server:
            by_server[server] = []
        by_server[server].append((tool_name, tool))

    for server, tools in by_server.items():
        print(f"\n{server} 服务器 ({len(tools)} 个工具):")
        for tool_name, tool in tools:
            # 提取工具的简短名称
            short_name = tool.tool_name
            desc = tool.get_description().replace(f'[MCP:{server}] ', '')[:50]
            dangerous = "⚠️ " if tool.is_dangerous() else ""
            print(f"  {dangerous}{short_name}: {desc}...")


def demo_agent_integration():
    """演示Agent集成"""
    print("\n" + "="*60)
    print("演示5: Agent如何使用MCP工具")
    print("="*60)

    print("\nAgent配置示例:")
    print("""
    agent_config = {
        'name': 'file_processor',
        'role': '文件处理专家',
        'tools': {
            'inherit_global': True,
            'whitelist': [
                'mcp__filesystem__read_file',
                'mcp__filesystem__write_file',
                'mcp__filesystem__search_files'
            ]
        }
    }
    """)

    print("\nLLM输出示例:")
    print("""
    {
        "analysis": "需要读取配置文件",
        "tool_calls": [
            {
                "tool": "mcp__filesystem__read_file",
                "parameters": {
                    "path": "config/settings.json"
                }
            }
        ],
        "output": "正在读取配置文件..."
    }
    """)


def main():
    """主函数"""
    print("\n" + "🚀"*30)
    print("MCP工具系统交互式演示")
    print("🚀"*30 + "\n")

    manager = None
    mcp_tools = None

    try:
        # 演示1: 基础使用
        manager, mcp_tools = demo_basic_usage()

        # 演示2: 文件操作
        demo_file_operations(mcp_tools)

        # 演示3: 搜索操作
        demo_search_operations(mcp_tools)

        # 演示4: 工具列表
        demo_tool_list(mcp_tools)

        # 演示5: Agent集成
        demo_agent_integration()

        print("\n" + "="*60)
        print("✓ 演示完成")
        print("="*60)

        print("\n提示:")
        print("  - MCP工具已集成到工具注册表")
        print("  - Agent可以像使用内置工具一样使用MCP工具")
        print("  - 工具命名格式: mcp__<server>__<tool>")
        print("  - 配置文件: config/mcp/global_servers.json")

    except Exception as e:
        print(f"\n✗ 演示失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # 清理
        if manager:
            print("\n正在关闭MCP系统...")
            manager.shutdown_all_servers()
            print("✓ MCP系统已关闭")


if __name__ == '__main__':
    main()
