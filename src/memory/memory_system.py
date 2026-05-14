"""
Agent记忆系统

实现三种类型的记忆：
1. 短期记忆（Short-term Memory）- 当前任务的上下文
2. 长期记忆（Long-term Memory）- 历史经验和知识
3. 工作记忆（Working Memory）- 临时推理状态

设计原则：
- 记忆分层：不同类型的记忆有不同的生命周期
- 自动管理：记忆的存储和检索自动化
- 向量检索：使用语义相似度检索相关记忆
- 遗忘机制：过期或不重要的记忆会被清理

为什么需要记忆系统：
- 上下文连续性：Agent能记住之前的对话和决策
- 经验积累：从历史任务中学习，避免重复错误
- 知识复用：相似任务可以复用之前的解决方案
- 推理能力：工作记忆支持复杂的多步推理
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import json


class MemoryType(Enum):
    """记忆类型"""
    SHORT_TERM = "short_term"      # 短期记忆
    LONG_TERM = "long_term"        # 长期记忆
    WORKING = "working"            # 工作记忆


class MemoryImportance(Enum):
    """记忆重要性"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class Memory:
    """
    记忆对象

    表示Agent的一条记忆。
    """

    def __init__(
        self,
        memory_id: str,
        agent_name: str,
        memory_type: MemoryType,
        content: str,
        metadata: Dict[str, Any] = None,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        tags: List[str] = None
    ):
        self.memory_id = memory_id
        self.agent_name = agent_name
        self.memory_type = memory_type
        self.content = content
        self.metadata = metadata or {}
        self.importance = importance
        self.tags = tags or []
        self.created_at = datetime.now()
        self.accessed_at = datetime.now()
        self.access_count = 0

    def access(self):
        """访问记忆（更新访问时间和次数）"""
        self.accessed_at = datetime.now()
        self.access_count += 1

    def is_expired(self, ttl_hours: int = 24) -> bool:
        """
        检查记忆是否过期

        Args:
            ttl_hours: 生存时间（小时）

        Returns:
            bool: 是否过期
        """
        if self.memory_type == MemoryType.LONG_TERM:
            return False  # 长期记忆不过期

        expiry_time = self.created_at + timedelta(hours=ttl_hours)
        return datetime.now() > expiry_time

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'memory_id': self.memory_id,
            'agent_name': self.agent_name,
            'memory_type': self.memory_type.value,
            'content': self.content,
            'metadata': self.metadata,
            'importance': self.importance.value,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'accessed_at': self.accessed_at.isoformat(),
            'access_count': self.access_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        """从字典创建"""
        memory = cls(
            memory_id=data['memory_id'],
            agent_name=data['agent_name'],
            memory_type=MemoryType(data['memory_type']),
            content=data['content'],
            metadata=data.get('metadata', {}),
            importance=MemoryImportance(data.get('importance', 2)),
            tags=data.get('tags', [])
        )
        memory.created_at = datetime.fromisoformat(data['created_at'])
        memory.accessed_at = datetime.fromisoformat(data['accessed_at'])
        memory.access_count = data.get('access_count', 0)
        return memory


