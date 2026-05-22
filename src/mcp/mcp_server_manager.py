"""
MCP服务器管理器

负责MCP服务器的生命周期管理：
1. 启动配置的MCP服务器
2. 维护服务器连接
3. 发现服务器提供的工具
4. 关闭服务器

设计原则：
- 系统启动时启动所有配置的MCP服务器
- 服务器启动失败时跳过，输出WARNING，不影响其他服务器
- 支持全局和Agent级别的服务器配置
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
from .mcp_client import MCPClient
from .stdio_client import StdioClient
from .sse_client import SSEClient
from .http_client import HTTPClient

logger = logging.getLogger(__name__)


class MCPServerManager:
    """
    MCP服务器管理器

    管理所有MCP服务器的生命周期，提供统一的工具发现和调用接口。
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化服务器管理器

        Args:
            config_path: 全局MCP服务器配置文件路径
        """
        self.config_path = config_path or 'config/mcp/global_servers.json'
        self.servers: Dict[str, MCPClient] = {}  # server_name -> client
        self.tools_cache: Dict[str, List[Dict]] = {}  # server_name -> tools

    def load_config(self) -> Dict[str, Any]:
        """
        加载MCP服务器配置

        Returns:
            Dict: 服务器配置
        """
        config_file = Path(self.config_path)
        if not config_file.exists():
            logger.warning(f"MCP配置文件不存在: {self.config_path}")
            return {}

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"加载MCP配置: {len(config.get('servers', {}))} 个服务器")
            return config
        except Exception as e:
            logger.error(f"加载MCP配置失败: {str(e)}")
            return {}

    def start_all_servers(self) -> None:
        """
        启动所有配置的MCP服务器

        失败的服务器会跳过并输出WARNING，不影响其他服务器。
        """
        config = self.load_config()
        servers_config = config.get('servers', {})

        if not servers_config:
            logger.info("没有配置MCP服务器")
            return

        logger.info(f"开始启动 {len(servers_config)} 个MCP服务器...")

        for server_name, server_config in servers_config.items():
            try:
                self._start_server(server_name, server_config)
            except Exception as e:
                # 启动失败：输出WARNING，跳过该服务器
                logger.warning(f"⚠️  MCP服务器 '{server_name}' 启动失败: {str(e)}")
                logger.warning(f"⚠️  跳过服务器 '{server_name}'，继续启动其他服务器")
                continue

        # 统计启动结果
        success_count = len(self.servers)
        total_count = len(servers_config)
        logger.info(f"MCP服务器启动完成: {success_count}/{total_count} 成功")

        if success_count < total_count:
            failed = total_count - success_count
            logger.warning(f"⚠️  {failed} 个服务器启动失败，已跳过")

    def _start_server(self, server_name: str, server_config: Dict[str, Any]) -> None:
        """
        启动单个MCP服务器

        Args:
            server_name: 服务器名称
            server_config: 服务器配置

        Raises:
            Exception: 启动失败时抛出异常
        """
        # 检查是否启用
        if not server_config.get('enabled', True):
            logger.info(f"服务器 '{server_name}' 已禁用，跳过")
            return

        # 获取传输类型
        transport = server_config.get('transport', 'stdio')

        # 创建客户端
        if transport == 'stdio':
            client = StdioClient(server_name, server_config)
        elif transport == 'sse':
            client = SSEClient(server_name, server_config)
        elif transport == 'http':
            client = HTTPClient(server_name, server_config)
        else:
            raise ValueError(f"不支持的传输协议: {transport}")

        # 连接服务器
        if not client.connect():
            raise Exception(f"连接失败")

        # 初始化
        if not client.initialize():
            client.close()
            raise Exception(f"初始化失败")

        # 发现工具
        tools = client.list_tools()
        if not tools:
            logger.warning(f"服务器 '{server_name}' 没有提供工具")

        # 保存客户端和工具
        self.servers[server_name] = client
        self.tools_cache[server_name] = tools

        logger.info(f"✓ 服务器 '{server_name}' 启动成功，提供 {len(tools)} 个工具")

    def get_all_tools(self) -> Dict[str, List[Dict]]:
        """
        获取所有服务器提供的工具

        Returns:
            Dict: {server_name: [tools]}
        """
        return self.tools_cache.copy()

    def get_server_tools(self, server_name: str) -> List[Dict]:
        """
        获取指定服务器的工具

        Args:
            server_name: 服务器名称

        Returns:
            List[Dict]: 工具列表
        """
        return self.tools_cache.get(server_name, [])

    def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用MCP工具

        Args:
            server_name: 服务器名称
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            Dict: 工具执行结果
        """
        if server_name not in self.servers:
            return {'error': f"服务器 '{server_name}' 不存在"}

        client = self.servers[server_name]
        return client.call_tool(tool_name, arguments)

    def shutdown_all_servers(self) -> None:
        """关闭所有MCP服务器"""
        logger.info(f"关闭 {len(self.servers)} 个MCP服务器...")

        for server_name, client in self.servers.items():
            try:
                client.close()
                logger.info(f"✓ 服务器 '{server_name}' 已关闭")
            except Exception as e:
                logger.error(f"关闭服务器 '{server_name}' 失败: {str(e)}")

        self.servers.clear()
        self.tools_cache.clear()
        logger.info("所有MCP服务器已关闭")

    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有服务器的状态

        Returns:
            Dict: {server_name: {connected, initialized, tool_count}}
        """
        status = {}
        for server_name, client in self.servers.items():
            status[server_name] = {
                'connected': client.connected,
                'initialized': client.initialized,
                'tool_count': len(self.tools_cache.get(server_name, []))
            }
        return status
