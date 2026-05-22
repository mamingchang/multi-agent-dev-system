#!/usr/bin/env python3
"""
MCP工具系统 - 交互式试用

让你可以直接输入命令来试用MCP工具
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

# 配置日志（只显示错误）
logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s - %(message)s'
)


def print_menu(mcp_tools):
    """显示菜单"""
    print("\n" + "="*60)
    print("MCP工具试用 - 可用操作")
    print("="*60)
    print("1. 读取文件")
    print("2. 列出目录")
    print("3. 搜索文件")
    print("4. 获取文件信息")
    print("5. 查看目录树")
    print("6. 列出所有工具")
    print("0. 退出")
    print("="*60)


def read_file_demo(mcp_tools):
    """读取文件演示"""
    print("\n【读取文件】")
    path = input("请输入文件路径（默认: README.md）: ").strip()
    if not path:
        path = "README.md"

    tool = mcp_tools.get('mcp__filesystem__read_file')
    if not tool:
        print("✗ 工具不可用")
        return

    print(f"\n正在读取: {path}")
    result = tool.execute(path=path)

    if result.success:
        content = result.output
        print(f"\n✓ 读取成功！文件长度: {len(content)} 字符")

        show_all = input("\n显示全部内容？(y/n，默认显示前500字符): ").strip().lower()
        if show_all == 'y':
            print("\n" + "-"*60)
            print(content)
            print("-"*60)
        else:
            print("\n" + "-"*60)
            print(content[:500])
            if len(content) > 500:
                print(f"\n... (还有 {len(content)-500} 字符)")
            print("-"*60)
    else:
        print(f"\n✗ 读取失败: {result.error}")


def list_directory_demo(mcp_tools):
    """列出目录演示"""
    print("\n【列出目录】")
    path = input("请输入目录路径（默认: src）: ").strip()
    if not path:
        path = "src"

    tool = mcp_tools.get('mcp__filesystem__list_directory')
    if not tool:
        print("✗ 工具不可用")
        return

    print(f"\n正在列出目录: {path}")
    result = tool.execute(path=path)

    if result.success:
        print(f"\n✓ 列出成功！")
        print("\n" + "-"*60)
        lines = result.output.split('\n')
        for line in lines[:20]:  # 只显示前20行
            if line.strip():
                print(line)
        if len(lines) > 20:
            print(f"\n... (还有 {len(lines)-20} 项)")
        print("-"*60)
    else:
        print(f"\n✗ 列出失败: {result.error}")


def search_files_demo(mcp_tools):
    """搜索文件演示"""
    print("\n【搜索文件】")
    path = input("请输入搜索目录（默认: src）: ").strip()
    if not path:
        path = "src"

    pattern = input("请输入搜索模式（默认: *.py）: ").strip()
    if not pattern:
        pattern = "*.py"

    tool = mcp_tools.get('mcp__filesystem__search_files')
    if not tool:
        print("✗ 工具不可用")
        return

    print(f"\n正在搜索: {path}/{pattern}")
    result = tool.execute(path=path, pattern=pattern, recursive=True)

    if result.success:
        print(f"\n✓ 搜索成功！")
        print("\n" + "-"*60)
        lines = result.output.split('\n')
        for i, line in enumerate(lines[:15], 1):  # 只显示前15个
            if line.strip():
                print(f"{i}. {line}")
        if len(lines) > 15:
            print(f"\n... (还有 {len(lines)-15} 个文件)")
        print("-"*60)
    else:
        print(f"\n✗ 搜索失败: {result.error}")


def get_file_info_demo(mcp_tools):
    """获取文件信息演示"""
    print("\n【获取文件信息】")
    path = input("请输入文件路径（默认: README.md）: ").strip()
    if not path:
        path = "README.md"

    tool = mcp_tools.get('mcp__filesystem__get_file_info')
    if not tool:
        print("✗ 工具不可用")
        return

    print(f"\n正在获取文件信息: {path}")
    result = tool.execute(path=path)

    if result.success:
        print(f"\n✓ 获取成功！")
        print("\n" + "-"*60)
        print(result.output)
        print("-"*60)
    else:
        print(f"\n✗ 获取失败: {result.error}")


def directory_tree_demo(mcp_tools):
    """目录树演示"""
    print("\n【查看目录树】")
    path = input("请输入目录路径（默认: src/mcp）: ").strip()
    if not path:
        path = "src/mcp"

    tool = mcp_tools.get('mcp__filesystem__directory_tree')
    if not tool:
        print("✗ 工具不可用")
        return

    print(f"\n正在生成目录树: {path}")
    result = tool.execute(path=path)

    if result.success:
        print(f"\n✓ 生成成功！")
        print("\n" + "-"*60)
        lines = result.output.split('\n')
        for line in lines[:30]:  # 只显示前30行
            print(line)
        if len(lines) > 30:
            print(f"\n... (还有 {len(lines)-30} 行)")
        print("-"*60)
    else:
        print(f"\n✗ 生成失败: {result.error}")


def list_all_tools(mcp_tools):
    """列出所有工具"""
    print("\n【所有可用工具】")
    print("\n" + "="*60)

    # 按服务器分组
    by_server = {}
    for tool_name, tool in mcp_tools.items():
        server = tool.server_name
        if server not in by_server:
            by_server[server] = []
        by_server[server].append(tool)

    for server, tools in by_server.items():
        print(f"\n{server} 服务器 ({len(tools)} 个工具):")
        for tool in tools:
            short_name = tool.tool_name
            desc = tool.get_description().replace(f'[MCP:{server}] ', '')[:50]
            dangerous = "⚠️ " if tool.is_dangerous() else "  "
            print(f"  {dangerous}{short_name}")
            print(f"      {desc}...")

    print("\n" + "="*60)


def main():
    """主函数"""
    print("\n" + "🎮"*30)
    print("MCP工具系统 - 交互式试用")
    print("🎮"*30)

    # 启动MCP系统
    print("\n正在启动MCP系统...")

    from src.mcp.mcp_server_manager import MCPServerManager
    from src.mcp.mcp_tool_wrapper import create_mcp_tools

    manager = MCPServerManager()
    manager.start_all_servers()

    mcp_tools = create_mcp_tools(manager)

    print(f"✓ MCP系统启动成功！")
    print(f"✓ 可用工具: {len(mcp_tools)} 个")

    # 交互循环
    try:
        while True:
            print_menu(mcp_tools)
            choice = input("\n请选择操作 (0-6): ").strip()

            if choice == '0':
                print("\n退出试用...")
                break
            elif choice == '1':
                read_file_demo(mcp_tools)
            elif choice == '2':
                list_directory_demo(mcp_tools)
            elif choice == '3':
                search_files_demo(mcp_tools)
            elif choice == '4':
                get_file_info_demo(mcp_tools)
            elif choice == '5':
                directory_tree_demo(mcp_tools)
            elif choice == '6':
                list_all_tools(mcp_tools)
            else:
                print("\n✗ 无效选择，请重试")

            input("\n按Enter继续...")

    except KeyboardInterrupt:
        print("\n\n用户中断，退出...")

    finally:
        # 关闭MCP系统
        print("\n正在关闭MCP系统...")
        manager.shutdown_all_servers()
        print("✓ MCP系统已关闭")
        print("\n感谢试用！")


if __name__ == '__main__':
    main()
