"""
工具加载器

根据Agent配置加载工具
"""

from typing import Dict, List
from ..registry.tool_registry import ToolRegistry as GlobalToolRegistry
from .base import Tool


class ToolLoader:
    """
    工具加载器

    功能：
    1. 根据Agent配置加载工具
    2. 创建Agent专用ToolRegistry
    3. 应用权限过滤
    """

    def __init__(self):
        self.global_registry = GlobalToolRegistry()

    def load_tools_for_agent(self, agent_config: Dict) -> 'AgentToolRegistry':
        """
        为Agent加载工具

        Args:
            agent_config: Agent配置

        Returns:
            AgentToolRegistry: Agent专用工具注册表
        """
        # 获取工具列表
        tools = self.global_registry.get_tools_for_agent(agent_config)

        # 创建Agent专用注册表
        agent_registry = AgentToolRegistry(tools, agent_config)

        return agent_registry


class AgentToolRegistry:
    """
    Agent专用工具注册表

    与全局ToolRegistry不同：
    - 只包含Agent允许使用的工具
    - 包含工具特定配置
    - 提供执行接口
    """

    def __init__(self, tools: List[Tool], agent_config: Dict):
        """
        初始化Agent工具注册表

        Args:
            tools: 工具列表
            agent_config: Agent配置
        """
        self.tools = {tool.get_name(): tool for tool in tools}
        self.agent_config = agent_config
        self.tool_configs = agent_config.get('tools', {}).get('tool_configs', {})

    def has_tool(self, name: str) -> bool:
        """
        检查工具是否可用

        Args:
            name: 工具名称

        Returns:
            bool: 是否可用
        """
        return name in self.tools

    def get_tool(self, name: str) -> Tool:
        """
        获取工具实例

        Args:
            name: 工具名称

        Returns:
            Tool: 工具实例

        Raises:
            ValueError: 如果工具不可用
        """
        if name not in self.tools:
            available = ', '.join(self.tools.keys())
            raise ValueError(f"工具不可用: {name}。可用工具: {available}")

        return self.tools[name]

    def list_tools(self) -> List[Tool]:
        """
        列出所有可用工具

        Returns:
            List[Tool]: 工具列表
        """
        return list(self.tools.values())

    def execute_tool(self, name: str, **kwargs):
        """
        执行工具

        包含：
        - 权限检查
        - 参数验证
        - 工具特定配置应用
        - 执行

        Args:
            name: 工具名称
            **kwargs: 工具参数

        Returns:
            ToolResult: 执行结果
        """
        tool = self.get_tool(name)

        # 应用工具特定配置
        if name in self.tool_configs:
            tool_config = self.tool_configs[name]
            # 合并配置（不覆盖显式传入的参数）
            for key, value in tool_config.items():
                if key not in kwargs:
                    kwargs[key] = value

        # 执行
        return tool.execute(**kwargs)

    def get_tools_for_llm(self) -> List[Dict]:
        """
        获取LLM格式的工具列表

        Returns:
            List[Dict]: 工具定义列表
        """
        return [tool.to_llm_format() for tool in self.tools.values()]
