"""
AgentRegistration - Agent注册系统（支持用户层）

负责Agent的注册、更新、注销，支持4种注册方式：
1. from_template: 从预定义模板创建
2. interactive: 交互式创建
3. from_file: 从YAML文件导入
4. from_existing: 从已有Agent复制

改进：
- 支持用户层：Agent属于特定用户
- 支持Agent元数据（是否公开、使用统计）
- 向后兼容：如果未指定user_id，使用全局目录
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml
import logging
from datetime import datetime
import shutil

from .capability_loader import CapabilityLoader

logger = logging.getLogger(__name__)


class AgentRegistration:
    """
    Agent注册管理器

    管理Agent的生命周期：注册、更新、注销
    支持用户层隔离
    """

    def __init__(self, user_id: str = None, config_dir: Path = None):
        """
        初始化注册管理器

        Args:
            user_id: 用户ID（如果提供，Agent保存到users/{user_id}/agents/）
            config_dir: Agent配置文件存储目录（如果提供，覆盖默认路径）
        """
        self.user_id = user_id

        if config_dir is None:
            if user_id:
                # 新架构：用户级Agent目录
                config_dir = Path('users') / user_id / 'agents'
            else:
                # 旧架构：全局Agent目录（向后兼容）
                config_dir = Path.cwd() / 'config' / 'agents'

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 模板目录（全局共享）
        self.template_dir = Path.cwd() / 'config' / 'templates'
        self.template_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"初始化AgentRegistration: {self.config_dir} (user_id={user_id})")

    def register_from_template(self,
                              agent_name: str,
                              template_name: str,
                              overrides: Dict[str, Any] = None,
                              visibility: str = 'private') -> Dict[str, Any]:
        """
        从模板创建Agent

        流程：
        1. 加载模板配置
        2. 应用overrides覆盖
        3. 验证配置
        4. 保存到agents/{agent_name}/config.yaml
        5. 创建元数据文件（包含全局唯一的agent_id）

        Args:
            agent_name: Agent名称（在用户空间内唯一）
            template_name: 模板名称（如 'product_manager', 'developer'）
            overrides: 覆盖模板的配置项
            visibility: 可见性（'private'私有, 'public'公开）

        Returns:
            完整的Agent配置字典

        Raises:
            ValueError: 模板不存在或Agent名称已存在
        """
        # 1. 检查Agent是否已存在
        if self._agent_exists(agent_name):
            raise ValueError(f"Agent '{agent_name}' 已存在")

        # 2. 加载模板
        template_path = self.template_dir / f"{template_name}.yaml"
        if not template_path.exists():
            raise ValueError(f"模板 '{template_name}' 不存在")

        with open(template_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 3. 应用overrides
        config['name'] = agent_name
        if overrides:
            config = self._merge_config(config, overrides)

        # 4. 添加元数据
        config['metadata'] = {
            'created_at': datetime.now().isoformat(),
            'created_from': 'template',
            'template': template_name,
            'version': '1.0.0'
        }

        # 5. 验证配置
        self._validate_config(config)

        # 6. 创建Agent目录结构
        agent_dir = self.config_dir / agent_name
        agent_dir.mkdir(parents=True, exist_ok=True)
        # 注意：不再在Agent目录下创建memory/，记忆应该在项目下
        (agent_dir / 'cache').mkdir(exist_ok=True)
        (agent_dir / 'workspace').mkdir(exist_ok=True)

        # 7. 保存配置
        config_path = agent_dir / 'config.yaml'
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)

        # 8. 创建元数据文件（包含全局唯一的agent_id）
        # agent_id格式：{user_id}_{agent_name}（全局唯一）
        agent_id = f"{self.user_id}_{agent_name}" if self.user_id else agent_name

        metadata = {
            'agent_id': agent_id,  # 全局唯一ID
            'agent_name': agent_name,  # 用户空间内的名称
            'owner': self.user_id or 'global',
            'visibility': visibility,  # 'private' 或 'public'
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'usage_count': 0,
            'tags': []
        }
        metadata_path = agent_dir / 'metadata.yaml'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, allow_unicode=True)

        logger.info(f"Agent '{agent_name}' 注册成功 (agent_id={agent_id}): {config_path}")

        return config

    def register_interactive(self) -> Dict[str, Any]:
        """
        交互式创建Agent

        通过命令行交互收集Agent配置信息

        Returns:
            完整的Agent配置字典
        """
        print("\n=== 交互式Agent注册 ===\n")

        # 收集基本信息
        agent_name = input("Agent名称: ").strip()
        role = input("角色: ").strip()
        description = input("描述: ").strip()

        # LLM配置
        print("\nLLM配置:")
        provider = input("  Provider (claude/openai/ollama) [claude]: ").strip() or 'claude'
        model = input("  Model [claude-sonnet-4-5]: ").strip() or 'claude-sonnet-4-5'

        # 可见性
        print("\n可见性:")
        print("  1. private - 只有你可以使用")
        print("  2. public - 所有人可以使用")
        visibility_choice = input("  选择 [1]: ").strip() or '1'
        visibility_map = {'1': 'private', '2': 'public'}
        visibility = visibility_map.get(visibility_choice, 'private')

        # 构建配置
        config = {
            'name': agent_name,
            'role': role,
            'description': description,
            'llm': {
                'provider': provider,
                'model': model
            },
            'tools': {
                'inherit_global': True
            },
            'skills': {
                'inherit_global': True
            },
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'created_from': 'interactive',
                'version': '1.0.0'
            }
        }

        # 验证配置
        self._validate_config(config)

        # 创建Agent目录结构
        agent_dir = self.config_dir / agent_name
        agent_dir.mkdir(parents=True, exist_ok=True)
        (agent_dir / 'memory').mkdir(exist_ok=True)
        (agent_dir / 'cache').mkdir(exist_ok=True)
        (agent_dir / 'workspace').mkdir(exist_ok=True)

        # 保存配置
        config_path = agent_dir / 'config.yaml'
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)

        # 创建元数据
        metadata = {
            'agent_id': agent_name,
            'owner': self.user_id or 'global',
            'visibility': visibility,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'usage_count': 0,
            'shared_with': [],
            'tags': []
        }
        metadata_path = agent_dir / 'metadata.yaml'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, allow_unicode=True)

        print(f"\n✓ Agent '{agent_name}' 注册成功")

        return config

    def register_from_file(self, agent_name: str, file_path: Path) -> Dict[str, Any]:
        """
        从YAML文件导入Agent配置

        Args:
            agent_name: Agent名称
            file_path: YAML配置文件路径

        Returns:
            完整的Agent配置字典

        Raises:
            ValueError: 文件不存在或格式错误
        """
        if not file_path.exists():
            raise ValueError(f"配置文件不存在: {file_path}")

        # 加载配置
        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 设置名称
        config['name'] = agent_name

        # 添加元数据
        config['metadata'] = {
            'created_at': datetime.now().isoformat(),
            'created_from': 'file',
            'source_file': str(file_path),
            'version': '1.0.0'
        }

        # 验证配置
        self._validate_config(config)

        # 创建Agent目录结构
        agent_dir = self.config_dir / agent_name
        agent_dir.mkdir(parents=True, exist_ok=True)
        (agent_dir / 'memory').mkdir(exist_ok=True)
        (agent_dir / 'cache').mkdir(exist_ok=True)
        (agent_dir / 'workspace').mkdir(exist_ok=True)

        # 保存配置
        config_path = agent_dir / 'config.yaml'
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)

        # 创建元数据
        metadata = {
            'agent_id': agent_name,
            'owner': self.user_id or 'global',
            'visibility': 'private',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'usage_count': 0,
            'shared_with': [],
            'tags': []
        }
        metadata_path = agent_dir / 'metadata.yaml'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, allow_unicode=True)

        logger.info(f"Agent '{agent_name}' 从文件导入成功: {file_path}")

        return config

    def register_from_existing(self, new_agent_name: str, existing_agent_name: str) -> Dict[str, Any]:
        """
        从已有Agent复制创建新Agent

        Args:
            new_agent_name: 新Agent名称
            existing_agent_name: 已存在的Agent名称

        Returns:
            完整的Agent配置字典

        Raises:
            ValueError: 源Agent不存在或新Agent名称已存在
        """
        if self._agent_exists(new_agent_name):
            raise ValueError(f"Agent '{new_agent_name}' 已存在")

        # 加载现有Agent配置
        config = self.load_config(existing_agent_name)
        if not config:
            raise ValueError(f"源Agent '{existing_agent_name}' 不存在")

        # 修改名称和元数据
        config['name'] = new_agent_name
        config['metadata'] = {
            'created_at': datetime.now().isoformat(),
            'created_from': 'existing',
            'source_agent': existing_agent_name,
            'version': '1.0.0'
        }

        # 创建Agent目录结构
        agent_dir = self.config_dir / new_agent_name
        agent_dir.mkdir(parents=True, exist_ok=True)
        (agent_dir / 'memory').mkdir(exist_ok=True)
        (agent_dir / 'cache').mkdir(exist_ok=True)
        (agent_dir / 'workspace').mkdir(exist_ok=True)

        # 保存配置
        config_path = agent_dir / 'config.yaml'
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)

        # 创建元数据
        metadata = {
            'agent_id': new_agent_name,
            'owner': self.user_id or 'global',
            'visibility': 'private',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'usage_count': 0,
            'shared_with': [],
            'tags': []
        }
        metadata_path = agent_dir / 'metadata.yaml'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, allow_unicode=True)

        logger.info(f"Agent '{new_agent_name}' 从 '{existing_agent_name}' 复制成功")

        return config

    def load_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        加载Agent配置

        支持新旧两种目录结构：
        - 新: agents/{agent_name}/config.yaml
        - 旧: agents/{agent_name}.yaml

        Args:
            agent_name: Agent名称

        Returns:
            Agent配置字典，如果不存在返回None
        """
        # 尝试新结构
        new_config_path = self.config_dir / agent_name / 'config.yaml'
        if new_config_path.exists():
            with open(new_config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)

        # 尝试旧结构（向后兼容）
        old_config_path = self.config_dir / f"{agent_name}.yaml"
        if old_config_path.exists():
            with open(old_config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)

        return None

    def load_metadata(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        加载Agent元数据

        Args:
            agent_name: Agent名称

        Returns:
            元数据字典，如果不存在返回None
        """
        metadata_path = self.config_dir / agent_name / 'metadata.yaml'
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return None

    def list_agents(self) -> List[Dict[str, Any]]:
        """
        列出所有已注册的Agent

        Returns:
            Agent配置列表
        """
        agents = []

        for item in self.config_dir.iterdir():
            if item.is_dir():
                # 新结构：目录
                config = self.load_config(item.name)
                if config:
                    metadata = self.load_metadata(item.name)
                    if metadata:
                        config['_metadata'] = metadata
                    agents.append(config)
            elif item.suffix == '.yaml':
                # 旧结构：文件（向后兼容）
                agent_name = item.stem
                config = self.load_config(agent_name)
                if config:
                    agents.append(config)

        return agents

    def update_config(self, agent_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新Agent配置

        Args:
            agent_name: Agent名称
            updates: 要更新的配置项

        Returns:
            更新后的完整配置

        Raises:
            ValueError: Agent不存在
        """
        config = self.load_config(agent_name)
        if not config:
            raise ValueError(f"Agent '{agent_name}' 不存在")

        # 合并更新
        config = self._merge_config(config, updates)

        # 更新元数据中的时间戳
        if 'metadata' in config:
            config['metadata']['updated_at'] = datetime.now().isoformat()

        # 保存配置
        self._save_config(agent_name, config)

        # 更新元数据
        metadata = self.load_metadata(agent_name)
        if metadata:
            metadata['updated_at'] = datetime.now().isoformat()
            metadata_path = self.config_dir / agent_name / 'metadata.yaml'
            with open(metadata_path, 'w', encoding='utf-8') as f:
                yaml.dump(metadata, f, allow_unicode=True)

        logger.info(f"Agent '{agent_name}' 配置已更新")

        return config

    def unregister(self, agent_name: str, backup: bool = True) -> None:
        """
        注销Agent

        Args:
            agent_name: Agent名称
            backup: 是否备份（默认True）

        Raises:
            ValueError: Agent不存在
        """
        if not self._agent_exists(agent_name):
            raise ValueError(f"Agent '{agent_name}' 不存在")

        # 备份
        if backup:
            self._backup_agent(agent_name)

        # 删除Agent目录或文件
        agent_dir = self.config_dir / agent_name
        if agent_dir.is_dir():
            shutil.rmtree(agent_dir)
        else:
            # 旧结构
            old_config_path = self.config_dir / f"{agent_name}.yaml"
            if old_config_path.exists():
                old_config_path.unlink()

        logger.info(f"Agent '{agent_name}' 已注销")

    def _agent_exists(self, agent_name: str) -> bool:
        """检查Agent是否存在"""
        # 检查新结构
        if (self.config_dir / agent_name / 'config.yaml').exists():
            return True
        # 检查旧结构
        if (self.config_dir / f"{agent_name}.yaml").exists():
            return True
        return False

    def _save_config(self, agent_name: str, config: Dict[str, Any]) -> None:
        """保存Agent配置"""
        # 优先保存到新结构
        agent_dir = self.config_dir / agent_name
        if agent_dir.is_dir():
            config_path = agent_dir / 'config.yaml'
        else:
            # 如果是旧结构，保持旧格式
            config_path = self.config_dir / f"{agent_name}.yaml"

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """验证Agent配置"""
        required_fields = ['name', 'role']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"缺少必需字段: {field}")

    def _merge_config(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置（深度合并）"""
        result = base.copy()
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result

    def _backup_agent(self, agent_name: str) -> None:
        """备份Agent配置"""
        backup_dir = self.config_dir / 'backups'
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{agent_name}_{timestamp}"

        agent_dir = self.config_dir / agent_name
        if agent_dir.is_dir():
            # 新结构：复制整个目录
            backup_path = backup_dir / backup_name
            shutil.copytree(agent_dir, backup_path)
        else:
            # 旧结构：复制文件
            old_config_path = self.config_dir / f"{agent_name}.yaml"
            if old_config_path.exists():
                backup_path = backup_dir / f"{backup_name}.yaml"
                shutil.copy2(old_config_path, backup_path)

        logger.info(f"Agent '{agent_name}' 已备份到: {backup_path}")
