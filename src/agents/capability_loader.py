"""
CapabilityLoader - Agent能力加载器

负责加载Agent的工具、技能、插件、MCP服务器，并根据配置进行过滤。

核心功能：
1. 加载全局和角色专属的能力
2. 应用白名单/黑名单过滤
3. 返回数据路径（隔离）
"""
from typing import Dict, Any, List, Set
from pathlib import Path
import logging
import importlib
import os

logger = logging.getLogger(__name__)


class CapabilityLoader:
    """
    能力加载器

    根据Agent配置加载和过滤工具、技能、插件、MCP服务器
    """

    def __init__(self, agent_config: Dict[str, Any], project_root: Path = None):
        """
        初始化能力加载器

        Args:
            agent_config: Agent配置字典（从YAML加载）
            project_root: 项目根目录（默认为当前目录）
        """
        self.config = agent_config
        self.role = agent_config.get('role', 'unknown')
        self.agent_name = agent_config.get('name', 'unknown')

        if project_root is None:
            project_root = Path.cwd()
        self.project_root = Path(project_root)

        logger.info(f"初始化CapabilityLoader: {self.agent_name} (role: {self.role})")

    def load_tools(self) -> Dict[str, Any]:
        """
        加载工具并过滤

        流程：
        1. 加载全局工具（如果inherit_global=true）
        2. 加载角色专属工具
        3. 应用whitelist过滤
        4. 应用blacklist过滤

        Returns:
            过滤后的工具字典 {tool_name: tool_instance}
        """
        tools_config = self.config.get('tools', {})
        tools = {}

        # 1. 加载全局工具
        if tools_config.get('inherit_global', True):
            logger.debug("加载全局工具")
            global_tools = self._load_tools_from_path('tools/global')
            tools.update(global_tools)

        # 2. 加载角色专属工具
        role_path = tools_config.get('role_specific_path')
        if role_path:
            logger.debug(f"加载角色专属工具: {role_path}")
            role_tools = self._load_tools_from_path(role_path)
            tools.update(role_tools)
        else:
            # 默认路径：tools/roles/{role}
            default_role_path = f'tools/roles/{self.role}'
            if self._path_exists(default_role_path):
                logger.debug(f"加载默认角色工具: {default_role_path}")
                role_tools = self._load_tools_from_path(default_role_path)
                tools.update(role_tools)

        # 3. 应用白名单过滤
        whitelist = tools_config.get('whitelist')
        if whitelist:
            logger.debug(f"应用工具白名单: {whitelist}")
            tools = {k: v for k, v in tools.items() if k in whitelist}

        # 4. 应用黑名单过滤
        blacklist = tools_config.get('blacklist', [])
        if blacklist:
            logger.debug(f"应用工具黑名单: {blacklist}")
            tools = {k: v for k, v in tools.items() if k not in blacklist}

        logger.info(f"加载了{len(tools)}个工具: {list(tools.keys())}")
        return tools

    def load_skills(self) -> Dict[str, Any]:
        """
        加载技能并过滤

        流程类似load_tools：
        1. 从load_from指定的路径加载
        2. 应用whitelist
        3. 应用blacklist

        Returns:
            过滤后的技能字典
        """
        skills_config = self.config.get('skills', {})
        skills = {}

        # 1. 从指定路径加载
        load_from = skills_config.get('load_from', ['global', 'project'])
        for path in load_from:
            if path == 'global':
                path = 'skills/global'
            elif path == 'project':
                path = 'skills/project'
            elif path.startswith('roles/'):
                path = f'skills/{path}'
            else:
                path = f'skills/{path}'

            if self._path_exists(path):
                logger.debug(f"加载技能: {path}")
                loaded = self._load_skills_from_path(path)
                skills.update(loaded)

        # 2. 应用白名单
        whitelist = skills_config.get('whitelist')
        if whitelist:
            logger.debug(f"应用技能白名单: {whitelist}")
            skills = {k: v for k, v in skills.items() if k in whitelist}

        # 3. 应用黑名单
        blacklist = skills_config.get('blacklist', [])
        if blacklist:
            logger.debug(f"应用技能黑名单: {blacklist}")
            skills = {k: v for k, v in skills.items() if k not in blacklist}

        logger.info(f"加载了{len(skills)}个技能: {list(skills.keys())}")
        return skills

    def load_plugins(self) -> List[Any]:
        """
        加载插件并过滤

        只加载enabled列表中的插件

        Returns:
            插件列表
        """
        plugins_config = self.config.get('plugins', {})
        enabled = plugins_config.get('enabled', [])
        disabled = plugins_config.get('disabled', [])

        plugins = []

        for plugin_name in enabled:
            if plugin_name in disabled:
                continue

            try:
                plugin = self._load_plugin(plugin_name)
                if plugin:
                    plugins.append(plugin)
            except Exception as e:
                logger.warning(f"加载插件{plugin_name}失败: {e}")

        logger.info(f"加载了{len(plugins)}个插件")
        return plugins

    def load_mcp_servers(self) -> List[Dict]:
        """
        加载MCP服务器配置

        只返回enabled=true的服务器

        Returns:
            MCP服务器配置列表
        """
        mcp_config = self.config.get('mcp_servers', [])

        enabled_servers = [
            server for server in mcp_config
            if server.get('enabled', False)
        ]

        logger.info(f"加载了{len(enabled_servers)}个MCP服务器")
        return enabled_servers

    def get_data_paths(self) -> Dict[str, Path]:
        """
        返回Agent的数据路径

        数据隔离：每个Agent有独立的数据目录

        Returns:
            {
                'root': Path('data/agents/{agent_name}'),
                'memory': Path('data/agents/{agent_name}/memory'),
                'cache': Path('data/agents/{agent_name}/cache'),
                'logs': Path('data/agents/{agent_name}/logs')
            }
        """
        data_config = self.config.get('data', {})
        root_path = data_config.get('root_path', f'data/agents/{self.agent_name}')

        root = self.project_root / root_path

        paths = {
            'root': root,
            'memory': root / 'memory',
            'cache': root / 'cache',
            'logs': root / 'logs'
        }

        # 确保目录存在
        for path in paths.values():
            path.mkdir(parents=True, exist_ok=True)

        logger.debug(f"数据路径: {paths['root']}")
        return paths

    # ========== 私有方法 ==========

    def _load_tools_from_path(self, path: str) -> Dict[str, Any]:
        """
        从指定路径加载工具

        Args:
            path: 相对路径（如 'tools/global'）

        Returns:
            工具字典
        """
        full_path = self.project_root / 'src' / path

        if not full_path.exists():
            logger.debug(f"工具路径不存在: {full_path}")
            return {}

        tools = {}

        # 扫描Python文件
        for py_file in full_path.glob('*.py'):
            if py_file.name.startswith('_'):
                continue

            try:
                # 动态导入模块
                module_path = f"src.{path.replace('/', '.')}.{py_file.stem}"
                module = importlib.import_module(module_path)

                # 查找工具类或函数
                # 假设工具以Tool结尾，如ReadFileTool
                for attr_name in dir(module):
                    if attr_name.endswith('Tool') and not attr_name.startswith('_'):
                        tool_class = getattr(module, attr_name)
                        tool_name = attr_name.replace('Tool', '').lower()
                        tools[tool_name] = tool_class()
                        logger.debug(f"加载工具: {tool_name} from {py_file.name}")

            except Exception as e:
                logger.warning(f"加载工具文件{py_file}失败: {e}")

        return tools

    def _load_skills_from_path(self, path: str) -> Dict[str, Any]:
        """
        从指定路径加载技能

        Args:
            path: 相对路径

        Returns:
            技能字典
        """
        full_path = self.project_root / 'src' / path

        if not full_path.exists():
            logger.debug(f"技能路径不存在: {full_path}")
            return {}

        skills = {}

        # 扫描.md文件（技能通常是Markdown格式）
        for md_file in full_path.glob('*.md'):
            if md_file.name.startswith('_'):
                continue

            skill_name = md_file.stem
            skills[skill_name] = {
                'name': skill_name,
                'path': str(md_file),
                'content': md_file.read_text(encoding='utf-8')
            }
            logger.debug(f"加载技能: {skill_name}")

        return skills

    def _load_plugin(self, plugin_name: str) -> Any:
        """
        加载单个插件

        Args:
            plugin_name: 插件名称

        Returns:
            插件实例
        """
        # TODO: 实现插件加载逻辑
        logger.debug(f"加载插件: {plugin_name}")
        return None

    def _path_exists(self, path: str) -> bool:
        """
        检查路径是否存在

        Args:
            path: 相对路径

        Returns:
            是否存在
        """
        full_path = self.project_root / 'src' / path
        return full_path.exists()
