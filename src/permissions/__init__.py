"""
权限系统

为Agent提供基于项目的权限控制
"""

import os
from typing import Dict, Any, List, Optional, Set
from enum import Enum
from pathlib import Path


class Permission(str, Enum):
    """权限类型"""
    READ = "read"              # 读取文件
    WRITE = "write"            # 写入文件
    EXECUTE = "execute"        # 执行命令
    DELETE = "delete"          # 删除文件
    SEARCH = "search"          # 搜索文件/代码


class PermissionLevel(str, Enum):
    """权限级别"""
    NONE = "none"              # 无权限
    READ_ONLY = "read_only"    # 只读
    READ_WRITE = "read_write"  # 读写
    FULL = "full"              # 完全控制


class ProjectPermission:
    """
    项目权限配置

    定义Agent对特定项目的操作权限
    """

    def __init__(
        self,
        project_id: str,
        project_path: str,
        level: PermissionLevel = PermissionLevel.READ_WRITE,
        allowed_permissions: Optional[Set[Permission]] = None,
        denied_paths: Optional[List[str]] = None,
        allowed_commands: Optional[List[str]] = None
    ):
        """
        初始化项目权限

        Args:
            project_id: 项目ID
            project_path: 项目根目录路径
            level: 权限级别
            allowed_permissions: 允许的权限集合（如果为None，根据level自动设置）
            denied_paths: 禁止访问的路径列表（相对于项目根目录）
            allowed_commands: 允许执行的命令列表（如果为None，允许所有非危险命令）
        """
        self.project_id = project_id
        self.project_path = os.path.abspath(project_path)
        self.level = level

        # 根据权限级别设置允许的权限
        if allowed_permissions is None:
            self.allowed_permissions = self._get_permissions_by_level(level)
        else:
            self.allowed_permissions = allowed_permissions

        # 禁止访问的路径
        self.denied_paths = denied_paths or []

        # 允许执行的命令
        self.allowed_commands = allowed_commands

    def _get_permissions_by_level(self, level: PermissionLevel) -> Set[Permission]:
        """
        根据权限级别获取允许的权限

        Args:
            level: 权限级别

        Returns:
            Set[Permission]: 权限集合
        """
        if level == PermissionLevel.NONE:
            return set()

        elif level == PermissionLevel.READ_ONLY:
            return {Permission.READ, Permission.SEARCH}

        elif level == PermissionLevel.READ_WRITE:
            return {Permission.READ, Permission.WRITE, Permission.SEARCH}

        elif level == PermissionLevel.FULL:
            return {Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.DELETE, Permission.SEARCH}

        return set()

    def has_permission(self, permission: Permission) -> bool:
        """
        检查是否有指定权限

        Args:
            permission: 权限类型

        Returns:
            bool: 是否有权限
        """
        return permission in self.allowed_permissions

    def is_path_allowed(self, file_path: str) -> bool:
        """
        检查路径是否允许访问

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否允许访问
        """
        # 转换为绝对路径
        abs_path = os.path.abspath(file_path)

        # 检查是否在项目目录内
        if not abs_path.startswith(self.project_path):
            return False

        # 检查是否在禁止列表中
        rel_path = os.path.relpath(abs_path, self.project_path)

        for denied in self.denied_paths:
            if rel_path.startswith(denied):
                return False

        return True

    def is_command_allowed(self, command: str) -> bool:
        """
        检查命令是否允许执行

        Args:
            command: 命令字符串

        Returns:
            bool: 是否允许执行
        """
        # 如果没有执行权限，直接拒绝
        if not self.has_permission(Permission.EXECUTE):
            return False

        # 检查危险命令
        dangerous_patterns = [
            'rm -rf /',
            'dd if=',
            'mkfs',
            '> /dev/',
            'format',
            'shutdown',
            'reboot',
            'init 0',
            'init 6'
        ]

        for pattern in dangerous_patterns:
            if pattern in command:
                return False

        # 如果指定了允许的命令列表，检查是否在列表中
        if self.allowed_commands is not None:
            # 提取命令的第一个词（命令名）
            cmd_name = command.strip().split()[0] if command.strip() else ""

            # 检查是否在允许列表中
            return any(cmd_name.startswith(allowed) for allowed in self.allowed_commands)

        # 默认允许（除了危险命令）
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'project_id': self.project_id,
            'project_path': self.project_path,
            'level': self.level.value,
            'allowed_permissions': [p.value for p in self.allowed_permissions],
            'denied_paths': self.denied_paths,
            'allowed_commands': self.allowed_commands
        }


