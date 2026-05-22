"""
MCP (Model Context Protocol) 客户端实现

这个模块实现了MCP客户端，允许我们的Agent系统连接到各种MCP服务器，
使用它们提供的工具和资源。

支持的传输协议：
- stdio: 本地子进程通信
- SSE: Server-Sent Events (HTTP流式)
- HTTP: Streamable HTTP

架构：
- MCPClient: MCP客户端基类
- StdioClient: stdio传输协议实现
- SSEClient: SSE传输协议实现
- HTTPClient: HTTP传输协议实现
- MCPServerManager: MCP服务器生命周期管理
- MCPTool: 将MCP工具包装为Tool对象
"""

from .mcp_client import MCPClient
from .stdio_client import StdioClient
from .sse_client import SSEClient
from .http_client import HTTPClient
from .mcp_server_manager import MCPServerManager
from .mcp_tool_wrapper import MCPTool

__all__ = [
    'MCPClient',
    'StdioClient',
    'SSEClient',
    'HTTPClient',
    'MCPServerManager',
    'MCPTool',
]
