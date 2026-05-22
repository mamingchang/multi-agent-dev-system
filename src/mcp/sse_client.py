"""
SSE (Server-Sent Events) 传输协议的MCP客户端

通过HTTP SSE与远程MCP服务器通信，实现MCP协议。

工作原理：
1. 建立SSE连接（GET请求，保持长连接）
2. 通过SSE接收服务器推送的消息
3. 通过HTTP POST发送请求
4. 消息格式：JSON-RPC over SSE

适用场景：
- 远程MCP服务器（需要持久连接）
- 向后兼容的HTTP流式传输
- 需要服务器主动推送的场景

注意：SSE协议已被标记为deprecated，推荐使用Streamable HTTP
"""

import requests
import json
import threading
import queue
import logging
import sseclient
from typing import Dict, Any, Optional
from .mcp_client import MCPClient

logger = logging.getLogger(__name__)


class SSEClient(MCPClient):
    """
    SSE传输协议的MCP客户端

    通过HTTP SSE与远程服务器通信。
    """

    def __init__(self, server_name: str, config: Dict[str, Any]):
        """
        初始化SSE客户端

        Args:
            server_name: 服务器名称
            config: 配置，必须包含：
                - url: 服务器URL
                - headers: HTTP头（可选）
                - timeout: 超时时间（可选，默认30秒）
        """
        super().__init__(server_name, config)
        self.url = config.get('url')
        self.headers = config.get('headers', {})
        self.timeout = config.get('timeout', 30)

        self.sse_client = None
        self.session = None
        self.response_queue = queue.Queue()
        self.reader_thread: Optional[threading.Thread] = None
        self._pending_requests: Dict[int, queue.Queue] = {}

    def connect(self) -> bool:
        """
        建立SSE连接

        Returns:
            bool: 连接是否成功
        """
        if not self.url:
            logger.error(f"[{self.server_name}] 缺少URL配置")
            return False

        try:
            logger.info(f"[{self.server_name}] 连接到SSE服务器: {self.url}")

            # 创建HTTP会话
            self.session = requests.Session()
            self.session.headers.update(self.headers)

            # 建立SSE连接（GET请求）
            sse_url = f"{self.url}/sse"
            response = self.session.get(
                sse_url,
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()

            # 创建SSE客户端
            self.sse_client = sseclient.SSEClient(response)

            # 启动读取线程
            self.reader_thread = threading.Thread(
                target=self._read_loop,
                daemon=True
            )
            self.reader_thread.start()

            self.connected = True
            logger.info(f"[{self.server_name}] SSE连接成功")
            return True

        except Exception as e:
            logger.error(f"[{self.server_name}] SSE连接失败: {str(e)}")
            return False

    def _read_loop(self) -> None:
        """
        读取线程：持续从SSE接收消息

        SSE消息格式：
        event: message
        data: {"jsonrpc": "2.0", ...}
        """
        if not self.sse_client:
            return

        try:
            for event in self.sse_client.events():
                if event.event == 'message':
                    try:
                        message = json.loads(event.data)
                        self._handle_message(message)
                    except json.JSONDecodeError as e:
                        logger.error(f"[{self.server_name}] JSON解析失败: {event.data[:100]}")
                    except Exception as e:
                        logger.error(f"[{self.server_name}] 消息处理失败: {str(e)}")

        except Exception as e:
            logger.error(f"[{self.server_name}] SSE读取循环异常: {str(e)}")

    def _handle_message(self, message: Dict) -> None:
        """
        处理接收到的消息

        Args:
            message: JSON-RPC消息
        """
        # 如果有id，说明是响应
        if 'id' in message:
            request_id = message['id']
            if request_id in self._pending_requests:
                self._pending_requests[request_id].put(message)
            else:
                logger.warning(f"[{self.server_name}] 收到未知请求ID的响应: {request_id}")
        else:
            # 没有id，说明是通知
            logger.debug(f"[{self.server_name}] 收到通知: {message.get('method')}")

    def send_request(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        发送JSON-RPC请求并等待响应

        通过HTTP POST发送请求，通过SSE接收响应。

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

        # 创建响应队列
        response_queue = queue.Queue()
        self._pending_requests[request_id] = response_queue

        try:
            # 构建请求
            request = {
                'jsonrpc': '2.0',
                'id': request_id,
                'method': method
            }
            if params:
                request['params'] = params

            # 通过HTTP POST发送请求
            post_url = f"{self.url}/message"
            response = self.session.post(
                post_url,
                json=request,
                timeout=self.timeout
            )
            response.raise_for_status()

            logger.debug(f"[{self.server_name}] 发送请求: {method}")

            # 等待响应（通过SSE接收）
            try:
                response = response_queue.get(timeout=self.timeout)
                return response
            except queue.Empty:
                logger.error(f"[{self.server_name}] 请求超时: {method}")
                return {'error': '请求超时'}

        except Exception as e:
            logger.error(f"[{self.server_name}] 发送请求失败: {str(e)}")
            return {'error': str(e)}

        finally:
            # 清理响应队列
            if request_id in self._pending_requests:
                del self._pending_requests[request_id]

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
            post_url = f"{self.url}/message"
            response = self.session.post(
                post_url,
                json=message,
                timeout=self.timeout
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"[{self.server_name}] 发送消息失败: {str(e)}")

    def close(self) -> None:
        """关闭SSE连接"""
        if not self.connected:
            return

        try:
            # 发送shutdown请求
            if self.initialized:
                self.send_request('shutdown')

            # 关闭SSE连接
            if self.sse_client:
                self.sse_client.close()

            # 关闭HTTP会话
            if self.session:
                self.session.close()

            self.connected = False
            self.initialized = False
            logger.info(f"[{self.server_name}] SSE连接已关闭")

        except Exception as e:
            logger.error(f"[{self.server_name}] 关闭连接失败: {str(e)}")
