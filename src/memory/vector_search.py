"""
向量检索系统（Vector Retrieval System）

使用向量数据库实现语义相似度搜索，提升记忆和经验检索的智能性。

为什么需要向量检索：
1. 关键词匹配有限：无法理解语义相似性
2. 同义词问题："登录"和"sign in"应该匹配
3. 上下文理解：理解查询意图而不仅仅是字面匹配
4. 相关性排序：按语义相似度排序结果

技术选型：
- ChromaDB：轻量级向量数据库，易于集成
- Sentence Transformers：生成文本嵌入向量
- 支持本地部署，无需外部API

架构：
┌──────────────┐
│  查询文本    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  嵌入模型    │  (Sentence Transformer)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  向量数据库  │  (ChromaDB)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  相似结果    │
└──────────────┘
"""

from typing import List, Dict, Any, Optional
import os
from datetime import datetime


class VectorStore:
    """
    向量存储

    封装ChromaDB，提供向量存储和检索功能。
    """

    def __init__(self, collection_name: str, persist_directory: str = "./chroma_db"):
        """
        初始化向量存储

        Args:
            collection_name: 集合名称
            persist_directory: 持久化目录
        """
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            raise ImportError(
                "ChromaDB未安装。请安装: pip install chromadb sentence-transformers"
            )

        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # 创建ChromaDB客户端
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_directory
        ))

        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": f"Vector store for {collection_name}"}
        )

        print(f"[VectorStore] 初始化完成: {collection_name}")

    def add(
        self,
        ids: List[str],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ):
        """
        添加文档到向量存储

        Args:
            ids: 文档ID列表
            documents: 文档内容列表
            metadatas: 元数据列表（可选）
        """
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        print(f"[VectorStore] 添加 {len(ids)} 个文档")

    def query(
        self,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        查询相似文档

        Args:
            query_texts: 查询文本列表
            n_results: 返回结果数量
            where: 元数据过滤条件

        Returns:
            Dict: 查询结果
            {
                'ids': [[...]],
                'documents': [[...]],
                'metadatas': [[...]],
                'distances': [[...]]
            }
        """
        results = self.collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where
        )

        return results

    def update(
        self,
        ids: List[str],
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ):
        """
        更新文档

        Args:
            ids: 文档ID列表
            documents: 新文档内容（可选）
            metadatas: 新元数据（可选）
        """
        self.collection.update(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    def delete(self, ids: List[str]):
        """
        删除文档

        Args:
            ids: 文档ID列表
        """
        self.collection.delete(ids=ids)

    def count(self) -> int:
        """获取文档数量"""
        return self.collection.count()

    def persist(self):
        """持久化到磁盘"""
        self.client.persist()


class SemanticMemorySearch:
    """
    语义记忆搜索

    为记忆系统添加语义搜索能力。
    """

    def __init__(self, agent_name: str):
        """
        初始化

        Args:
            agent_name: Agent名称
        """
        self.agent_name = agent_name
        self.vector_store = VectorStore(
            collection_name=f"memories_{agent_name}",
            persist_directory="./chroma_db/memories"
        )

    def add_memory(self, memory_id: str, content: str, metadata: Dict[str, Any]):
        """
        添加记忆到向量存储

        Args:
            memory_id: 记忆ID
            content: 记忆内容
            metadata: 元数据
        """
        self.vector_store.add(
            ids=[memory_id],
            documents=[content],
            metadatas=[metadata]
        )

    def search_similar(
        self,
        query: str,
        limit: int = 5,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相似记忆

        Args:
            query: 查询文本
            limit: 返回数量
            memory_type: 记忆类型过滤

        Returns:
            List[Dict]: 相似记忆列表
        """
        # 构建过滤条件
        where = None
        if memory_type:
            where = {"memory_type": memory_type}

        # 查询
        results = self.vector_store.query(
            query_texts=[query],
            n_results=limit,
            where=where
        )

        # 格式化结果
        memories = []
        if results['ids'] and len(results['ids']) > 0:
            for i in range(len(results['ids'][0])):
                memories.append({
                    'memory_id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'similarity': 1 - results['distances'][0][i]  # 转换为相似度
                })

        return memories

    def delete_memory(self, memory_id: str):
        """删除记忆"""
        self.vector_store.delete(ids=[memory_id])

    def count(self) -> int:
        """获取记忆数量"""
        return self.vector_store.count()


class SemanticExperienceSearch:
    """
    语义经验搜索

    为经验系统添加语义搜索能力。
    """

    def __init__(self):
        """初始化"""
        self.vector_store = VectorStore(
            collection_name="experiences",
            persist_directory="./chroma_db/experiences"
        )

    def add_experience(
        self,
        experience_id: str,
        title: str,
        description: str,
        metadata: Dict[str, Any]
    ):
        """
        添加经验到向量存储

        Args:
            experience_id: 经验ID
            title: 标题
            description: 描述
            metadata: 元数据
        """
        # 组合标题和描述作为文档内容
        document = f"{title}\n{description}"

        self.vector_store.add(
            ids=[experience_id],
            documents=[document],
            metadatas=[metadata]
        )

    def search_similar(
        self,
        query: str,
        limit: int = 5,
        experience_type: Optional[str] = None,
        min_confidence: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        搜索相似经验

        Args:
            query: 查询文本
            limit: 返回数量
            experience_type: 经验类型过滤
            min_confidence: 最小置信度

        Returns:
            List[Dict]: 相似经验列表
        """
        # 构建过滤条件
        where = {}
        if experience_type:
            where["experience_type"] = experience_type
        if min_confidence > 0:
            where["confidence"] = {"$gte": min_confidence}

        # 查询
        results = self.vector_store.query(
            query_texts=[query],
            n_results=limit,
            where=where if where else None
        )

        # 格式化结果
        experiences = []
        if results['ids'] and len(results['ids']) > 0:
            for i in range(len(results['ids'][0])):
                experiences.append({
                    'experience_id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'similarity': 1 - results['distances'][0][i]
                })

        return experiences

    def delete_experience(self, experience_id: str):
        """删除经验"""
        self.vector_store.delete(ids=[experience_id])

    def count(self) -> int:
        """获取经验数量"""
        return self.vector_store.count()


# 全局实例
_semantic_memory_stores: Dict[str, SemanticMemorySearch] = {}
_semantic_experience_store: Optional[SemanticExperienceSearch] = None


def get_semantic_memory_search(agent_name: str) -> SemanticMemorySearch:
    """
    获取Agent的语义记忆搜索实例

    Args:
        agent_name: Agent名称

    Returns:
        SemanticMemorySearch: 语义记忆搜索实例
    """
    global _semantic_memory_stores

    if agent_name not in _semantic_memory_stores:
        _semantic_memory_stores[agent_name] = SemanticMemorySearch(agent_name)

    return _semantic_memory_stores[agent_name]


def get_semantic_experience_search() -> SemanticExperienceSearch:
    """
    获取全局语义经验搜索实例

    Returns:
        SemanticExperienceSearch: 语义经验搜索实例
    """
    global _semantic_experience_store

    if _semantic_experience_store is None:
        _semantic_experience_store = SemanticExperienceSearch()

    return _semantic_experience_store
