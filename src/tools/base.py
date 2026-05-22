"""
工具基类

定义工具的接口和注册机制
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class ToolResultStatus(Enum):
    """工具执行结果状态"""
    SUCCESS = "success"
    ERROR = "error"
    PERMISSION_DENIED = "permission_denied"
    TIMEOUT = "timeout"


@dataclass
class ToolResult:
    """
    工具执行结果

    包含执行状态、输出内容、错误信息等
    """
    status: ToolResultStatus
    output: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'status': self.status.value,
            'output': self.output,
            'error': self.error,
            'metadata': self.metadata or {}
        }

    def is_success(self) -> bool:
        """是否成功"""
        return self.status == ToolResultStatus.SUCCESS

    @property
    def success(self) -> bool:
        """是否成功（属性形式）"""
        return self.status == ToolResultStatus.SUCCESS


class Tool(ABC):
    """
    工具基类

    所有工具都必须继承这个类并实现execute方法

    设计思想：
    - 每个工具是一个独立的功能单元
    - 工具有名称、描述、参数定义
    - 工具执行返回标准化的ToolResult
    - 支持权限检查
    """

    def __init__(self):
        """初始化工具"""
        self.name = self.get_name()
        self.description = self.get_description()
        self.parameters = self.get_parameters()
        self.required_permission = self.get_required_permission()

    def get_required_permission(self) -> str:
        """
        获取工具需要的权限级别

        Returns:
            str: 权限级别（read/write/execute/agent_call）
        """
        return "read"

    def is_dangerous(self) -> bool:
        """
        是否为危险工具

        Returns:
            bool: True表示危险工具，需要特别注意
        """
        return False

    @abstractmethod
    def get_name(self) -> str:
        """
        获取工具名称

        Returns:
            str: 工具名称（如"read_file"、"run_command"）
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """
        获取工具描述

        Returns:
            str: 工具的功能描述，用于让LLM理解工具用途
        """
        pass

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """
        获取工具参数定义

        Returns:
            Dict: 参数定义，JSON Schema格式
            {
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "参数1描述"},
                    "param2": {"type": "integer", "description": "参数2描述"}
                },
                "required": ["param1"]
            }
        """
        pass

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            ToolResult: 执行结果
        """
        pass

    def to_llm_format(self) -> Dict[str, Any]:
        """
        转换为LLM可理解的格式

        用于在system prompt中告诉LLM有哪些工具可用

        Returns:
            Dict: 工具定义
        """
        return {
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters,
            'permission': self.get_required_permission(),
            'dangerous': self.is_dangerous()
        }


class ToolRegistry:
    """
    工具注册表

    管理所有可用的工具

    设计思想：
    - 集中管理工具
    - 支持动态注册和查询
    - 为Agent提供工具列表
    - 支持权限检查
    """

    def __init__(self):
        """初始化注册表"""
        self.tools: Dict[str, Tool] = {}
        self.permission_manager = None
        self._init_permission_manager()

    def _init_permission_manager(self):
        """初始化权限管理器"""
        try:
            from ..permissions import get_permission_manager
            self.permission_manager = get_permission_manager()
        except ImportError:
            # 如果权限系统不可用，跳过
            self.permission_manager = None

    def register(self, tool: Tool) -> None:
        """
        注册工具

        Args:
            tool: 工具实例
        """
        self.tools[tool.name] = tool
        print(f"✓ 注册工具: {tool.name}")

    def get_tool(self, name: str) -> Optional[Tool]:
        """
        获取工具

        Args:
            name: 工具名称

        Returns:
            Tool: 工具实例，如果不存在返回None
        """
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """
        列出所有工具名称

        Returns:
            List[str]: 工具名称列表
        """
        return list(self.tools.keys())

    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """
        获取工具列表（LLM格式）

        用于在system prompt中告诉LLM有哪些工具可用

        Returns:
            List[Dict]: 工具定义列表
        """
        return [tool.to_llm_format() for tool in self.tools.values()]

    def execute_tool(self, name: str, project_id: Optional[str] = None, **kwargs) -> ToolResult:
        """
        执行工具（带权限检查）

        Args:
            name: 工具名称
            project_id: 项目ID（用于权限检查）
            **kwargs: 工具参数

        Returns:
            ToolResult: 执行结果
        """
        tool = self.get_tool(name)

        if not tool:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                output=None,
                error=f"工具不存在: {name}"
            )

        # 权限检查
        if self.permission_manager and project_id:
            permission_check = self._check_tool_permission(tool, project_id, **kwargs)

            if not permission_check['allowed']:
                return ToolResult(
                    status=ToolResultStatus.PERMISSION_DENIED,
                    output=None,
                    error=permission_check['reason']
                )

        # 执行工具
        try:
            return tool.execute(**kwargs)
        except Exception as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                output=None,
                error=f"工具执行失败: {str(e)}"
            )

    def _check_tool_permission(
        self,
        tool: Tool,
        project_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        检查工具执行权限

        Args:
            tool: 工具实例
            project_id: 项目ID
            **kwargs: 工具参数

        Returns:
            Dict: {'allowed': bool, 'reason': str}
        """
        from ..permissions import Permission

        # 获取工具需要的权限
        required_perm = tool.required_permission

        if not required_perm:
            # 工具不需要权限
            return {'allowed': True, 'reason': None}

        # 转换为Permission枚举
        try:
            perm_enum = Permission(required_perm)
        except ValueError:
            return {'allowed': False, 'reason': f'未知权限类型: {required_perm}'}

        # 文件操作工具：检查文件路径权限
        if 'file_path' in kwargs:
            allowed, reason = self.permission_manager.check_file_permission(
                project_id=project_id,
                file_path=kwargs['file_path'],
                permission=perm_enum
            )

            return {'allowed': allowed, 'reason': reason}

        # 命令执行工具：检查命令权限
        if 'command' in kwargs:
            allowed, reason = self.permission_manager.check_command_permission(
                project_id=project_id,
                command=kwargs['command']
            )

            return {'allowed': allowed, 'reason': reason}

        # 搜索工具：检查搜索路径权限
        if 'path' in kwargs:
            allowed, reason = self.permission_manager.check_file_permission(
                project_id=project_id,
                file_path=kwargs['path'],
                permission=perm_enum
            )

            return {'allowed': allowed, 'reason': reason}

        # 默认允许
        return {'allowed': True, 'reason': None}


# 全局工具注册表
_global_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """
    获取全局工具注册表

    Returns:
        ToolRegistry: 全局注册表实例
    """
    return _global_registry