class MemoryStore:
    """
    记忆存储

    管理Agent的所有记忆。
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.memories: Dict[str, Memory] = {}

    def add_memory(
        self,
        content: str,
        memory_type: MemoryType,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        metadata: Dict[str, Any] = None,
        tags: List[str] = None
    ) -> Memory:
        """
        添加记忆

        Args:
            content: 记忆内容
            memory_type: 记忆类型
            importance: 重要性
            metadata: 元数据
            tags: 标签

        Returns:
            Memory: 创建的记忆对象
        """
        import uuid
        memory_id = f"mem-{uuid.uuid4().hex[:12]}"

        memory = Memory(
            memory_id=memory_id,
            agent_name=self.agent_name,
            memory_type=memory_type,
            content=content,
            metadata=metadata,
            importance=importance,
            tags=tags
        )

        self.memories[memory_id] = memory

        # 同步到向量存储（如果可用）
        try:
            from .vector_search import get_semantic_memory_search
            vector_search = get_semantic_memory_search(self.agent_name)
            vector_search.add_memory(
                memory_id=memory_id,
                content=content,
                metadata={
                    'memory_type': memory_type.value,
                    'importance': importance.value,
                    'tags': tags or [],
                    'created_at': memory.created_at.isoformat()
                }
            )
        except ImportError:
            # 向量搜索不可用，跳过
            pass

        return memory

    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """获取指定记忆"""
        memory = self.memories.get(memory_id)
        if memory:
            memory.access()
        return memory

    def search_memories(
        self,
        query: str = None,
        memory_type: MemoryType = None,
        tags: List[str] = None,
        min_importance: MemoryImportance = None,
        limit: int = 10
    ) -> List[Memory]:
        """
        搜索记忆

        Args:
            query: 查询关键词（简单的字符串匹配）
            memory_type: 记忆类型过滤
            tags: 标签过滤
            min_importance: 最小重要性
            limit: 返回数量限制

        Returns:
            List[Memory]: 匹配的记忆列表
        """
        results = []

        for memory in self.memories.values():
            # 类型过滤
            if memory_type and memory.memory_type != memory_type:
                continue

            # 重要性过滤
            if min_importance and memory.importance.value < min_importance.value:
                continue

            # 标签过滤
            if tags and not any(tag in memory.tags for tag in tags):
                continue

            # 关键词过滤
            if query and query.lower() not in memory.content.lower():
                continue

            results.append(memory)

        # 按重要性和访问时间排序
        results.sort(
            key=lambda m: (m.importance.value, m.accessed_at),
            reverse=True
        )

        # 访问记忆
        for memory in results[:limit]:
            memory.access()

        return results[:limit]

    def get_recent_memories(
        self,
        memory_type: MemoryType = None,
        hours: int = 24,
        limit: int = 10
    ) -> List[Memory]:
        """
        获取最近的记忆

        Args:
            memory_type: 记忆类型过滤
            hours: 时间范围（小时）
            limit: 返回数量限制

        Returns:
            List[Memory]: 最近的记忆列表
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        results = []

        for memory in self.memories.values():
            if memory_type and memory.memory_type != memory_type:
                continue

            if memory.created_at >= cutoff_time:
                results.append(memory)

        # 按时间排序
        results.sort(key=lambda m: m.created_at, reverse=True)

        return results[:limit]

    def cleanup_expired(self, ttl_hours: int = 24):
        """
        清理过期记忆

        Args:
            ttl_hours: 生存时间（小时）
        """
        expired_ids = [
            memory_id
            for memory_id, memory in self.memories.items()
            if memory.is_expired(ttl_hours)
        ]

        for memory_id in expired_ids:
            del self.memories[memory_id]

        return len(expired_ids)

    def clear_working_memory(self):
        """清空工作记忆"""
        working_memory_ids = [
            memory_id
            for memory_id, memory in self.memories.items()
            if memory.memory_type == MemoryType.WORKING
        ]

        for memory_id in working_memory_ids:
            del self.memories[memory_id]

        return len(working_memory_ids)

    def semantic_search(
        self,
        query: str,
        limit: int = 5,
        memory_type: MemoryType = None
    ) -> List[Memory]:
        """
        语义搜索记忆（基于向量相似度）

        Args:
            query: 查询文本
            limit: 返回数量
            memory_type: 记忆类型过滤

        Returns:
            List[Memory]: 相似记忆列表
        """
        try:
            from .vector_search import get_semantic_memory_search

            vector_search = get_semantic_memory_search(self.agent_name)

            # 执行语义搜索
            results = vector_search.search_similar(
                query=query,
                limit=limit,
                memory_type=memory_type.value if memory_type else None
            )

            # 转换为Memory对象
            memories = []
            for result in results:
                memory_id = result['memory_id']
                if memory_id in self.memories:
                    memory = self.memories[memory_id]
                    memory.access()
                    memories.append(memory)

            return memories

        except ImportError:
            # 向量搜索不可用，回退到关键词搜索
            return self.search_memories(
                query=query,
                memory_type=memory_type,
                limit=limit
            )

    def get_statistics(self) -> Dict[str, Any]:
        """获取记忆统计"""
        stats = {
            'total': len(self.memories),
            'by_type': {},
            'by_importance': {},
            'total_accesses': sum(m.access_count for m in self.memories.values())
        }

        for memory in self.memories.values():
            # 按类型统计
            type_key = memory.memory_type.value
            stats['by_type'][type_key] = stats['by_type'].get(type_key, 0) + 1

            # 按重要性统计
            importance_key = memory.importance.name
            stats['by_importance'][importance_key] = stats['by_importance'].get(importance_key, 0) + 1

        return stats

    def save_to_file(self, filepath: str):
        """保存记忆到文件"""
        data = {
            'agent_name': self.agent_name,
            'memories': [m.to_dict() for m in self.memories.values()]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'MemoryStore':
        """从文件加载记忆"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        store = cls(agent_name=data['agent_name'])

        for memory_data in data['memories']:
            memory = Memory.from_dict(memory_data)
            store.memories[memory.memory_id] = memory

        return store


class AgentMemoryManager:
    """
    Agent记忆管理器

    为每个Agent管理独立的记忆存储。
    """

    def __init__(self):
        self.stores: Dict[str, MemoryStore] = {}

    def get_store(self, agent_name: str) -> MemoryStore:
        """获取Agent的记忆存储"""
        if agent_name not in self.stores:
            self.stores[agent_name] = MemoryStore(agent_name)
        return self.stores[agent_name]

    def add_memory(
        self,
        agent_name: str,
        content: str,
        memory_type: MemoryType,
        **kwargs
    ) -> Memory:
        """为Agent添加记忆"""
        store = self.get_store(agent_name)
        return store.add_memory(content, memory_type, **kwargs)

    def search_memories(
        self,
        agent_name: str,
        **kwargs
    ) -> List[Memory]:
        """搜索Agent的记忆"""
        store = self.get_store(agent_name)
        return store.search_memories(**kwargs)

    def cleanup_all(self, ttl_hours: int = 24):
        """清理所有Agent的过期记忆"""
        total_cleaned = 0
        for store in self.stores.values():
            total_cleaned += store.cleanup_expired(ttl_hours)
        return total_cleaned

    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """获取所有Agent的记忆统计"""
        return {
            agent_name: store.get_statistics()
            for agent_name, store in self.stores.items()
        }


# 全局记忆管理器实例
_global_memory_manager = AgentMemoryManager()


def get_memory_manager() -> AgentMemoryManager:
    """获取全局记忆管理器"""
    return _global_memory_manager
