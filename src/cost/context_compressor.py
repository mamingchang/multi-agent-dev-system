"""
上下文压缩器

实现对话上下文的智能压缩，降低Token消耗。

压缩策略：
1. 触发条件：上下文达到配置长度的70%
2. 压缩目标：压缩到30%
3. 压缩方式：LLM摘要 + 关键信息提取
4. 保留内容：关键决策、结论、错误信息保留原文
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import tiktoken


@dataclass
class Message:
    """对话消息"""
    role: str  # system, user, assistant
    content: str
    metadata: Optional[Dict[str, Any]] = None


class ContextCompressor:
    """上下文压缩器"""

    def __init__(
        self,
        model: str = "gpt-4",
        max_tokens: int = 8000,
        compression_trigger: float = 0.7,
        compression_target: float = 0.3
    ):
        """
        初始化压缩器

        Args:
            model: 模型名称（用于Token计数）
            max_tokens: 最大Token数
            compression_trigger: 触发压缩的阈值（70%）
            compression_target: 压缩目标（30%）
        """
        self.model = model
        self.max_tokens = max_tokens
        self.compression_trigger = compression_trigger
        self.compression_target = compression_target

        # 初始化Token编码器
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # 如果模型不支持，使用默认编码
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """
        计算文本的Token数量

        Args:
            text: 文本内容

        Returns:
            int: Token数量
        """
        return len(self.encoding.encode(text))

    def count_messages_tokens(self, messages: List[Message]) -> int:
        """
        计算消息列表的总Token数

        Args:
            messages: 消息列表

        Returns:
            int: 总Token数
        """
        total = 0
        for msg in messages:
            # 每条消息有固定开销（role + 分隔符）
            total += 4  # 固定开销
            total += self.count_tokens(msg.content)
        return total

    def should_compress(self, messages: List[Message]) -> bool:
        """
        判断是否需要压缩

        Args:
            messages: 消息列表

        Returns:
            bool: 是否需要压缩
        """
        current_tokens = self.count_messages_tokens(messages)
        threshold = self.max_tokens * self.compression_trigger

        return current_tokens >= threshold

    def compress(
        self,
        messages: List[Message],
        llm_summarize_func: Optional[callable] = None
    ) -> List[Message]:
        """
        压缩消息列表

        Args:
            messages: 原始消息列表
            llm_summarize_func: LLM摘要函数（可选）

        Returns:
            List[Message]: 压缩后的消息列表
        """
        if not messages:
            return messages

        # 分离系统消息和对话消息
        system_messages = [m for m in messages if m.role == "system"]
        conversation_messages = [m for m in messages if m.role != "system"]

        if not conversation_messages:
            return messages

        # 识别关键消息（需要保留原文）
        key_messages = self._identify_key_messages(conversation_messages)

        # 识别可压缩消息
        compressible_messages = [
            m for m in conversation_messages
            if m not in key_messages
        ]

        # 如果有LLM摘要函数，使用LLM压缩
        if llm_summarize_func and compressible_messages:
            summary = self._compress_with_llm(
                compressible_messages,
                llm_summarize_func
            )
        else:
            # 否则使用简单压缩
            summary = self._compress_simple(compressible_messages)

        # 构建压缩后的消息列表
        compressed = system_messages.copy()

        # 添加压缩摘要
        if summary:
            compressed.append(Message(
                role="system",
                content=f"[历史对话摘要]\n{summary}",
                metadata={"compressed": True}
            ))

        # 添加关键消息
        compressed.extend(key_messages)

        return compressed

    def _identify_key_messages(self, messages: List[Message]) -> List[Message]:
        """
        识别关键消息（需要保留原文）

        关键消息包括：
        1. 包含错误信息的消息
        2. 包含重要决策的消息
        3. 最近的N条消息

        Args:
            messages: 消息列表

        Returns:
            List[Message]: 关键消息列表
        """
        key_messages = []

        # 关键词列表
        error_keywords = ["error", "错误", "失败", "exception", "failed"]
        decision_keywords = ["决定", "选择", "采用", "使用", "decide", "choose"]

        for msg in messages:
            content_lower = msg.content.lower()

            # 检查是否包含错误信息
            if any(kw in content_lower for kw in error_keywords):
                key_messages.append(msg)
                continue

            # 检查是否包含重要决策
            if any(kw in content_lower for kw in decision_keywords):
                key_messages.append(msg)
                continue

        # 保留最近的3条消息
        recent_messages = messages[-3:]
        for msg in recent_messages:
            if msg not in key_messages:
                key_messages.append(msg)

        return key_messages

    def _compress_with_llm(
        self,
        messages: List[Message],
        llm_summarize_func: callable
    ) -> str:
        """
        使用LLM压缩消息

        Args:
            messages: 消息列表
            llm_summarize_func: LLM摘要函数

        Returns:
            str: 压缩后的摘要
        """
        # 构建待摘要的文本
        text_to_summarize = "\n\n".join([
            f"[{msg.role}]: {msg.content}"
            for msg in messages
        ])

        # 构建摘要提示
        prompt = f"""请对以下对话历史进行摘要，保留关键信息：

