"""
IM群聊系统模块

提供项目群组、任务线程、实时通信、@提及、人工介入等功能
"""

from .group_manager import GroupManager
from .message_router import MessageRouter
from .mention_handler import MentionHandler
from .intervention_manager import InterventionManager

__all__ = [
    "GroupManager",
    "MessageRouter",
    "MentionHandler",
    "InterventionManager",
]
