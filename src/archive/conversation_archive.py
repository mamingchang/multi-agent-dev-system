"""
对话归档系统

提供实时存储、永久归档、记忆关联功能
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import json
import hashlib


class ConversationArchive:
    """
    对话归档管理器

    为什么: 保存所有对话历史，支持回溯和分析
    """

    def __init__(self, db: Session):
        self.db = db

    def archive_conversation(
        self,
        session_id: str,
        messages: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        归档对话

        为什么: 实时保存对话内容，防止数据丢失
        """
        from ..database.models import ConversationArchive as ArchiveModel

        # 生成归档ID
        archive_id = self._generate_archive_id(session_id)

        # 计算对话摘要
        summary = self._generate_summary(messages)

        # 创建归档记录
        archive = ArchiveModel(
            archive_id=archive_id,
            session_id=session_id,
            messages=messages,
            message_count=len(messages),
            summary=summary,
            metadata=metadata or {},
            archived_at=datetime.utcnow()
        )

        self.db.add(archive)
        self.db.commit()

        return archive_id

    def _generate_archive_id(self, session_id: str) -> str:
        """
        生成归档ID

        为什么: 唯一标识每个归档
        """
        timestamp = datetime.utcnow().timestamp()
        raw = f"{session_id}_{timestamp}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _generate_summary(self, messages: List[Dict[str, Any]]) -> str:
        """
        生成对话摘要

        为什么: 快速了解对话内容
        """
        if not messages:
            return "Empty conversation"

        # 提取关键信息
        total_messages = len(messages)
        user_messages = [m for m in messages if m.get("role") == "user"]
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]

        # 提取第一条和最后一条用户消息
        first_user_msg = user_messages[0]["content"][:100] if user_messages else ""
        last_user_msg = user_messages[-1]["content"][:100] if user_messages else ""

        summary = f"Total: {total_messages} messages ({len(user_messages)} user, {len(assistant_messages)} assistant). "
        summary += f"Started with: '{first_user_msg}...'"

        if len(user_messages) > 1:
            summary += f" Ended with: '{last_user_msg}...'"

        return summary

    def retrieve_conversation(
        self,
        archive_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        检索归档对话

        为什么: 查看历史对话内容
        """
        from ..database.models import ConversationArchive as ArchiveModel

        archive = self.db.query(ArchiveModel).filter(
            ArchiveModel.archive_id == archive_id
        ).first()

        if not archive:
            return None

        return {
            "archive_id": archive.archive_id,
            "session_id": archive.session_id,
            "messages": archive.messages,
            "message_count": archive.message_count,
            "summary": archive.summary,
            "metadata": archive.metadata,
            "archived_at": archive.archived_at.isoformat(),
            "linked_memories": self._get_linked_memories(archive_id)
        }

    def search_archives(
        self,
        session_id: Optional[str] = None,
        keyword: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        搜索归档

        为什么: 查找特定的历史对话
        """
        from ..database.models import ConversationArchive as ArchiveModel

        query = self.db.query(ArchiveModel)

        if session_id:
            query = query.filter(ArchiveModel.session_id == session_id)

        if keyword:
            query = query.filter(ArchiveModel.summary.ilike(f"%{keyword}%"))

        if start_date:
            query = query.filter(ArchiveModel.archived_at >= start_date)

        if end_date:
            query = query.filter(ArchiveModel.archived_at <= end_date)

        archives = query.order_by(
            ArchiveModel.archived_at.desc()
        ).limit(limit).all()

        return [
            {
                "archive_id": a.archive_id,
                "session_id": a.session_id,
                "message_count": a.message_count,
                "summary": a.summary,
                "archived_at": a.archived_at.isoformat()
            }
            for a in archives
        ]

    def link_to_memory(
        self,
        archive_id: str,
        memory_id: str,
        link_type: str = "reference"
    ) -> bool:
        """
        关联到记忆系统

        为什么: 将对话与记忆关联，便于知识管理
        """
        from ..database.models import ArchiveMemoryLink

        # 检查归档是否存在
        from ..database.models import ConversationArchive as ArchiveModel
        archive = self.db.query(ArchiveModel).filter(
            ArchiveModel.archive_id == archive_id
        ).first()

        if not archive:
            return False

        # 创建关联
        link = ArchiveMemoryLink(
            archive_id=archive_id,
            memory_id=memory_id,
            link_type=link_type,
            created_at=datetime.utcnow()
        )

        self.db.add(link)
        self.db.commit()

        return True

    def _get_linked_memories(self, archive_id: str) -> List[Dict[str, Any]]:
        """
        获取关联的记忆

        为什么: 显示与对话相关的记忆
        """
        from ..database.models import ArchiveMemoryLink

        links = self.db.query(ArchiveMemoryLink).filter(
            ArchiveMemoryLink.archive_id == archive_id
        ).all()

        return [
            {
                "memory_id": link.memory_id,
                "link_type": link.link_type,
                "created_at": link.created_at.isoformat()
            }
            for link in links
        ]

    def delete_archive(self, archive_id: str) -> bool:
        """
        删除归档

        为什么: 清理不需要的归档
        """
        from ..database.models import ConversationArchive as ArchiveModel

        archive = self.db.query(ArchiveModel).filter(
            ArchiveModel.archive_id == archive_id
        ).first()

        if archive:
            self.db.delete(archive)
            self.db.commit()
            return True

        return False

    def get_statistics(
        self,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取归档统计

        为什么: 了解归档使用情况
        """
        from ..database.models import ConversationArchive as ArchiveModel

        query = self.db.query(ArchiveModel)

        if session_id:
            query = query.filter(ArchiveModel.session_id == session_id)

        total_archives = query.count()
        total_messages = self.db.query(
            self.db.func.sum(ArchiveModel.message_count)
        ).scalar() or 0

        return {
            "total_archives": total_archives,
            "total_messages": int(total_messages),
            "average_messages_per_archive": round(
                total_messages / total_archives, 2
            ) if total_archives > 0 else 0
        }
