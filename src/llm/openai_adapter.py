"""
OpenAI API Adapter
OpenAI GPT API的适配器实现

这个适配器封装了OpenAI API的调用逻辑，
支持GPT-4、GPT-3.5等模型。
"""

import openai
from typing import Optional
from .base import LLMClient, LLMConfig, LLMResponse, LLMError, APIKeyError, RateLimitError


class OpenAIAdapter(LLMClient):
    """
    OpenAI API适配器

    封装OpenAI API的调用，实现统一的LLMClient接口。

    支持的模型：
    - gpt-4 (最强)
    - gpt-4-turbo (更快的GPT-4)
    - gpt-3.5-turbo (便宜快速)
    """

    def __init__(self, config: LLMConfig):
        """
        初始化OpenAI适配器

        Args:
            config: LLM配置对象，必须包含api_key

        Raises:
            APIKeyError: 如果没有提供API密钥
        """
        super().__init__(config)

        # 验证API密钥
        if not config.api_key:
            raise APIKeyError("OpenAI API需要提供api_key")

        # 初始化OpenAI客户端
        self.client = openai.OpenAI(
            api_key=config.api_key,
            timeout=config.timeout,
            # 如果配置了自定义base_url（比如使用代理或兼容API）
            base_url=config.api_base if config.api_base else None
        )

    def call(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        调用OpenAI API生成回复

        Args:
            prompt: 用户输入的提示词
            system_prompt: 系统提示词（定义Agent角色）
            temperature: 温度参数（0-2，越高越随机）
            max_tokens: 最大生成token数
            **kwargs: 其他参数

        Returns:
            LLMResponse: 统一格式的响应

        Raises:
            LLMError: API调用失败时抛出
        """
        try:
            # 使用配置中的默认值
            temperature = temperature if temperature is not None else self.config.temperature
            max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens

            # 构建消息列表
            # OpenAI使用messages格式，system和user分开
            messages = []

            # 如果有系统提示词，添加到消息列表开头
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            # 添加用户消息
            messages.append({
                "role": "user",
                "content": prompt
            })

            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs  # 传递其他参数（如top_p, frequency_penalty等）
            )

            # 提取响应内容
            # OpenAI返回的是choices列表，通常取第一个
            content = response.choices[0].message.content if response.choices else ""

            # 提取token使用情况
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }

            # 转换为统一的响应格式
            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=response.choices[0].finish_reason if response.choices else "unknown",
                raw_response=response.model_dump()
            )

        except openai.RateLimitError as e:
            # OpenAI的限流错误
            raise RateLimitError(f"OpenAI API限流: {str(e)}")

        except openai.APIError as e:
            # OpenAI的API错误
            raise LLMError(f"OpenAI API错误: {str(e)}")

        except Exception as e:
            # 其他未预期的错误
            raise LLMError(f"调用OpenAI API时发生错误: {str(e)}")

    def validate_config(self) -> bool:
        """
        验证OpenAI配置是否有效

        Returns:
            bool: 配置是否有效
        """
        if not super().validate_config():
            return False

        # OpenAI特定的验证
        if not self.config.api_key:
            return False

        # 验证模型名称
        valid_models = [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
        ]

        if self.model not in valid_models:
            print(f"警告: 模型 '{self.model}' 不在已知模型列表中")

        return True
