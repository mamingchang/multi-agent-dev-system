"""
Message utilities
消息传递工具
"""
from typing import Dict, Any
from datetime import datetime


class Message:
    """消息对象"""

    def __init__(self, from_agent: str, to_agent: str, content: Any, msg_type: str = "info"):
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.content = content
        self.msg_type = msg_type  # info, question, approval, rejection
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'from': self.from_agent,
            'to': self.to_agent,
            'content': self.content,
            'type': self.msg_type,
            'timestamp': self.timestamp.isoformat()
        }

    def __repr__(self):
        return f"<Message(from='{self.from_agent}', to='{self.to_agent}', type='{self.msg_type}')>"