{text_to_summarize}

要求：
1. 提取关键决策和结论
2. 保留重要的技术细节
3. 忽略重复和无关内容
4. 使用简洁的语言
5. 摘要长度控制在原文的30%以内

摘要："""

        # 调用LLM生成摘要
        try:
            summary = llm_summarize_func(prompt)
            return summary
        except Exception as e:
            print(f"LLM摘要失败: {e}")
            # 降级到简单压缩
            return self._compress_simple(messages)

    def _compress_simple(self, messages: List[Message]) -> str:
        """
        简单压缩（不使用LLM）

        策略：
        1. 提取每条消息的前100个字符
        2. 合并为摘要

        Args:
            messages: 消息列表

        Returns:
            str: 压缩后的摘要
        """
        summaries = []

        for msg in messages:
            # 提取前100个字符
            preview = msg.content[:100]
            if len(msg.content) > 100:
                preview += "..."

            summaries.append(f"[{msg.role}]: {preview}")

        return "\n".join(summaries)

    def get_compression_stats(
        self,
        original_messages: List[Message],
        compressed_messages: List[Message]
    ) -> Dict[str, Any]:
        """
        获取压缩统计信息

        Args:
            original_messages: 原始消息列表
            compressed_messages: 压缩后消息列表

        Returns:
            dict: 压缩统计
        """
        original_tokens = self.count_messages_tokens(original_messages)
        compressed_tokens = self.count_messages_tokens(compressed_messages)

        compression_ratio = 1 - (compressed_tokens / original_tokens) if original_tokens > 0 else 0

        return {
            "original_messages": len(original_messages),
            "compressed_messages": len(compressed_messages),
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "tokens_saved": original_tokens - compressed_tokens,
            "compression_ratio": compression_ratio,
            "compression_percentage": f"{compression_ratio * 100:.1f}%"
        }


class ContextManager:
    """上下文管理器"""

    def __init__(self, agent_name: str, max_tokens: int = 8000):
        """
        初始化上下文管理器

        Args:
            agent_name: Agent名称
            max_tokens: 最大Token数
        """
        self.agent_name = agent_name
        self.max_tokens = max_tokens
        self.messages: List[Message] = []
        self.compressor = ContextCompressor(max_tokens=max_tokens)
        self.compression_count = 0

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        添加消息

        Args:
            role: 角色
            content: 内容
            metadata: 元数据
        """
        message = Message(role=role, content=content, metadata=metadata)
        self.messages.append(message)

        # 检查是否需要压缩
        if self.compressor.should_compress(self.messages):
            self._compress_context()

    def _compress_context(self, llm_summarize_func: Optional[callable] = None):
        """
        压缩上下文

        Args:
            llm_summarize_func: LLM摘要函数
        """
        print(f"\n[{self.agent_name}] 触发上下文压缩...")

        original_messages = self.messages.copy()

        # 执行压缩
        self.messages = self.compressor.compress(
            self.messages,
            llm_summarize_func
        )

        self.compression_count += 1

        # 打印统计信息
        stats = self.compressor.get_compression_stats(
            original_messages,
            self.messages
        )

        print(f"  压缩前: {stats['original_messages']}条消息, {stats['original_tokens']} tokens")
        print(f"  压缩后: {stats['compressed_messages']}条消息, {stats['compressed_tokens']} tokens")
        print(f"  节省: {stats['tokens_saved']} tokens ({stats['compression_percentage']})")

    def get_messages(self) -> List[Message]:
        """获取所有消息"""
        return self.messages

    def get_token_count(self) -> int:
        """获取当前Token数"""
        return self.compressor.count_messages_tokens(self.messages)

    def get_usage_percentage(self) -> float:
        """获取使用百分比"""
        current = self.get_token_count()
        return (current / self.max_tokens) * 100

    def clear(self):
        """清空上下文"""
        self.messages = []
        self.compression_count = 0
