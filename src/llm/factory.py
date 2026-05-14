"""
LLM Factory
LLM客户端工厂类

根据配置自动创建对应的LLM适配器实例。
使用工厂模式，让创建逻辑集中管理。
"""

from typing import Dict, Any
from .base import LLMClient, LLMConfig, LLMProvider, LLMError
from .claude_adapter import ClaudeAdapter
from .openai_adapter import OpenAIAdapter


class LLMFactory:
    """
    LLM客户端工厂

    设计模式：工厂模式（Factory Pattern）
    目的：根据配置自动创建对应的LLM客户端，隐藏创建细节

    使用示例：
        config = LLMConfig(provider="claude", model="claude-3-sonnet", api_key="...")
        client = LLMFactory.create(config)
        response = client.call("你好")
    """

    # 注册表：provider名称 → 适配器类
    # 这是一个类变量，存储所有支持的适配器
    _adapters: Dict[str, type] = {
        LLMProvider.CLAUDE.value: ClaudeAdapter,
        LLMProvider.OPENAI.value: OpenAIAdapter,
        # 未来可以添加更多：
        # LLMProvider.OLLAMA.value: OllamaAdapter,
        # LLMProvider.CUSTOM.value: CustomAdapter,
    }

    @classmethod
    def create(cls, config: LLMConfig) -> LLMClient:
        """
        根据配置创建LLM客户端

        这是工厂方法，根据provider自动选择对应的适配器类。

        Args:
            config: LLM配置对象

        Returns:
            LLMClient: 对应的LLM客户端实例

        Raises:
            LLMError: 如果provider不支持

        示例：
            # 创建Claude客户端
            config = LLMConfig(provider="claude", model="claude-3-sonnet", api_key="sk-...")
            client = LLMFactory.create(config)

            # 创建OpenAI客户端
            config = LLMConfig(provider="openai", model="gpt-4", api_key="sk-...")
            client = LLMFactory.create(config)
        """
        # 获取provider对应的适配器类
        adapter_class = cls._adapters.get(config.provider)

        # 如果provider不支持，抛出错误
        if adapter_class is None:
            supported = ", ".join(cls._adapters.keys())
            raise LLMError(
                f"不支持的LLM提供商: {config.provider}. "
                f"支持的提供商: {supported}"
            )

        # 创建并返回适配器实例
        # 这里使用了多态：返回的是LLMClient类型，但实际是具体的适配器
        return adapter_class(config)

    @classmethod
    def create_from_dict(cls, config_dict: Dict[str, Any]) -> LLMClient:
        """
        从字典创建LLM客户端

        方便从配置文件（YAML/JSON）加载配置后直接创建客户端。

        Args:
            config_dict: 配置字典

        Returns:
            LLMClient: LLM客户端实例

        示例：
            config_dict = {
                "provider": "claude",
                "model": "claude-3-sonnet",
                "api_key": "sk-...",
                "temperature": 0.7
            }
            client = LLMFactory.create_from_dict(config_dict)
        """
        # 将字典转换为LLMConfig对象
        config = LLMConfig(**config_dict)

        # 调用create方法创建客户端
        return cls.create(config)

    @classmethod
    def register_adapter(cls, provider: str, adapter_class: type):
        """
        注册新的适配器

        允许用户自定义适配器并注册到工厂中。
        这是开放-封闭原则的体现：对扩展开放，对修改封闭。

        Args:
            provider: 提供商名称
            adapter_class: 适配器类（必须继承自LLMClient）

        示例：
            # 假设你实现了一个自定义的Ollama适配器
            class OllamaAdapter(LLMClient):
                ...

            # 注册到工厂
            LLMFactory.register_adapter("ollama", OllamaAdapter)

            # 现在可以使用了
            config = LLMConfig(provider="ollama", model="llama2")
            client = LLMFactory.create(config)
        """
        # 验证adapter_class是否继承自LLMClient
        if not issubclass(adapter_class, LLMClient):
            raise TypeError(f"{adapter_class} 必须继承自 LLMClient")

        # 注册到注册表
        cls._adapters[provider] = adapter_class
        print(f"已注册LLM适配器: {provider} -> {adapter_class.__name__}")

    @classmethod
    def list_providers(cls) -> list:
        """
        列出所有支持的提供商

        Returns:
            list: 提供商名称列表
        """
        return list(cls._adapters.keys())
