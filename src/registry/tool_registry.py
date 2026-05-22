"""
工具注册表

管理所有已注册的工具
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from .base_registry import BaseRegistry
from ..tools.base import Tool


class ToolRegistry(BaseRegistry):
    """
    工具注册表

    功能：
    1. 注册/注销工具
    2. 查询工具元数据
    3. 加载工具实例
    4. 根据Agent配置筛选工具
    5. 管理工具分组
    """

    def __init__(self, registry_path: Optional[str] = None):
        super().__init__(registry_path)
        self._tool_cache: Dict[str, Tool] = {}  # 工具实例缓存

    def get_registry_type(self) -> str:
        """返回注册表类型"""
        return "tools"

    def register_tool(
        self,
        name: str,
        display_name: str,
        description: str,
        tool_type: str,  # builtin/custom/mcp
        class_path: str,
        permission_level: str,
        tags: List[str] = None,
        author: str = None,
        dangerous: bool = False
    ) -> bool:
        """
        注册工具

        Args:
            name: 工具名称（唯一标识）
            display_name: 显示名称
            description: 工具描述
            tool_type: 工具类型（builtin/custom/mcp）
            class_path: 工具类路径（如"src.tools.file_tools.ReadTool"）
            permission_level: 权限级别（read/write/execute/agent_call）
            tags: 标签列表
            author: 作者
            dangerous: 是否为危险工具

        Returns:
            bool: 是否成功
        """
        metadata = {
            'name': name,
            'display_name': display_name,
            'description': description,
            'type': tool_type,
            'class_path': class_path,
            'permission_level': permission_level,
            'dangerous': dangerous,
            'enabled': True,
            'tags': tags or [],
            'author': author
        }

        return self.register(name, metadata)

    def unregister_tool(self, name: str) -> bool:
        """
        注销工具

        Args:
            name: 工具名称

        Returns:
            bool: 是否成功
        """
        # 清除缓存
        if name in self._tool_cache:
            del self._tool_cache[name]

        return self.unregister(name)

    def get_tool_metadata(self, name: str) -> Optional[Dict]:
        """
        获取工具元数据

        Args:
            name: 工具名称

        Returns:
            Optional[Dict]: 工具元数据
        """
        return self.get(name)

    def list_tools(
        self,
        filter_by_type: str = None,
        filter_by_tags: List[str] = None,
        filter_by_permission: str = None,
        enabled_only: bool = True
    ) -> List[Dict]:
        """
        列出工具

        Args:
            filter_by_type: 按类型过滤
            filter_by_tags: 按标签过滤
            filter_by_permission: 按权限级别过滤
            enabled_only: 是否只返回启用的工具

        Returns:
            List[Dict]: 工具列表
        """
        filter_by = {}

        if filter_by_type:
            filter_by['type'] = filter_by_type

        if filter_by_permission:
            filter_by['permission_level'] = filter_by_permission

        if filter_by_tags:
            filter_by['tags'] = filter_by_tags

        return self.list_all(filter_by=filter_by, enabled_only=enabled_only)

    def load_tool_instance(self, name: str) -> Tool:
        """
        加载工具实例

        Args:
            name: 工具名称

        Returns:
            Tool: 工具实例

        Raises:
            ValueError: 如果工具不存在
            ImportError: 如果无法导入工具类
        """
        # 检查缓存
        if name in self._tool_cache:
            return self._tool_cache[name]

        # 获取元数据
        metadata = self.get_tool_metadata(name)
        if not metadata:
            raise ValueError(f"工具不存在: {name}")

        # 动态导入
        class_path = metadata['class_path']
        module_path, class_name = class_path.rsplit('.', 1)

        import importlib
        module = importlib.import_module(module_path)
        tool_class = getattr(module, class_name)

        # 实例化
        tool_instance = tool_class()

        # 缓存
        self._tool_cache[name] = tool_instance

        return tool_instance

    def get_tools_for_agent(self, agent_config: Dict) -> List[Tool]:
        """
        根据Agent配置获取工具列表

        权限优先级：
        1. Agent配置的whitelist/blacklist
        2. 角色权限
        3. 全局工具

        Args:
            agent_config: Agent配置

        Returns:
            List[Tool]: 工具实例列表
        """
        tools_config = agent_config.get('tools', {})

        # 1. 获取基础工具列表
        if tools_config.get('inherit_global', True):
            # 继承全局工具
            available_tools = self.list_tools(enabled_only=True)
        else:
            available_tools = []

        # 2. 应用角色权限
        if tools_config.get('inherit_role_permissions', True):
            role = agent_config.get('role', '')
            role_permissions = self._get_role_permissions(role)
            available_tools = self._apply_role_permissions(
                available_tools,
                role_permissions
            )

        # 3. 应用白名单
        whitelist = tools_config.get('whitelist', [])
        if whitelist:
            available_tools = [
                t for t in available_tools
                if t['name'] in whitelist
            ]

        # 4. 应用黑名单
        blacklist = tools_config.get('blacklist', [])
        if blacklist:
            available_tools = [
                t for t in available_tools
                if t['name'] not in blacklist
            ]

        # 5. 应用工具分组
        groups = tools_config.get('groups', [])
        if groups:
            group_tools = set()
            for group_name in groups:
                group_tools.update(self.get_group(group_name))

            available_tools = [
                t for t in available_tools
                if t['name'] in group_tools
            ]

        # 6. 加载工具实例
        tool_instances = []
        for tool_meta in available_tools:
            try:
                tool_instance = self.load_tool_instance(tool_meta['name'])
                tool_instances.append(tool_instance)
            except Exception as e:
                print(f"⚠️  加载工具失败: {tool_meta['name']}, {e}")

        return tool_instances

    def _get_role_permissions(self, role: str) -> Dict:
        """
        获取角色权限配置

        Args:
            role: 角色名称

        Returns:
            Dict: 角色权限配置
        """
        permissions_path = Path("config/tools/tool_permissions.yaml")

        if not permissions_path.exists():
            return {}

        with open(permissions_path, 'r', encoding='utf-8') as f:
            permissions_data = yaml.safe_load(f)

        # 标准化角色名称
        role_normalized = role.lower().replace(' ', '_')

        return permissions_data.get('role_permissions', {}).get(role_normalized, {})

    def _apply_role_permissions(
        self,
        tools: List[Dict],
        role_permissions: Dict
    ) -> List[Dict]:
        """
        应用角色权限

        Args:
            tools: 工具列表
            role_permissions: 角色权限配置

        Returns:
            List[Dict]: 过滤后的工具列表
        """
        if not role_permissions:
            return tools

        # 获取允许的工具分组
        allowed_groups = role_permissions.get('allowed_groups', [])
        allowed_tools_set = set()

        for group_name in allowed_groups:
            allowed_tools_set.update(self.get_group(group_name))

        # 添加显式允许的工具
        allowed_tools_set.update(role_permissions.get('allowed_tools', []))

        # 移除显式禁止的工具
        denied_tools = set(role_permissions.get('denied_tools', []))
        allowed_tools_set -= denied_tools

        # 过滤
        return [t for t in tools if t['name'] in allowed_tools_set]
