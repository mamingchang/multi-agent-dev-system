"""
Base Agent Class
所有角色Agent的基类，定义通用接口和行为
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime


class BaseAgent(ABC):
    """Agent基类"""

    def __init__(self, name: str, role: str, config: Dict[str, Any] = None):
        self.name = name
        self.role = role
        self.config = config or {}
        self.history: List[Dict] = []

    @abstractmethod
    def process(self, task: Any) -> Dict[str, Any]:
        """
        处理任务的核心方法，每个具体Agent必须实现

        Args:
            task: 任务对象

        Returns:
            处理结果字典
        """
        pass

    def receive_message(self, message: Dict[str, Any]) -> None:
        """接收消息"""
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'received',
            'content': message
        })

    def send_message(self, to_agent: str, content: Any) -> Dict[str, Any]:
        """发送消息"""
        message = {
            'from': self.name,
            'to': to_agent,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'sent',
            'content': message
        })
        return message

    def get_history(self) -> List[Dict]:
        """获取历史记录"""
        return self.history

    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}', role='{self.role}')>"
