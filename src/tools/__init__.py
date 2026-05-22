"""
工具系统

为Agent提供外部工具调用能力，类似Claude Code的工具系统
"""

from .base import Tool, ToolResult, ToolRegistry
from .file_tools import ReadTool, WriteTool, EditTool
from .shell_tools import BashTool
from .search_tools import GrepTool, GlobTool

__all__ = [
    'Tool',
    'ToolResult',
    'ToolRegistry',
    'ReadTool',
    'WriteTool',
    'EditTool',
    'BashTool',
    'GrepTool',
    'GlobTool',
]
