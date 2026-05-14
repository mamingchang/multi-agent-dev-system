"""
LLM Config Loader
从配置文件加载LLM配置

支持从YAML文件加载配置，并自动替换环境变量。
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from .base import LLMConfig


class ConfigLoader:
    """
    配置加载器

    从YAML文件加载LLM配置，支持：
    1. 环境变量替换（${VAR_NAME}）
    2. 默认配置 + Agent特定配置
    3. 配置验证
    """

    def __init__(self, config_path: str = None):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径，如果不提供则使用默认路径
        """
        if config_path is None:
            # 默认配置文件路径：项目根目录/config/llm_config.yaml
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "llm_config.yaml"

        self.config_path = Path(config_path)
        self._config_data: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, Any]:
        """
        加载配置文件

        Returns:
            Dict: 配置数据

        Raises:
            FileNotFoundError: 如果配置文件不存在
            yaml.YAMLError: 如果YAML格式错误
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        # 读取YAML文件
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # 替换环境变量
        config_data = self._replace_env_vars(config_data)

        self._config_data = config_data
        return config_data

    def _replace_env_vars(self, data: Any) -> Any:
        """
        递归替换配置中的环境变量

        支持格式：${VAR_NAME} 或 ${VAR_NAME:default_value}

        Args:
            data: 配置数据（可能是dict、list、str等）

        Returns:
            替换后的数据
        """
        if isinstance(data, dict):
            # 如果是字典，递归处理每个值
            return {k: self._replace_env_vars(v) for k, v in data.items()}

        elif isinstance(data, list):
            # 如果是列表，递归处理每个元素
            return [self._replace_env_vars(item) for item in data]

        elif isinstance(data, str):
            # 如果是字符串，检查是否包含环境变量
            if data.startswith("${") and data.endswith("}"):
                # 提取变量名
                var_expr = data[2:-1]  # 去掉 ${ 和 }

                # 支持默认值：${VAR:default}
                if ":" in var_expr:
                    var_name, default_value = var_expr.split(":", 1)
                    return os.getenv(var_name.strip(), default_value.strip())
                else:
                    var_name = var_expr.strip()
                    value = os.getenv(var_name)
                    if value is None:
                        print(f"警告: 环境变量 {var_name} 未设置")
                        return ""
                    return value

        # 其他类型（int、float、bool等）直接返回
        return data

    def get_agent_config(self, agent_name: str) -> LLMConfig:
        """
        获取指定Agent的LLM配置

        如果Agent有特定配置，使用特定配置；
        否则使用默认配置。

        Args:
            agent_name: Agent名称（如"Requester"、"Developer"等）

        Returns:
            LLMConfig: LLM配置对象

        Raises:
            ValueError: 如果配置无效
        """
        # 如果还没加载配置，先加载
        if self._config_data is None:
            self.load()

        # 获取默认配置
        default_config = self._config_data.get("default", {})

        # 获取Agent特定配置
        agent_configs = self._config_data.get("agents", {})
        agent_config = agent_configs.get(agent_name, {})

        # 合并配置：Agent特定配置覆盖默认配置
        merged_config = {**default_config, **agent_config}

        # 获取API密钥
        api_keys = self._config_data.get("api_keys", {})
        provider = merged_config.get("provider")
        if provider and "api_key" not in merged_config:
            # 如果配置中没有api_key，从api_keys中获取
            merged_config["api_key"] = api_keys.get(provider)

        # 创建LLMConfig对象
        try:
            return LLMConfig(**merged_config)
        except Exception as e:
            raise ValueError(f"创建{agent_name}的LLM配置失败: {str(e)}")

    def get_all_agent_configs(self) -> Dict[str, LLMConfig]:
        """
        获取所有Agent的配置

        Returns:
            Dict[str, LLMConfig]: Agent名称 -> LLM配置的映射
        """
        if self._config_data is None:
            self.load()

        agent_configs = {}
        agents = self._config_data.get("agents", {})

        for agent_name in agents.keys():
            agent_configs[agent_name] = self.get_agent_config(agent_name)

        return agent_configs


# 全局配置加载器实例
# 使用单例模式，避免重复加载配置文件
_global_loader: Optional[ConfigLoader] = None


def get_config_loader(config_path: str = None) -> ConfigLoader:
    """
    获取全局配置加载器实例

    使用单例模式，确保配置只加载一次。

    Args:
        config_path: 配置文件路径（可选）

    Returns:
        ConfigLoader: 配置加载器实例
    """
    global _global_loader

    if _global_loader is None:
        _global_loader = ConfigLoader(config_path)

    return _global_loader
