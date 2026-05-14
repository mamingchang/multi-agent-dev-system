"""
@提及处理器

处理消息中的@提及功能
"""

from typing import List, Set, Optional, Dict, Any
import re
from datetime import datetime
from sqlalchemy.orm import Session

from ..database.models import IMMention, User, IMMessage


class MentionHandler:
    """@提及处理器"""

    def __init__(self, db: Session):
        self.db = db

    def extract_mentions(self, content: str) -> Set[str]:
        """
        从消息内容中提取@提及

        为什么: 解析消息中的@username
        """
        # 匹配 @username 格式
        pattern = r'@(\w+)'
        mentions = re.findall(pattern, content)
        return set(mentions)

    def process_mentions(
        self,
        message_id: int,
        content: str,
        sender_id: int
    ) -> List[IMMention]:
        """
        处理消息中的@提及

        为什么: 创建提及记录并通知被提及用户
        """
        # 提取@提及
        usernames = self.extract_mentions(content)
        if not usernames:
            return []

        # 查找用户
        users = self.db.query(User).filter(
            User.username.in_(usernames)
        ).all()

        mentions = []
        for user in users:
            # 不能@自己
            if user.id == sender_id:
                continue

            # 创建提及记录
            mention = IMMention(
                message_id=message_id,
                mentioned_user_id=user.id,
                mentioned_by=sender_id,
                mentioned_at=datetime.utcnow(),
                is_read=False
            )
            self.db.add(mention)
            mentions.append(mention)

        self.db.commit()

        # 发送通知
        self._send_mention_notifications(mentions)

        return mentions

    def _send_mention_notifications(self, mentions: List[IMMention]):
        """
        发送@提及通知

        为什么: 通知被@的用户
        """
        # TODO: 集成通知系统
        # 这里可以发送邮件、推送通知等
        pass

    def get_user_mentions(
        self,
        user_id: int,
        is_read: Optional[bool] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取用户的@提及列表

        为什么: 显示用户被@的消息
        """
        query = self.db.query(IMMention, IMMessage, User).join(
            IMMessage, IMMention.message_id == IMMessage.id
        ).join(
            User, IMMention.mentioned_by == User.id
        ).filter(
            IMMention.mentioned_user_id == user_id
        )

        if is_read is not None:
            query = query.filter(IMMention.is_read == is_read)

        query = query.order_by(IMMention.mentioned_at.desc()).limit(limit)

        mentions = query.all()

        return [
            {
                "id": mention.id,
                "message": {
                    "id": message.id,
                    "content": message.content,
                    "group_id": message.group_id,
                    "thread_id": message.thread_id,
                    "sent_at": message.sent_at.isoformat()
                },
                "mentioned_by": {
                    "id": user.id,
                    "username": user.username
                },
                "mentioned_at": mention.mentioned_at.isoformat(),
                "is_read": mention.is_read
            }
            for mention, message, user in mentions
        ]

    def mark_mentions_as_read(
        self,
        user_id: int,
        mention_ids: List[int]
    ) -> int:
        """
        标记@提及为已读

        为什么: 跟踪用户是否已查看@提及
        """
        count = self.db.query(IMMention).filter(
            IMMention.id.in_(mention_ids),
            IMMention.mentioned_user_id == user_id
        ).update(
            {"is_read": True},
            synchronize_session=False
        )
        self.db.commit()
        return count

    def get_unread_mention_count(self, user_id: int) -> int:
        """
        获取未读@提及数量

        为什么: 显示未读@提及数量徽章
        """
        return self.db.query(IMMention).filter(
            IMMention.mentioned_user_id == user_id,
            IMMention.is_read == False
        ).count()
