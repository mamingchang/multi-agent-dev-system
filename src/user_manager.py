"""
用户管理系统

负责：
1. 用户创建和配置
2. 用户切换
3. 用户数据路径管理
4. 用户权限控制
"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import os


class User:
    """用户对象"""

    def __init__(self, user_id: str, username: str, email: str = None, settings: Dict = None):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.settings = settings or {}
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at,
            'settings': self.settings
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """从字典创建"""
        user = cls(
            user_id=data['user_id'],
            username=data['username'],
            email=data.get('email'),
            settings=data.get('settings', {})
        )
        user.created_at = data.get('created_at', datetime.now().isoformat())
        return user


class UserManager:
    """
    用户管理器

    负责用户的创建、切换、查询等操作
    """

    def __init__(self, base_dir: str = "users"):
        """
        初始化用户管理器

        Args:
            base_dir: 用户数据根目录
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

        # 当前用户配置文件
        self.current_user_file = Path(".current_user")

    def create_user(self, username: str, email: str = None, settings: Dict = None) -> User:
        """
        创建新用户

        Args:
            username: 用户名
            email: 邮箱（可选）
            settings: 用户设置（可选）

        Returns:
            User: 用户对象

        Raises:
            ValueError: 如果用户名已存在
        """
        # 生成user_id（使用username作为ID，确保唯一性）
        user_id = f"user_{username}"

        # 检查用户是否已存在
        if self.user_exists(user_id):
            raise ValueError(f"用户已存在: {username}")

        # 创建用户对象
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            settings=settings or {}
        )

        # 创建用户目录结构
        user_dir = self.base_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        (user_dir / "agents").mkdir(exist_ok=True)
        (user_dir / "projects").mkdir(exist_ok=True)

        # 保存用户配置
        profile_path = user_dir / "profile.yaml"
        with open(profile_path, 'w', encoding='utf-8') as f:
            yaml.dump(user.to_dict(), f, allow_unicode=True)

        return user

    def get_user(self, user_id: str) -> Optional[User]:
        """
        获取用户信息

        Args:
            user_id: 用户ID

        Returns:
            Optional[User]: 用户对象，如果不存在返回None
        """
        profile_path = self.base_dir / user_id / "profile.yaml"

        if not profile_path.exists():
            return None

        with open(profile_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return User.from_dict(data)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        通过用户名获取用户

        Args:
            username: 用户名

        Returns:
            Optional[User]: 用户对象
        """
        user_id = f"user_{username}"
        return self.get_user(user_id)

    def user_exists(self, user_id: str) -> bool:
        """
        检查用户是否存在

        Args:
            user_id: 用户ID

        Returns:
            bool: 是否存在
        """
        return (self.base_dir / user_id / "profile.yaml").exists()

    def list_users(self) -> List[User]:
        """
        列出所有用户

        Returns:
            List[User]: 用户列表
        """
        users = []

        for user_dir in self.base_dir.iterdir():
            if user_dir.is_dir():
                profile_path = user_dir / "profile.yaml"
                if profile_path.exists():
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    users.append(User.from_dict(data))

        return users

    def set_current_user(self, user_id: str) -> None:
        """
        设置当前用户

        Args:
            user_id: 用户ID

        Raises:
            ValueError: 如果用户不存在
        """
        if not self.user_exists(user_id):
            raise ValueError(f"用户不存在: {user_id}")

        # 保存到配置文件
        with open(self.current_user_file, 'w', encoding='utf-8') as f:
            f.write(user_id)

    def get_current_user(self) -> Optional[User]:
        """
        获取当前用户

        Returns:
            Optional[User]: 当前用户对象，如果未设置返回None
        """
        if not self.current_user_file.exists():
            return None

        with open(self.current_user_file, 'r', encoding='utf-8') as f:
            user_id = f.read().strip()

        return self.get_user(user_id)

    def get_current_user_id(self) -> Optional[str]:
        """
        获取当前用户ID

        Returns:
            Optional[str]: 当前用户ID
        """
        user = self.get_current_user()
        return user.user_id if user else None

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> User:
        """
        更新用户信息

        Args:
            user_id: 用户ID
            updates: 更新的字段

        Returns:
            User: 更新后的用户对象

        Raises:
            ValueError: 如果用户不存在
        """
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"用户不存在: {user_id}")

        # 更新字段
        if 'email' in updates:
            user.email = updates['email']
        if 'settings' in updates:
            user.settings.update(updates['settings'])

        # 保存
        profile_path = self.base_dir / user_id / "profile.yaml"
        with open(profile_path, 'w', encoding='utf-8') as f:
            yaml.dump(user.to_dict(), f, allow_unicode=True)

        return user

    def get_user_agents_dir(self, user_id: str) -> Path:
        """获取用户的Agent目录"""
        return self.base_dir / user_id / "agents"

    def get_user_projects_dir(self, user_id: str) -> Path:
        """获取用户的项目目录"""
        return self.base_dir / user_id / "projects"

    def ensure_user_dirs(self, user_id: str) -> None:
        """确保用户目录存在"""
        user_dir = self.base_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        (user_dir / "agents").mkdir(exist_ok=True)
        (user_dir / "projects").mkdir(exist_ok=True)
