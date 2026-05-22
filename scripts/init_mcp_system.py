"""
MCP系统初始化脚本

在系统启动时：
1. 启动所有配置的MCP服务器
2. 发现所有MCP工具
3. 注册MCP工具到工具注册表
4. 使MCP工具对所有Agent可用
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

logger = logging.getLogger(__name__)


def init_mcp_system():
    """
    初始化MCP系统

    Returns:
        MCPServerManager: 服务器管理器实例
    """
    from src.mcp.mcp_server_manager import MCPServerManager
    from src.mcp.mcp_tool_wrapper import create_mcp_tools
    from src.registry.tool_registry import ToolRegistry

    logger.info("="*60)
    logger.info("初始化MCP工具系统")
    logger.info("="*60)

    # 1. 创建服务器管理器
    manager = MCPServerManager()

    # 2. 启动所有MCP服务器
    logger.info("\n步骤1: 启动MCP服务器...")
    manager.start_all_servers()

    # 3. 创建MCP工具
    logger.info("\n步骤2: 创建MCP工具...")
    mcp_tools = create_mcp_tools(manager)
    logger.info(f"创建了 {len(mcp_tools)} 个MCP工具")

    # 4. 注册到工具注册表
    logger.info("\n步骤3: 注册MCP工具到工具注册表...")
    registry = ToolRegistry()

    registered_count = 0
    for tool_name, tool in mcp_tools.items():
        try:
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
            registered_count += 1

        except Exception as e:
            logger.warning(f"注册工具 {tool_name} 失败: {str(e)}")

    logger.info(f"成功注册 {registered_count}/{len(mcp_tools)} 个MCP工具")

    # 5. 显示统计信息
    logger.info("\n" + "="*60)
    logger.info("MCP系统初始化完成")
    logger.info("="*60)

    status = manager.get_server_status()
    logger.info(f"\n服务器状态:")
    for server_name, server_status in status.items():
        logger.info(f"  ✓ {server_name}: {server_status['tool_count']} 个工具")

    all_tools = registry.list_all()
    mcp_tool_count = len([t for t in all_tools if t.get('type') == 'mcp'])
    logger.info(f"\n工具注册表:")
    logger.info(f"  总工具数: {len(all_tools)}")
    logger.info(f"  MCP工具数: {mcp_tool_count}")
    logger.info(f"  内置工具数: {len(all_tools) - mcp_tool_count}")

    return manager


def shutdown_mcp_system(manager):
    """
    关闭MCP系统

    Args:
        manager: MCPServerManager实例
    """
    logger.info("\n" + "="*60)
    logger.info("关闭MCP系统")
    logger.info("="*60)

    if manager:
        manager.shutdown_all_servers()
        logger.info("✓ MCP系统已关闭")


def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    manager = None

    try:
        # 初始化MCP系统
        manager = init_mcp_system()

        print("\n" + "="*60)
        print("✓ MCP系统初始化成功")
        print("="*60)
        print("\n提示：在实际应用中，manager应该保持运行状态")
        print("      只在系统关闭时调用shutdown_mcp_system()")

    except Exception as e:
        logger.error(f"MCP系统初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # 清理（仅用于测试）
        if manager:
            input("\n按Enter键关闭MCP系统...")
            shutdown_mcp_system(manager)


if __name__ == '__main__':
    main()
