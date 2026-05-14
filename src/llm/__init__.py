"""
LLM Client Module
统一的LLM调用接口模块

这个模块提供了一个统一的接口来调用不同的LLM API，
使用适配器模式让Agent不需要关心底层使用的是哪个LLM提供商。

使用示例：
    # 方式1：直接创建
    from src.llm import LLMFactory, LLMConfig

    config = LLMConfig(provider="claude", model="claude-3-sonnet", api_key="...")
    client = LLMFactory.create(config)
    response = client.call("你好")
    print(response.content)

    # 方式2：从配置文件加载
    from src.llm import get_config_loader, LLMFactory

    loader = get_config_loader()
    config = loader.get_agent_config("Developer")
    client = LLMFactory.create(config)
"""

from .base import LLMClient, LLMConfig, LLMResponse, LLMError, LLMProvider
from .factory import LLMFactory
from .config_loader import ConfigLoader, get_config_loader
from .claude_adapter import ClaudeAdapter
from .openai_adapter import OpenAIAdapter

__all__ = [
    # 基础类
    'LLMClient',
    'LLMConfig',
    'LLMResponse',
    'LLMError',
    'LLMProvider',

    # 工厂
    'LLMFactory',

    # 配置加载
    'ConfigLoader',
    'get_config_loader',

    # 适配器（通常不需要直接使用，通过工厂创建）
    'ClaudeAdapter',
    'OpenAIAdapter',
]
