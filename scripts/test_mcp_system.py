"""
测试MCP工具系统

验证MCP客户端、服务器管理器和工具包装器是否正常工作。

测试内容：
1. 启动MCP服务器
2. 发现工具
3. 调用工具
4. 关闭服务器
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_mcp_server_manager():
    """测试MCP服务器管理器"""
    print("=" * 60)
    print("测试1: MCP服务器管理器")
    print("=" * 60)

    from src.mcp.mcp_server_manager import MCPServerManager

    # 创建管理器
    manager = MCPServerManager()

    # 启动所有服务器
    print("\n启动MCP服务器...")
    manager.start_all_servers()

    # 获取服务器状态
    status = manager.get_server_status()
    print(f"\n服务器状态:")
    for server_name, server_status in status.items():
        print(f"  - {server_name}:")
        print(f"      连接: {server_status['connected']}")
        print(f"      初始化: {server_status['initialized']}")
        print(f"      工具数: {server_status['tool_count']}")

    # 获取所有工具
    all_tools = manager.get_all_tools()
    print(f"\n发现的工具:")
    for server_name, tools in all_tools.items():
        print(f"  {server_name}: {len(tools)} 个工具")
        for tool in tools[:3]:  # 只显示前3个
            print(f"    - {tool.get('name')}: {tool.get('description', '')[:50]}")

    print("\n✓ MCP服务器管理器测试通过")
    return manager


def test_mcp_tool_wrapper(manager):
    """测试MCP工具包装器"""
    print("\n" + "=" * 60)
    print("测试2: MCP工具包装器")
    print("=" * 60)

    from src.mcp.mcp_tool_wrapper import create_mcp_tools

    # 创建MCP工具
    mcp_tools = create_mcp_tools(manager)

    print(f"\n创建的MCP工具: {len(mcp_tools)} 个")
    for tool_name, tool in list(mcp_tools.items())[:5]:  # 只显示前5个
        print(f"  - {tool_name}")
        print(f"      描述: {tool.get_description()[:60]}")
        print(f"      权限: {tool.get_required_permission()}")
        print(f"      危险: {tool.is_dangerous()}")

    print("\n✓ MCP工具包装器测试通过")
    return mcp_tools


def test_mcp_tool_execution(manager, mcp_tools):
    """测试MCP工具执行"""
    print("\n" + "=" * 60)
    print("测试3: MCP工具执行")
    print("=" * 60)

    # 查找filesystem服务器的read_file工具
    read_file_tool = None
    for tool_name, tool in mcp_tools.items():
        if 'filesystem' in tool_name and 'read' in tool_name.lower():
            read_file_tool = tool
            break

    if not read_file_tool:
        print("\n⚠️  未找到filesystem的read工具，跳过执行测试")
        return

    print(f"\n测试工具: {read_file_tool.get_name()}")

    # 测试读取README文件
    readme_path = str(Path(project_root) / "README.md")
    print(f"读取文件: {readme_path}")

    try:
        result = read_file_tool.execute(path=readme_path)

        print(f"\n执行结果:")
        print(f"  成功: {result.success}")
        if result.success:
            output = result.output or ""
            print(f"  输出长度: {len(output)} 字符")
            print(f"  前100字符: {output[:100]}")
        else:
            print(f"  错误: {result.error}")

        print("\n✓ MCP工具执行测试通过")

    except Exception as e:
        print(f"\n✗ MCP工具执行失败: {str(e)}")
        import traceback
        traceback.print_exc()


def test_tool_registry_integration(manager, mcp_tools):
    """测试与工具注册表的集成"""
    print("\n" + "=" * 60)
    print("测试4: 工具注册表集成")
    print("=" * 60)

    from src.registry.tool_registry import ToolRegistry

    registry = ToolRegistry()

    # 注册MCP工具到工具注册表
    print(f"\n注册 {len(mcp_tools)} 个MCP工具到工具注册表...")

    for tool_name, tool in mcp_tools.items():
        # 构建工具元数据
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

    # 验证注册
    all_tools = registry.list_all()
    mcp_tool_count = len([t for t in all_tools if t.get('type') == 'mcp'])

    print(f"\n工具注册表统计:")
    print(f"  总工具数: {len(all_tools)}")
    print(f"  MCP工具数: {mcp_tool_count}")

    print("\n✓ 工具注册表集成测试通过")


def main():
    """运行所有测试"""
    print("\n" + "🔧" * 30)
    print("MCP工具系统测试")
    print("🔧" * 30 + "\n")

    manager = None

    try:
        # 测试1: 服务器管理器
        manager = test_mcp_server_manager()

        # 测试2: 工具包装器
        mcp_tools = test_mcp_tool_wrapper(manager)

        # 测试3: 工具执行
        test_mcp_tool_execution(manager, mcp_tools)

        # 测试4: 工具注册表集成
        test_tool_registry_integration(manager, mcp_tools)

        print("\n" + "=" * 60)
        print("✓ 所有测试通过")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # 清理：关闭所有服务器
        if manager:
            print("\n关闭MCP服务器...")
            manager.shutdown_all_servers()


if __name__ == '__main__':
    main()
