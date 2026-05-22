"""
MCP工具包装器

将MCP服务器提供的工具包装为我们系统的Tool对象，
使Agent可以像使用内置工具一样使用MCP工具。

命名格式：mcp__server__tool
例如：mcp__filesystem__read_file

设计原则：
- MCPTool是通用包装器，不是每个MCP工具一个类
- 动态创建Tool实例，参数从MCP工具的inputSchema转换
- 执行时调用MCPServerManager
"""

from typing import Dict, Any, Optional
from ..tools.base import Tool, ToolResult, ToolResultStatus
import logging

logger = logging.getLogger(__name__)


class MCPTool(Tool):
    """
    MCP工具包装器

    将MCP服务器的工具包装为Tool对象。
    """

    def __init__(
        self,
        server_name: str,
        tool_name: str,
        tool_schema: Dict[str, Any],
        server_manager
    ):
        """
        初始化MCP工具

        Args:
            server_name: MCP服务器名称
            tool_name: 工具名称
            tool_schema: MCP工具的schema（包含name、description、inputSchema）
            server_manager: MCPServerManager实例
        """
        self.server_name = server_name
        self.tool_name = tool_name
        self.tool_schema = tool_schema
        self.server_manager = server_manager

        # 生成工具的完整名称：mcp__server__tool
        self.full_name = f"mcp__{server_name}__{tool_name}"

        super().__init__()

    def get_name(self) -> str:
        """返回工具名称"""
        return self.full_name

    def get_description(self) -> str:
        """返回工具描述"""
        description = self.tool_schema.get('description', '')
        # 添加来源信息
        return f"[MCP:{self.server_name}] {description}"

    def get_parameters(self) -> Dict[str, Any]:
        """
        返回参数定义

        将MCP的inputSchema转换为我们的参数格式。
        """
        input_schema = self.tool_schema.get('inputSchema', {})

        # MCP使用JSON Schema格式，我们直接返回
        return input_schema

    def get_required_permission(self) -> str:
        """
        返回所需权限

        MCP工具的权限根据服务器类型判断：
        - filesystem: write
        - git: write
        - github: write
        - 其他: read
        """
        # 根据服务器名称推断权限级别
        if self.server_name in ['filesystem', 'git', 'github']:
            return 'write'
        elif self.server_name in ['postgres', 'sqlite']:
            return 'execute'
        else:
            return 'read'

    def is_dangerous(self) -> bool:
        """
        是否为危险工具

        文件系统和Git操作可能是危险的。
        """
        return self.server_name in ['filesystem', 'git', 'run_command']

    def execute(self, **kwargs) -> ToolResult:
        """
        执行MCP工具

        Args:
            **kwargs: 工具参数

        Returns:
            ToolResult: 执行结果
        """
        try:
            logger.info(f"执行MCP工具: {self.full_name}")
            logger.debug(f"参数: {kwargs}")

            # 调用MCP服务器
            result = self.server_manager.call_tool(
                self.server_name,
                self.tool_name,
                kwargs
            )

            # 检查是否有错误
            if 'error' in result:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    output=None,
                    error=str(result['error'])
                )

            # 提取内容
            # MCP工具返回格式：{"content": [...], "isError": false}
            content = result.get('content', [])
            is_error = result.get('isError', False)

            if is_error:
                # 提取错误信息
                error_text = self._extract_text_from_content(content)
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    output=None,
                    error=error_text
                )

            # 提取输出
            output_text = self._extract_text_from_content(content)

            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                output=output_text,
                metadata={
                    'server': self.server_name,
                    'tool': self.tool_name,
                    'raw_result': result
                }
            )

        except Exception as e:
            logger.error(f"MCP工具执行失败: {str(e)}")
            return ToolResult(
                status=ToolResultStatus.ERROR,
                output=None,
                error=f"MCP工具执行异常: {str(e)}"
            )

    def _extract_text_from_content(self, content: list) -> str:
        """
        从MCP内容中提取文本

        MCP返回的content是一个列表，每个元素可能是：
        - {"type": "text", "text": "..."}
        - {"type": "resource", "resource": {...}}

        Args:
            content: MCP内容列表

        Returns:
            str: 提取的文本
        """
        texts = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    texts.append(item.get('text', ''))
                elif item.get('type') == 'resource':
                    # 资源类型，提取资源信息
                    resource = item.get('resource', {})
                    texts.append(str(resource))
            elif isinstance(item, str):
                texts.append(item)

        return '\n'.join(texts)


def create_mcp_tools(server_manager) -> Dict[str, MCPTool]:
    """
    从MCPServerManager创建所有MCP工具

    Args:
        server_manager: MCPServerManager实例

    Returns:
        Dict[str, MCPTool]: {tool_full_name: MCPTool}
    """
    mcp_tools = {}

    all_tools = server_manager.get_all_tools()

    for server_name, tools in all_tools.items():
        for tool_schema in tools:
            tool_name = tool_schema.get('name')
            if not tool_name:
                logger.warning(f"服务器 '{server_name}' 的工具缺少name字段")
                continue

            # 创建MCPTool实例
            mcp_tool = MCPTool(
                server_name=server_name,
                tool_name=tool_name,
                tool_schema=tool_schema,
                server_manager=server_manager
            )

            full_name = mcp_tool.get_name()
            mcp_tools[full_name] = mcp_tool

            logger.debug(f"创建MCP工具: {full_name}")

    logger.info(f"创建了 {len(mcp_tools)} 个MCP工具")
    return mcp_tools
