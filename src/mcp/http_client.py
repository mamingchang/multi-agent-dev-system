"""
Streamable HTTP传输协议的MCP客户端

通过标准HTTP请求与远程MCP服务器通信，实现MCP协议。

工作原理：
1. 每个请求是独立的HTTP POST
2. 请求和响应都是JSON-RPC格式
3. 无状态设计，适合云服务和负载均衡
4. 支持流式响应（可选）

适用场景：
- 远程MCP服务器（云服务）
- 无状态架构
- 需要负载均衡的场景
- GitHub、Slack等远程API服务器

这是MCP协议推荐的传输方式。
"""

import requests
import json
import logging
from typing import Dict, Any, Optional
from .mcp_client import MCPClient

logger = logging.getLogger(__name__)


class HTTPClient(MCPClient):
    """
    Streamable HTTP传输协议的MCP客户端

    通过标准HTTP请求与远程服务器通信。
    """

    def __init__(self, server_name: str, config: Dict[str, Any]):
        """
        初始化HTTP客户端

        Args:
            server_name: 服务器名称
            config: 配置，必须包含：
                - url: 服务器URL
                - headers: HTTP头（可选）
                - timeout: 超时时间（可选，默认30秒）
                - auth: 认证信息（可选）
                  - type: 认证类型（bearer/basic/api_key）
                  - token: 认证令牌
        """
        super().__init__(server_name, config)
        self.url = config.get('url')
        self.headers = config.get('headers', {})
        self.timeout = config.get('timeout', 30)
        self.auth_config = config.get('auth', {})

        self.session = None

        # 设置认证
        self._setup_auth()

    def _setup_auth(self) -> None:
        """设置HTTP认证"""
        auth_type = self.auth_config.get('type')
        token = self.auth_config.get('token')

        if auth_type == 'bearer' and token:
            self.headers['Authorization'] = f'Bearer {token}'
        elif auth_type == 'api_key' and token:
            # API Key可能在header或query参数中
            key_name = self.auth_config.get('key_name', 'X-API-Key')
            self.headers[key_name] = token
        # basic auth通过requests.auth处理

    def connect(self) -> bool:
        """
        建立HTTP连接（创建会话）

        Returns:
            bool: 连接是否成功
        """
        if not self.url:
            logger.error(f"[{self.server_name}] 缺少URL配置")
            return False

        try:
            logger.info(f"[{self.server_name}] 连接到HTTP服务器: {self.url}")

            # 创建HTTP会话
            self.session = requests.Session()
            self.session.headers.update(self.headers)

            # 设置basic auth（如果配置）
            if self.auth_config.get('type') == 'basic':
                username = self.auth_config.get('username')
                password = self.auth_config.get('password')
                if username and password:
                    self.session.auth = (username, password)

            # 测试连接（发送一个简单的请求）
            # 注意：HTTP是无状态的，这里只是验证URL可达
            try:
                response = self.session.get(
                    self.url,
                    timeout=5
                )
                # 只要不是404/500等错误就认为连接成功
                if response.status_code < 500:
                    self.connected = True
                    logger.info(f"[{self.server_name}] HTTP连接成功")
                    return True
                else:
                    logger.error(f"[{self.server_name}] 服务器错误: {response.status_code}")
                    return False
            except requests.exceptions.RequestException:
                # 某些服务器可能不支持GET根路径，但这不影响MCP通信
                # 我们仍然认为连接成功，在initialize时再验证
                self.connected = True
                logger.info(f"[{self.server_name}] HTTP会话已创建")
                return True

        except Exception as e:
            logger.error(f"[{self.server_name}] HTTP连接失败: {str(e)}")
            return False

    def send_request(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        发送JSON-RPC请求并等待响应

        通过HTTP POST发送请求，同步等待响应。

        Args:
            method: RPC方法名
            params: 方法参数

        Returns:
            Dict: 响应结果
        """
        if not self.connected or not self.session:
            return {'error': '未连接到服务器'}

        # 生成请求ID
        request_id = self._next_request_id()

        try:
            # 构建请求
            request = {
                'jsonrpc': '2.0',
                'id': request_id,
                'method': method
            }
            if params:
                request['params'] = params

            # 发送HTTP POST请求
            # MCP Streamable HTTP使用 /mcp/v1 端点
            endpoint = f"{self.url.rstrip('/')}/mcp/v1"

            logger.debug(f"[{self.server_name}] 发送请求: {method} -> {endpoint}")

            response = self.session.post(
                endpoint,
                json=request,
                timeout=self.timeout
            )

            # 检查HTTP状态码
            if response.status_code != 200:
                logger.error(f"[{self.server_name}] HTTP错误: {response.status_code}")
                return {'error': f'HTTP {response.status_code}: {response.text}'}

            # 解析响应
            try:
                result = response.json()
                return result
            except json.JSONDecodeError:
                logger.error(f"[{self.server_name}] 响应不是有效的JSON")
                return {'error': '响应格式错误'}

        except requests.exceptions.Timeout:
            logger.error(f"[{self.server_name}] 请求超时: {method}")
            return {'error': '请求超时'}
        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.server_name}] 请求失败: {str(e)}")
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"[{self.server_name}] 发送请求异常: {str(e)}")
            return {'error': str(e)}

    def _send_message(self, message: Dict) -> None:
        """
        发送消息（内部方法）

        通过HTTP POST发送通知。

        Args:
            message: JSON-RPC消息
        """
        if not self.connected or not self.session:
            logger.error(f"[{self.server_name}] 未连接，无法发送消息")
            return

        try:
            endpoint = f"{self.url.rstrip('/')}/mcp/v1"
            response = self.session.post(
                endpoint,
                json=message,
                timeout=self.timeout
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"[{self.server_name}] 发送消息失败: {str(e)}")

    def close(self) -> None:
        """关闭HTTP连接"""
        if not self.connected:
            return

        try:
            # 发送shutdown请求
            if self.initialized:
                self.send_request('shutdown')

            # 关闭HTTP会话
            if self.session:
                self.session.close()

            self.connected = False
            self.initialized = False
            logger.info(f"[{self.server_name}] HTTP连接已关闭")

        except Exception as e:
            logger.error(f"[{self.server_name}] 关闭连接失败: {str(e)}")
