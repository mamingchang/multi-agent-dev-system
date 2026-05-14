"""
Conversation System
对话系统：管理Agent之间的多轮对话

核心功能：
1. 记录Agent之间的对话
2. 支持不同类型的消息（提问、建议、质疑、批准）
3. 提供对话历史查询
4. 支持反馈循环
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class MessageType(Enum):
    """
    消息类型枚举

    定义Agent之间可以发送的消息类型
    """
    QUESTION = "question"              # 提问
    SUGGESTION = "suggestion"          # 建议
    OBJECTION = "objection"           # 质疑/反对
    REVISION_REQUEST = "revision_request"  # 要求修改
    APPROVAL = "approval"             # 批准通过
    INFO = "info"                     # 信息通知
    CLARIFICATION = "clarification"   # 澄清说明


class Message:
    """
    消息类

    表示Agent之间的一条消息。
    """

    def __init__(
        self,
        from_agent: str,
        to_agent: str,
        content: Any,
        message_type: MessageType,
        reference_artifact: Optional[str] = None
    ):
        """
        初始化消息

        Args:
            from_agent: 发送者Agent名称
            to_agent: 接收者Agent名称
            content: 消息内容（可以是字符串或字典）
            message_type: 消息类型
            reference_artifact: 引用的产物类型（可选）
        """
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.content = content
        self.message_type = message_type
        self.reference_artifact = reference_artifact
        self.timestamp = datetime.now()
        self.id = f"{from_agent}-{to_agent}-{self.timestamp.timestamp()}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'from': self.from_agent,
            'to': self.to_agent,
            'content': self.content,
            'type': self.message_type.value,
            'reference_artifact': self.reference_artifact,
            'timestamp': self.timestamp.isoformat()
        }

    def __repr__(self) -> str:
        return f"Message({self.from_agent} → {self.to_agent}: {self.message_type.value})"


class Conversation:
    """
    对话类

    管理一个任务中所有Agent之间的对话历史。

    设计思想：
    - 对话是任务的一部分，记录协作过程
    - 支持查询特定Agent的相关对话
    - 支持按类型过滤消息
    """

    def __init__(self):
        """初始化对话"""
        self.messages: List[Message] = []

    def add_message(
        self,
        from_agent: str,
        to_agent: str,
        content: Any,
        message_type: MessageType,
        reference_artifact: Optional[str] = None
    ) -> Message:
        """
        添加一条消息

        Args:
            from_agent: 发送者
            to_agent: 接收者
            content: 内容
            message_type: 类型
            reference_artifact: 引用的产物

        Returns:
            Message: 创建的消息对象
        """
        message = Message(
            from_agent=from_agent,
            to_agent=to_agent,
            content=content,
            message_type=message_type,
            reference_artifact=reference_artifact
        )

        self.messages.append(message)

        # 打印消息（用于调试和可视化）
        self._print_message(message)

        return message

    def _print_message(self, message: Message):
        """
        打印消息（格式化输出）

        让用户能看到Agent之间的对话
        """
        icon_map = {
            MessageType.QUESTION: "❓",
            MessageType.SUGGESTION: "💡",
            MessageType.OBJECTION: "⚠️",
            MessageType.REVISION_REQUEST: "🔄",
            MessageType.APPROVAL: "✅",
            MessageType.INFO: "ℹ️",
            MessageType.CLARIFICATION: "📝"
        }

        icon = icon_map.get(message.message_type, "💬")

        print(f"\n{icon} [{message.from_agent} → {message.to_agent}] {message.message_type.value}")

        # 打印内容（如果是字典，格式化输出）
        if isinstance(message.content, dict):
            for key, value in message.content.items():
                print(f"   {key}: {value}")
        else:
            print(f"   {message.content}")

    def get_messages_for(self, agent_name: str) -> List[Message]:
        """
        获取与指定Agent相关的所有消息

        包括：
        - 发送给该Agent的消息
        - 该Agent发送的消息

        Args:
            agent_name: Agent名称

        Returns:
            List[Message]: 相关消息列表
        """
        return [
            msg for msg in self.messages
            if msg.from_agent == agent_name or msg.to_agent == agent_name
        ]

    def get_messages_to(self, agent_name: str) -> List[Message]:
        """
        获取发送给指定Agent的消息

        Args:
            agent_name: Agent名称

        Returns:
            List[Message]: 消息列表
        """
        return [msg for msg in self.messages if msg.to_agent == agent_name]

    def get_messages_from(self, agent_name: str) -> List[Message]:
        """
        获取指定Agent发送的消息

        Args:
            agent_name: Agent名称

        Returns:
            List[Message]: 消息列表
        """
        return [msg for msg in self.messages if msg.from_agent == agent_name]

    def get_messages_by_type(self, message_type: MessageType) -> List[Message]:
        """
        按类型获取消息

        Args:
            message_type: 消息类型

        Returns:
            List[Message]: 消息列表
        """
        return [msg for msg in self.messages if msg.message_type == message_type]

    def get_feedback_for(self, agent_name: str) -> List[Message]:
        """
        获取发送给指定Agent的反馈消息

        反馈消息包括：
        - REVISION_REQUEST（要求修改）
        - OBJECTION（质疑）
        - SUGGESTION（建议）

        Args:
            agent_name: Agent名称

        Returns:
            List[Message]: 反馈消息列表
        """
        feedback_types = [
            MessageType.REVISION_REQUEST,
            MessageType.OBJECTION,
            MessageType.SUGGESTION
        ]

        return [
            msg for msg in self.messages
            if msg.to_agent == agent_name and msg.message_type in feedback_types
        ]

    def has_unresolved_feedback(self, agent_name: str) -> bool:
        """
        检查是否有未解决的反馈

        如果有反馈消息，但该Agent还没有回应，则认为是未解决的。

        Args:
            agent_name: Agent名称

        Returns:
            bool: 是否有未解决的反馈
        """
        feedback = self.get_feedback_for(agent_name)
        if not feedback:
            return False

        # 检查是否有回应
        # 简化版本：如果有反馈，就认为需要处理
        return True

    def get_conversation_context(self, agent_name: str, max_messages: int = 10) -> str:
        """
        获取对话上下文（用于传递给LLM）

        将对话历史格式化为文本，让Agent能看到之前的讨论。

        Args:
            agent_name: Agent名称
            max_messages: 最多返回多少条消息

        Returns:
            str: 格式化的对话上下文
        """
        messages = self.get_messages_for(agent_name)

        # 只取最近的N条消息
        recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages

        if not recent_messages:
            return "（暂无对话历史）"

        # 格式化为文本
        context_lines = ["## 对话历史\n"]

        for msg in recent_messages:
            context_lines.append(f"[{msg.from_agent} → {msg.to_agent}] {msg.message_type.value}:")

            if isinstance(msg.content, dict):
                for key, value in msg.content.items():
                    context_lines.append(f"  - {key}: {value}")
            else:
                context_lines.append(f"  {msg.content}")

            context_lines.append("")  # 空行

        return "\n".join(context_lines)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（用于序列化）"""
        return {
            'messages': [msg.to_dict() for msg in self.messages],
            'total_messages': len(self.messages)
        }

    def __len__(self) -> int:
        """返回消息数量"""
        return len(self.messages)

    def __repr__(self) -> str:
        return f"Conversation({len(self.messages)} messages)"
