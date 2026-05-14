"""
记忆管理器 - 标准化接口

提供与memory_system.py相同的功能，但使用标准化的类名
"""

from src.memory.memory_system import AgentMemoryManager as MemoryManager
from src.memory.memory_system import MemoryType

__all__ = ['MemoryManager', 'MemoryType']
