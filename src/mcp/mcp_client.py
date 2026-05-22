"""
MCP客户端基类

定义MCP客户端的统一接口，所有传输协议的客户端都继承此类。

MCP协议核心概念：
1. 连接生命周期：initialize -> 工作 -> shutdown
2. JSON-RPC消息格式：request/response/notification
3. 工具发现：通过tools/list获取服务器提供的工具
4. 工具调用：通过tools/call执行工具
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import logging

logger = logging.getLogger(__name__)


class MCPClient(ABC):
    """
    MCP客户端基类

    所有MCP客户端（stdio/SSE/HTTP）都继承此类，实现统一接口。

    生命周期：
    1. __init__: 创建客户端
    2. connect(): 建立连接
    3. initialize(): 初始化握手
    4. list_tools(): 获取工具列表
    5. call_tool(): 调用工具
    6. close(): 关闭连接
    """

    def __init__(self, server_name: str, config: Dict[str, Any]):
        """
        初始化MCP客户端

        Args:
            server_name: 服务器名称（用于标识）
            config: 服务器配置
        """
        self.server_name = server_name
        self.config = config
        self.connected = False
        self.initialized = False
        self._request_id = 0

    def _next_request_id(self) -> int:
        """生成下一个请求ID"""
        self._request_id += 1
        return self._request_id

    @abstractmethod
    def connect(self) -> bool:
        """
        建立与MCP服务器的连接

        Returns:
            bool: 连接是否成功
        """
        pass

    @abstractmethod
    def send_request(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        发送JSON-RPC请求并等待响应

        Args:
            method: RPC方法名
            params: 方法参数

        Returns:
            Dict: 响应结果
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """关闭连接"""
        pass

    def initialize(self) -> bool:
        """
        初始化MCP连接（握手）

        发送initialize请求，建立协议版本和能力协商。

        Returns:
            bool: 初始化是否成功
        """
        if not self.connected:
            logger.error(f"[{self.server_name}] 未连接，无法初始化")
            return False

        try:
            # 发送initialize请求
            response = self.send_request('initialize', {
                'protocolVersion': '2024-11-05',
                'capabilities': {
                    'tools': {}  # 我们支持工具调用
                },
                'clientInfo': {
                    'name': 'multi-agent-dev-system',
                    'version': '1.0.0'
                }
            })

            if 'error' in response:
                logger.error(f"[{self.server_name}] 初始化失败: {response['error']}")
                return False

            # 发送initialized通知
            self.send_notification('notifications/initialized')

            self.initialized = True
            logger.info(f"[{self.server_name}] 初始化成功")
            return True

        except Exception as e:
            logger.error(f"[{self.server_name}] 初始化异常: {str(e)}")
            return False

    def send_notification(self, method: str, params: Optional[Dict] = None) -> None:
        """
        发送JSON-RPC通知（不需要响应）

        Args:
            method: 通知方法名
            params: 通知参数
        """
        # 通知不需要id字段
        message = {
            'jsonrpc': '2.0',
            'method': method
        }
        if params:
            message['params'] = params

        # 子类实现具体发送逻辑
        self._send_message(message)

    @abstractmethod
    def _send_message(self, message: Dict) -> None:
        """
        发送消息（内部方法）

        Args:
            message: JSON-RPC消息
        """
        pass

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        获取服务器提供的工具列表

        Returns:
            List[Dict]: 工具列表，每个工具包含name、description、inputSchema
        """
        if not self.initialized:
            logger.error(f"[{self.server_name}] 未初始化，无法列出工具")
            return []

        try:
            response = self.send_request('tools/list')

            if 'error' in response:
                logger.error(f"[{self.server_name}] 获取工具列表失败: {response['error']}")
                return []

            tools = response.get('result', {}).get('tools', [])
            logger.info(f"[{self.server_name}] 发现 {len(tools)} 个工具")
            return tools

        except Exception as e:
            logger.error(f"[{self.server_name}] 获取工具列表异常: {str(e)}")
            return []

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用MCP工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            Dict: 工具执行结果
        """
        if not self.initialized:
            logger.error(f"[{self.server_name}] 未初始化，无法调用工具")
            return {'error': '客户端未初始化'}

        try:
            response = self.send_request('tools/call', {
                'name': tool_name,
                'arguments': arguments
            })

            if 'error' in response:
                logger.error(f"[{self.server_name}] 工具调用失败: {response['error']}")
                return {'error': response['error']}

            result = response.get('result', {})
            logger.debug(f"[{self.server_name}] 工具 {tool_name} 执行成功")
            return result

        except Exception as e:
            logger.error(f"[{self.server_name}] 工具调用异常: {str(e)}")
            return {'error': str(e)}
