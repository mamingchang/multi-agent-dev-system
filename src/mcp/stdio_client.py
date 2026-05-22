"""
Stdio传输协议的MCP客户端

通过stdin/stdout与本地子进程通信，实现MCP协议。

工作原理：
1. 启动MCP服务器作为子进程
2. 通过stdin发送JSON-RPC消息（每行一个消息）
3. 通过stdout接收JSON-RPC响应（每行一个消息）
4. 消息格式：{"jsonrpc": "2.0", "id": 1, "method": "...", "params": {...}}

适用场景：
- 本地文件系统操作（filesystem服务器）
- 本地Git操作（git服务器）
- 本地数据库（sqlite服务器）
"""

import subprocess
import json
import threading
import queue
import logging
from typing import Dict, Any, Optional, List
from .mcp_client import MCPClient

logger = logging.getLogger(__name__)


class StdioClient(MCPClient):
    """
    Stdio传输协议的MCP客户端

    启动MCP服务器作为子进程，通过stdin/stdout通信。
    """

    def __init__(self, server_name: str, config: Dict[str, Any]):
        """
        初始化Stdio客户端

        Args:
            server_name: 服务器名称
            config: 配置，必须包含：
                - command: 启动命令（字符串或列表）
                - args: 命令参数（可选）
                - env: 环境变量（可选）
        """
        super().__init__(server_name, config)
        self.process: Optional[subprocess.Popen] = None
        self.response_queue = queue.Queue()
        self.reader_thread: Optional[threading.Thread] = None
        self._pending_requests: Dict[int, queue.Queue] = {}

    def connect(self) -> bool:
        """
        启动MCP服务器子进程并建立连接

        Returns:
            bool: 连接是否成功
        """
        try:
            # 构建命令
            command = self.config.get('command')
            args = self.config.get('args', [])
            env = self.config.get('env', None)

            if isinstance(command, str):
                cmd = [command] + args
            else:
                cmd = command + args

            logger.info(f"[{self.server_name}] 启动MCP服务器: {' '.join(cmd)}")

            # 启动子进程
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1  # 行缓冲
            )

            # 启动读取线程
            self.reader_thread = threading.Thread(
                target=self._read_loop,
                daemon=True
            )
            self.reader_thread.start()

            self.connected = True
            logger.info(f"[{self.server_name}] 连接成功")
            return True

        except Exception as e:
            logger.error(f"[{self.server_name}] 连接失败: {str(e)}")
            return False

    def _read_loop(self) -> None:
        """
        读取线程：持续从stdout读取响应

        每行是一个JSON-RPC消息，解析后放入对应的响应队列。
        """
        if not self.process or not self.process.stdout:
            return

        try:
            for line in self.process.stdout:
                line = line.strip()
                if not line:
                    continue

                try:
                    message = json.loads(line)
                    self._handle_message(message)
                except json.JSONDecodeError as e:
                    logger.error(f"[{self.server_name}] JSON解析失败: {line[:100]}")
                except Exception as e:
                    logger.error(f"[{self.server_name}] 消息处理失败: {str(e)}")

        except Exception as e:
            logger.error(f"[{self.server_name}] 读取循环异常: {str(e)}")

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
                # 将响应放入对应请求的队列
                self._pending_requests[request_id].put(message)
            else:
                logger.warning(f"[{self.server_name}] 收到未知请求ID的响应: {request_id}")
        else:
            # 没有id，说明是通知或错误
            logger.debug(f"[{self.server_name}] 收到通知: {message.get('method')}")

    def send_request(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        发送JSON-RPC请求并等待响应

        Args:
            method: RPC方法名
            params: 方法参数

        Returns:
            Dict: 响应结果
        """
        if not self.connected or not self.process or not self.process.stdin:
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

            # 发送请求（换行符分隔）
            request_line = json.dumps(request) + '\n'
            self.process.stdin.write(request_line)
            self.process.stdin.flush()

            logger.debug(f"[{self.server_name}] 发送请求: {method}")

            # 等待响应（超时30秒）
            try:
                response = response_queue.get(timeout=30)
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

        Args:
            message: JSON-RPC消息
        """
        if not self.connected or not self.process or not self.process.stdin:
            logger.error(f"[{self.server_name}] 未连接，无法发送消息")
            return

        try:
            message_line = json.dumps(message) + '\n'
            self.process.stdin.write(message_line)
            self.process.stdin.flush()
        except Exception as e:
            logger.error(f"[{self.server_name}] 发送消息失败: {str(e)}")

    def close(self) -> None:
        """关闭连接并终止子进程"""
        if not self.connected:
            return

        try:
            # 发送shutdown请求
            if self.initialized:
                self.send_request('shutdown')

            # 终止子进程
            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"[{self.server_name}] 进程未响应，强制终止")
                    self.process.kill()

            self.connected = False
            self.initialized = False
            logger.info(f"[{self.server_name}] 连接已关闭")

        except Exception as e:
            logger.error(f"[{self.server_name}] 关闭连接失败: {str(e)}")
