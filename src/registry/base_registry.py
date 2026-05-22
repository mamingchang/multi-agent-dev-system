"""
注册表基类

提供通用的注册表功能，供工具、技能、插件等注册表继承
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from abc import ABC, abstractmethod


class BaseRegistry(ABC):
    """
    注册表基类

    功能：
    1. 加载和保存注册表数据
    2. 注册/注销条目
    3. 查询条目
    4. 管理分组

    子类需要实现：
    - get_registry_type(): 返回注册表类型（如"tools", "skills"）
    """

    def __init__(self, registry_path: Optional[str] = None):
        """
        初始化注册表

        Args:
            registry_path: 注册表文件路径，如果为None则使用默认路径
        """
        if registry_path is None:
            registry_type = self.get_registry_type()
            registry_path = f"data/{registry_type}/registry.json"

        self.registry_path = Path(registry_path)
        self.registry_data = self._load_registry()

    @abstractmethod
    def get_registry_type(self) -> str:
        """
        获取注册表类型

        Returns:
            str: 注册表类型（如"tools", "skills", "plugins"）
        """
        pass

    def _load_registry(self) -> Dict:
        """
        加载注册表数据

        Returns:
            Dict: 注册表数据
        """
        if self.registry_path.exists():
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        # 返回默认结构
        registry_type = self.get_registry_type()
        return {
            'version': '1.0',
            registry_type: {},
            f'{registry_type[:-1]}_groups': {}  # tools -> tool_groups
        }

    def _save_registry(self):
        """保存注册表数据"""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.registry_data, f, indent=2, ensure_ascii=False)

    def register(
        self,
        name: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        注册条目

        Args:
            name: 条目名称（唯一标识）
            metadata: 条目元数据

        Returns:
            bool: 是否成功

        Raises:
            ValueError: 如果条目已存在
        """
        registry_type = self.get_registry_type()

        if name in self.registry_data[registry_type]:
            raise ValueError(f"{registry_type[:-1].capitalize()} 已存在: {name}")

        # 添加时间戳
        metadata['created_at'] = datetime.now().isoformat()
        metadata['updated_at'] = datetime.now().isoformat()

        self.registry_data[registry_type][name] = metadata
        self._save_registry()

        return True

    def unregister(self, name: str) -> bool:
        """
        注销条目

        Args:
            name: 条目名称

        Returns:
            bool: 是否成功
        """
        registry_type = self.get_registry_type()

        if name not in self.registry_data[registry_type]:
            return False

        del self.registry_data[registry_type][name]

        # 从分组中移除
        group_key = f'{registry_type[:-1]}_groups'
        for group_name, items in self.registry_data[group_key].items():
            if name in items:
                items.remove(name)

        self._save_registry()
        return True

    def get(self, name: str) -> Optional[Dict]:
        """
        获取条目元数据

        Args:
            name: 条目名称

        Returns:
            Optional[Dict]: 条目元数据，如果不存在返回None
        """
        registry_type = self.get_registry_type()
        return self.registry_data[registry_type].get(name)

    def list_all(
        self,
        filter_by: Optional[Dict[str, Any]] = None,
        enabled_only: bool = True
    ) -> List[Dict]:
        """
        列出所有条目

        Args:
            filter_by: 过滤条件（字段名 -> 值）
            enabled_only: 是否只返回启用的条目

        Returns:
            List[Dict]: 条目列表
        """
        registry_type = self.get_registry_type()
        items = list(self.registry_data[registry_type].values())

        # 过滤启用状态
        if enabled_only:
            items = [item for item in items if item.get('enabled', True)]

        # 应用过滤条件
        if filter_by:
            for key, value in filter_by.items():
                if isinstance(value, list):
                    # 列表类型：检查是否有交集
                    items = [
                        item for item in items
                        if any(v in item.get(key, []) for v in value)
                    ]
                else:
                    # 普通类型：精确匹配
                    items = [item for item in items if item.get(key) == value]

        return items

    def update(self, name: str, metadata: Dict[str, Any]) -> bool:
        """
        更新条目元数据

        Args:
            name: 条目名称
            metadata: 新的元数据（会合并到现有元数据）

        Returns:
            bool: 是否成功
        """
        registry_type = self.get_registry_type()

        if name not in self.registry_data[registry_type]:
            return False

        # 合并元数据
        self.registry_data[registry_type][name].update(metadata)
        self.registry_data[registry_type][name]['updated_at'] = datetime.now().isoformat()

        self._save_registry()
        return True

    def create_group(self, group_name: str, items: List[str]) -> bool:
        """
        创建分组

        Args:
            group_name: 分组名称
            items: 条目名称列表

        Returns:
            bool: 是否成功
        """
        group_key = f'{self.get_registry_type()[:-1]}_groups'
        self.registry_data[group_key][group_name] = items
        self._save_registry()
        return True

    def get_group(self, group_name: str) -> List[str]:
        """
        获取分组

        Args:
            group_name: 分组名称

        Returns:
            List[str]: 条目名称列表
        """
        group_key = f'{self.get_registry_type()[:-1]}_groups'
        return self.registry_data[group_key].get(group_name, [])

    def list_groups(self) -> Dict[str, List[str]]:
        """
        列出所有分组

        Returns:
            Dict[str, List[str]]: 分组字典
        """
        group_key = f'{self.get_registry_type()[:-1]}_groups'
        return self.registry_data[group_key]

    def exists(self, name: str) -> bool:
        """
        检查条目是否存在

        Args:
            name: 条目名称

        Returns:
            bool: 是否存在
        """
        registry_type = self.get_registry_type()
        return name in self.registry_data[registry_type]
