"""
LLM Client Base Classes
LLM客户端的抽象基类和数据模型

这个文件定义了：
1. LLMClient - 所有LLM适配器必须实现的抽象基类
2. LLMConfig - LLM配置的数据模型
3. LLMResponse - LLM响应的统一格式
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class LLMProvider(Enum):
    """
    LLM提供商枚举

    支持的LLM提供商列表，方便统一管理和类型检查
    """
    CLAUDE = "claude"      # Anthropic Claude
    OPENAI = "openai"      # OpenAI GPT系列
    OLLAMA = "ollama"      # 本地Ollama
    CUSTOM = "custom"      # 自定义API端点


@dataclass
class LLMConfig:
    """
    LLM配置数据类

    包含调用LLM所需的所有配置信息

    Attributes:
        provider: LLM提供商（claude/openai/ollama等）
        model: 模型名称（如claude-3-sonnet, gpt-4等）
        api_key: API密钥（如果需要）
        api_base: API基础URL（用于自定义端点）
        temperature: 温度参数，控制输出的随机性（0-1）
        max_tokens: 最大生成token数
        timeout: 请求超时时间（秒）
        extra_params: 其他额外参数
    """
    provider: str
    model: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60
    extra_params: Dict[str, Any] = None

    def __post_init__(self):
        """初始化后的验证"""
        if self.extra_params is None:
            self.extra_params = {}


@dataclass
class LLMResponse:
    """
    LLM响应的统一格式

    不同的LLM API返回格式不同，这个类统一了响应格式，
    让Agent不需要关心底层API的差异。

    Attributes:
        content: LLM生成的文本内容
        model: 使用的模型名称
        usage: token使用情况（输入/输出/总计）
        finish_reason: 完成原因（stop/length/error等）
        raw_response: 原始API响应（用于调试）
    """
    content: str
    model: str
    usage: Dict[str, int]  # {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300}
    finish_reason: str
    raw_response: Optional[Dict[str, Any]] = None


class LLMClient(ABC):
    """
    LLM客户端抽象基类

    这是一个抽象基类，定义了所有LLM适配器必须实现的接口。
    使用适配器模式，让不同的LLM API都能通过统一的接口调用。

    设计模式：适配器模式（Adapter Pattern）
    目的：统一不同LLM API的调用方式

    子类必须实现：
    - call(): 同步调用LLM
    - async_call(): 异步调用LLM（可选）
    """

    def __init__(self, config: LLMConfig):
        """
        初始化LLM客户端

        Args:
            config: LLM配置对象
        """
        self.config = config
        self.provider = config.provider
        self.model = config.model

    @abstractmethod
    def call(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        调用LLM生成回复（同步方法）

        这是核心方法，所有子类必须实现。

        Args:
            prompt: 用户输入的提示词
            system_prompt: 系统提示词（定义Agent的角色和行为）
            temperature: 温度参数（覆盖配置中的默认值）
            max_tokens: 最大token数（覆盖配置中的默认值）
            **kwargs: 其他参数，传递给具体的API

        Returns:
            LLMResponse: 统一格式的响应对象

        Raises:
            LLMError: 当API调用失败时抛出
        """
        pass

    def validate_config(self) -> bool:
        """
        验证配置是否有效

        检查API密钥、模型名称等是否正确配置

        Returns:
            bool: 配置是否有效
        """
        # 基础验证：检查必需字段
        if not self.config.model:
            return False

        # 子类可以重写这个方法添加更多验证
        return True

    def __repr__(self) -> str:
        """返回客户端的字符串表示"""
        return f"{self.__class__.__name__}(provider={self.provider}, model={self.model})"


class LLMError(Exception):
    """
    LLM调用错误的基类

    所有LLM相关的错误都继承自这个类，
    方便统一处理和捕获。
    """
    pass


class APIKeyError(LLMError):
    """API密钥错误"""
    pass


class ModelNotFoundError(LLMError):
    """模型不存在错误"""
    pass


class RateLimitError(LLMError):
    """API限流错误"""
    pass


class TimeoutError(LLMError):
    """请求超时错误"""
    pass
