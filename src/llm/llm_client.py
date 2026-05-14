"""
简化的LLM客户端 - MVP版本

为了快速验证Agent工作流，我们先实现一个简化的LLM客户端。
支持多种LLM后端（Claude、OpenAI、Ollama），使用适配器模式。

为什么这样设计：
1. 适配器模式：统一接口，方便切换不同的LLM
2. 配置驱动：通过配置文件选择LLM
3. 易于扩展：添加新LLM只需实现适配器接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os


class LLMAdapter(ABC):
    """LLM适配器基类"""

    @abstractmethod
    def chat(self, system: str, user: str, **kwargs) -> str:
        """
        聊天接口

        Args:
            system: 系统提示词
            user: 用户提示词
            **kwargs: 其他参数（如temperature、max_tokens等）

        Returns:
            str: LLM响应
        """
        pass


class MockLLMAdapter(LLMAdapter):
    """
    Mock LLM适配器 - 用于测试

    返回预设的响应，不真实调用LLM。
    用于快速测试工作流逻辑。
    """

    def __init__(self, responses: Dict[str, str] = None):
        """
        初始化Mock适配器

        Args:
            responses: 预设响应字典，key为Agent名称或"Agent名称_iteration_N"，value为响应内容
        """
        self.responses = responses or {}
        self.call_count = 0
        self.agent_call_count = {}  # 记录每个Agent的调用次数

    def chat(self, system: str, user: str, **kwargs) -> str:
        """
        返回Mock响应

        支持两种key格式：
        1. "AgentName" - 默认响应
        2. "AgentName_iteration_N" - 第N次迭代的响应

        Args:
            system: 系统提示词
            user: 用户提示词

        Returns:
            str: Mock响应
        """
        self.call_count += 1

        # 从system prompt中提取Agent名称
        agent_name = self._extract_agent_name(system)

        # 更新该Agent的调用次数
        if agent_name not in self.agent_call_count:
            self.agent_call_count[agent_name] = 0
        self.agent_call_count[agent_name] += 1

        iteration = self.agent_call_count[agent_name]

        # 优先查找带迭代次数的响应
        iteration_key = f"{agent_name}_iteration_{iteration}"
        if iteration_key in self.responses:
            return self.responses[iteration_key]

        # 其次查找默认响应
        if agent_name in self.responses:
            return self.responses[agent_name]

        # 最后返回默认Mock响应（更详细）
        return f"""[{agent_name}的分析]

我已经仔细分析了任务需求，以下是我的专业意见：

1. 核心目标：{agent_name}负责的工作已经完成
2. 关键要点：符合需求规范和最佳实践
3. 建议方案：采用标准化流程和工具
4. 预期成果：高质量的交付物

