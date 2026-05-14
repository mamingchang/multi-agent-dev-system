"""
Claude API Adapter
Anthropic Claude API的适配器实现

这个适配器封装了Anthropic Claude API的调用逻辑，
将其适配到我们统一的LLMClient接口。
"""

import anthropic
from typing import Optional
from .base import LLMClient, LLMConfig, LLMResponse, LLMError, APIKeyError, RateLimitError


class ClaudeAdapter(LLMClient):
    """
    Claude API适配器

    封装Anthropic Claude API的调用，实现统一的LLMClient接口。

    支持的模型：
    - claude-3-opus-20240229 (最强，最贵)
    - claude-3-sonnet-20240229 (平衡)
    - claude-3-haiku-20240307 (最快，最便宜)
    """

    def __init__(self, config: LLMConfig):
        """
        初始化Claude适配器

        Args:
            config: LLM配置对象，必须包含api_key

        Raises:
            APIKeyError: 如果没有提供API密钥
        """
        super().__init__(config)

        # 验证API密钥
        if not config.api_key:
            raise APIKeyError("Claude API需要提供api_key")

        # 初始化Anthropic客户端
        # 支持自定义API端点（用于代理或兼容服务）
        client_kwargs = {
            'api_key': config.api_key,
            'timeout': config.timeout
        }

        # 如果配置了自定义API端点，使用它
        if config.api_base:
            client_kwargs['base_url'] = config.api_base
            print(f"[ClaudeAdapter] 使用自定义API端点: {config.api_base}")

        self.client = anthropic.Anthropic(**client_kwargs)

    def call(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        调用Claude API生成回复

        Args:
            prompt: 用户输入的提示词
            system_prompt: 系统提示词（定义Agent角色）
            temperature: 温度参数（0-1，越高越随机）
            max_tokens: 最大生成token数
            **kwargs: 其他参数

        Returns:
            LLMResponse: 统一格式的响应

        Raises:
            LLMError: API调用失败时抛出
        """
        try:
            # 使用配置中的默认值，如果参数没有提供
            temperature = temperature if temperature is not None else self.config.temperature
            max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens

            # 构建消息列表
            # Claude API使用messages格式，而不是单个prompt
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            # 调用Claude API
            # 注意：system参数是单独传递的，不在messages里
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt if system_prompt else "",
                messages=messages
            )

            # 提取响应内容
            # Claude返回的content是一个列表，通常第一个元素是文本
            content = response.content[0].text if response.content else ""

            # 提取token使用情况
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }

            # 转换为统一的响应格式
            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=response.stop_reason,
                raw_response=response.model_dump()  # 保存原始响应用于调试
            )

        except anthropic.APIError as e:
            # API错误（如限流、服务器错误等）
            if "rate_limit" in str(e).lower():
                raise RateLimitError(f"Claude API限流: {str(e)}")
            raise LLMError(f"Claude API错误: {str(e)}")

        except Exception as e:
            # 其他未预期的错误
            raise LLMError(f"调用Claude API时发生错误: {str(e)}")

    def validate_config(self) -> bool:
        """
        验证Claude配置是否有效

        检查：
        1. API密钥是否存在
        2. 模型名称是否有效

        Returns:
            bool: 配置是否有效
        """
        # 调用父类的基础验证
        if not super().validate_config():
            return False

        # Claude特定的验证
        if not self.config.api_key:
            return False

        # 验证模型名称（Claude的模型名称有特定格式）
        valid_models = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20241022",  # 新版本
        ]

        # 如果模型名称不在已知列表中，给出警告但不阻止
        # 因为Anthropic可能会发布新模型
        if self.model not in valid_models:
            print(f"警告: 模型 '{self.model}' 不在已知模型列表中，可能无法使用")

        return True