class PermissionManager:
    """
    权限管理器

    管理所有项目的权限配置
    """

    def __init__(self):
        """初始化权限管理器"""
        self.permissions: Dict[str, ProjectPermission] = {}

    def register_project(
        self,
        project_id: str,
        project_path: str,
        level: PermissionLevel = PermissionLevel.READ_WRITE,
        **kwargs
    ) -> ProjectPermission:
        """
        注册项目权限

        Args:
            project_id: 项目ID
            project_path: 项目路径
            level: 权限级别
            **kwargs: 其他权限配置参数

        Returns:
            ProjectPermission: 项目权限对象
        """
        # 确保项目目录存在
        if not os.path.exists(project_path):
            os.makedirs(project_path, exist_ok=True)

        # 创建权限配置
        permission = ProjectPermission(
            project_id=project_id,
            project_path=project_path,
            level=level,
            **kwargs
        )

        self.permissions[project_id] = permission

        print(f"✓ 注册项目权限: {project_id} ({level.value})")
        print(f"  路径: {project_path}")
        print(f"  权限: {[p.value for p in permission.allowed_permissions]}")

        return permission

    def get_permission(self, project_id: str) -> Optional[ProjectPermission]:
        """
        获取项目权限

        Args:
            project_id: 项目ID

        Returns:
            ProjectPermission: 项目权限对象，如果不存在返回None
        """
        return self.permissions.get(project_id)

    def check_file_permission(
        self,
        project_id: str,
        file_path: str,
        permission: Permission
    ) -> tuple[bool, Optional[str]]:
        """
        检查文件操作权限

        Args:
            project_id: 项目ID
            file_path: 文件路径
            permission: 需要的权限

        Returns:
            tuple[bool, Optional[str]]: (是否允许, 拒绝原因)
        """
        # 获取项目权限
        proj_perm = self.get_permission(project_id)

        if not proj_perm:
            return False, f"项目不存在: {project_id}"

        # 检查权限类型
        if not proj_perm.has_permission(permission):
            return False, f"没有{permission.value}权限"

        # 检查路径
        if not proj_perm.is_path_allowed(file_path):
            return False, f"路径不允许访问: {file_path}"

        return True, None

    def check_command_permission(
        self,
        project_id: str,
        command: str
    ) -> tuple[bool, Optional[str]]:
        """
        检查命令执行权限

        Args:
            project_id: 项目ID
            command: 命令字符串

        Returns:
            tuple[bool, Optional[str]]: (是否允许, 拒绝原因)
        """
        # 获取项目权限
        proj_perm = self.get_permission(project_id)

        if not proj_perm:
            return False, f"项目不存在: {project_id}"

        # 检查命令
        if not proj_perm.is_command_allowed(command):
            return False, f"命令不允许执行: {command}"

        return True, None

    def list_projects(self) -> List[str]:
        """
        列出所有项目

        Returns:
            List[str]: 项目ID列表
        """
        return list(self.permissions.keys())

    def get_project_info(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        获取项目信息

        Args:
            project_id: 项目ID

        Returns:
            Dict: 项目信息，如果不存在返回None
        """
        perm = self.get_permission(project_id)
        return perm.to_dict() if perm else None


# 全局权限管理器
_global_permission_manager = PermissionManager()


def get_permission_manager() -> PermissionManager:
    """
    获取全局权限管理器

    Returns:
        PermissionManager: 全局权限管理器实例
    """
    return _global_permission_manager
