#!/usr/bin/env python3
"""
MCP工具CLI - 直接执行MCP工具任务

用法:
    python3 cli/mcp_tool.py <tool_name> [参数...]

示例:
    # 读取文件
    python3 cli/mcp_tool.py read_file --path README.md

    # 列出目录
    python3 cli/mcp_tool.py list_directory --path src

    # 搜索文件
    python3 cli/mcp_tool.py search_files --path src --pattern "*.py" --recursive

    # 获取文件信息
    python3 cli/mcp_tool.py get_file_info --path README.md
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
import json

# 配置日志
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s - %(message)s'
)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='MCP工具CLI - 直接执行MCP工具任务',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  读取文件:
    %(prog)s read_file --path README.md

  列出目录:
    %(prog)s list_directory --path src

  搜索文件:
    %(prog)s search_files --path src --pattern "*.py" --recursive

  获取文件信息:
    %(prog)s get_file_info --path README.md

  查看目录树:
    %(prog)s directory_tree --path src/mcp
        """
    )

    parser.add_argument('tool', nargs='?', help='工具名称（不需要mcp__filesystem__前缀）')
    parser.add_argument('--path', help='文件或目录路径')
    parser.add_argument('--pattern', help='搜索模式（如 *.py）')
    parser.add_argument('--recursive', action='store_true', help='递归搜索')
    parser.add_argument('--content', help='文件内容（用于写入）')
    parser.add_argument('--json', action='store_true', help='以JSON格式输出')
    parser.add_argument('--list-tools', action='store_true', help='列出所有可用工具')

    return parser.parse_args()


def list_available_tools(mcp_tools):
    """列出所有可用工具"""
    print("\n可用的MCP工具:")
    print("="*60)

    # 按服务器分组
    by_server = {}
    for tool_name, tool in mcp_tools.items():
        server = tool.server_name
        if server not in by_server:
            by_server[server] = []
        by_server[server].append(tool)

    for server, tools in by_server.items():
        print(f"\n{server} 服务器:")
        for tool in tools:
            short_name = tool.tool_name
            desc = tool.get_description().replace(f'[MCP:{server}] ', '')[:60]
            print(f"  {short_name}")
            print(f"    {desc}...")

    print("\n" + "="*60)
    print("\n使用方法:")
    print("  python3 cli/mcp_tool.py <tool_name> --path <path>")
    print("\n示例:")
    print("  python3 cli/mcp_tool.py read_file --path README.md")


def execute_tool(mcp_tools, tool_name, args):
    """执行工具"""
    # 构建完整工具名
    full_tool_name = f"mcp__filesystem__{tool_name}"

    # 查找工具
    tool = mcp_tools.get(full_tool_name)
    if not tool:
        print(f"✗ 工具不存在: {tool_name}")
        print(f"\n提示: 使用 --list-tools 查看所有可用工具")
        return False

    # 构建参数
    params = {}
    if args.path:
        params['path'] = args.path
    if args.pattern:
        params['pattern'] = args.pattern
    if args.recursive:
        params['recursive'] = True
    if args.content:
        params['content'] = args.content

    # 执行工具
    print(f"执行工具: {tool_name}")
    if params:
        print(f"参数: {params}")
    print()

    result = tool.execute(**params)

    # 输出结果
    if args.json:
        # JSON格式输出
        output = {
            'success': result.success,
            'output': result.output,
            'error': result.error,
            'metadata': result.metadata
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        # 普通格式输出
        if result.success:
            print("✓ 执行成功\n")
            print("-"*60)
            print(result.output)
            print("-"*60)
        else:
            print(f"✗ 执行失败: {result.error}")

    return result.success


def main():
    """主函数"""
    args = parse_args()

    # 启动MCP系统
    from src.mcp.mcp_server_manager import MCPServerManager
    from src.mcp.mcp_tool_wrapper import create_mcp_tools

    print("正在启动MCP系统...")
    manager = MCPServerManager()
    manager.start_all_servers()

    mcp_tools = create_mcp_tools(manager)
    print(f"✓ MCP系统启动成功 ({len(mcp_tools)} 个工具)\n")

    try:
        # 列出工具
        if args.list_tools:
            list_available_tools(mcp_tools)
            return 0

        # 检查是否提供了工具名
        if not args.tool:
            print("✗ 错误: 请提供工具名称")
            print("\n使用 --list-tools 查看所有可用工具")
            print("或使用 -h 查看帮助")
            return 1

        # 执行工具
        success = execute_tool(mcp_tools, args.tool, args)
        return 0 if success else 1

    finally:
        # 关闭MCP系统
        print("\n正在关闭MCP系统...")
        manager.shutdown_all_servers()


if __name__ == '__main__':
    sys.exit(main())