我认为这个方案是可行的，建议继续推进。
"""

    def _extract_agent_name(self, system: str) -> str:
        """
        从system prompt中提取Agent名称

        Args:
            system: 系统提示词

        Returns:
            str: Agent名称
        """
        # 简单提取：查找"你是XXX"
        if "你是" in system:
            start = system.index("你是") + 2
            end = system.index("，", start) if "，" in system[start:] else len(system)
            return system[start:end]
        return "Unknown"


class ClaudeLLMAdapter(LLMAdapter):
    """
    Claude LLM适配器

    使用Anthropic API调用Claude模型。
    """

    def __init__(self, api_key: str = None, model: str = "claude-sonnet-4-5", base_url: str = None):
        """
        初始化Claude适配器

        Args:
            api_key: Anthropic API密钥
            model: 模型名称
            base_url: 自定义API端点（可选）
        """
        # 支持多种环境变量名称
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")
        self.model = model
        self.base_url = base_url or os.getenv("ANTHROPIC_BASE_URL")

        if not self.api_key:
            raise ValueError("未设置ANTHROPIC_API_KEY或ANTHROPIC_AUTH_TOKEN环境变量")

        # 延迟导入，避免没有安装anthropic包时报错
        try:
            from anthropic import Anthropic

            # 如果有自定义base_url，使用它
            if self.base_url:
                self.client = Anthropic(api_key=self.api_key, base_url=self.base_url)
                print(f"[Claude] 使用自定义端点: {self.base_url}")
            else:
                self.client = Anthropic(api_key=self.api_key)

        except ImportError:
            raise ImportError("请安装anthropic包: pip install anthropic")

    def chat(self, system: str, user: str, **kwargs) -> str:
        """
        调用Claude API

        Args:
            system: 系统提示词
            user: 用户提示词
            **kwargs: 其他参数

        Returns:
            str: Claude响应
        """
        try:
            # 如果使用自定义base_url，尝试直接HTTP请求（兼容性更好）
            if self.base_url:
                import requests
                url = f"{self.base_url}/v1/messages"
                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
                data = {
                    "model": self.model,
                    "max_tokens": kwargs.get('max_tokens', 4096),
                    "temperature": kwargs.get('temperature', 0.7),
                    "system": system,
                    "messages": [{"role": "user", "content": user}]
                }

                response = requests.post(url, headers=headers, json=data, timeout=60)

                if response.status_code == 200:
                    result = response.json()
                    return result['content'][0]['text']
                else:
                    raise RuntimeError(f"API返回错误: {response.status_code} - {response.text}")

            # 使用官方API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get('max_tokens', 4096),
                temperature=kwargs.get('temperature', 0.7),
                system=system,
                messages=[
                    {"role": "user", "content": user}
                ]
            )

            return response.content[0].text

        except Exception as e:
            # 打印详细错误信息
            import traceback
            error_detail = traceback.format_exc()
            print(f"\n[Claude API错误详情]\n{error_detail}")
            raise RuntimeError(f"Claude API调用失败: {str(e)}")


class OpenAILLMAdapter(LLMAdapter):
    """
    OpenAI LLM适配器

    使用OpenAI API调用GPT模型。
    """

    def __init__(self, api_key: str = None, model: str = "gpt-4"):
        """
        初始化OpenAI适配器

        Args:
            api_key: OpenAI API密钥
            model: 模型名称
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError("未设置OPENAI_API_KEY环境变量")

        # 延迟导入
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("请安装openai包: pip install openai")

    def chat(self, system: str, user: str, **kwargs) -> str:
        """
        调用OpenAI API

        Args:
            system: 系统提示词
            user: 用户提示词
            **kwargs: 其他参数

        Returns:
            str: GPT响应
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=kwargs.get('max_tokens', 4096),
                temperature=kwargs.get('temperature', 0.7),
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ]
            )

            return response.choices[0].message.content

        except Exception as e:
            raise RuntimeError(f"OpenAI API调用失败: {str(e)}")


class LLMClientFactory:
    """
    LLM客户端工厂

    根据配置创建对应的LLM适配器。
    """

    @staticmethod
    def create(llm_type: str = "mock", **kwargs) -> LLMAdapter:
        """
        创建LLM适配器

        Args:
            llm_type: LLM类型（mock/claude/openai）
            **kwargs: 其他参数

        Returns:
            LLMAdapter: LLM适配器实例
        """
        if llm_type == "mock":
            return MockLLMAdapter(responses=kwargs.get('responses'))

        elif llm_type in ["claude", "anthropic"]:
            return ClaudeLLMAdapter(
                api_key=kwargs.get('api_key'),
                model=kwargs.get('model', 'claude-sonnet-4-5')
            )

        elif llm_type == "openai":
            return OpenAILLMAdapter(
                api_key=kwargs.get('api_key'),
                model=kwargs.get('model', 'gpt-4')
            )

        else:
            raise ValueError(f"不支持的LLM类型: {llm_type}")


# 便捷函数
def create_llm_client(llm_type: str = "mock", **kwargs) -> LLMAdapter:
    """
    创建LLM客户端的便捷函数

    Args:
        llm_type: LLM类型
        **kwargs: 其他参数

    Returns:
        LLMAdapter: LLM适配器实例
    """
    return LLMClientFactory.create(llm_type, **kwargs)


# 标准化别名
LLMClient = LLMAdapter


__all__ = ['LLMClient', 'LLMAdapter', 'LLMClientFactory', 'create_llm_client']

