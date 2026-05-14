"""
消息路由器

处理消息发送、接收、路由、存储
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..database.models import IMMessage, IMGroup, IMThread, User


class MessageType:
    """消息类型"""
    TEXT = "text"  # 文本消息
    IMAGE = "image"  # 图片
    FILE = "file"  # 文件
    CODE = "code"  # 代码片段
    SYSTEM = "system"  # 系统消息


class MessageRouter:
    """消息路由器"""

    def __init__(self, db: Session):
        self.db = db
        self.websocket_manager = None  # 将在API层注入

    def set_websocket_manager(self, manager):
        """
        设置WebSocket管理器

        为什么: 实现实时消息推送
        """
        self.websocket_manager = manager

    def send_message(
        self,
        sender_id: int,
        group_id: Optional[int] = None,
        thread_id: Optional[int] = None,
        content: str = "",
        message_type: str = MessageType.TEXT,
        extra_data: Optional[Dict[str, Any]] = None,
        reply_to: Optional[int] = None
    ) -> IMMessage:
        """
        发送消息

        为什么: 统一的消息发送接口
        """
        # 验证目标
        if not group_id and not thread_id:
            raise ValueError("Must specify either group_id or thread_id")

        # 创建消息
        message = IMMessage(
            sender_id=sender_id,
            group_id=group_id,
            thread_id=thread_id,
            content=content,
            message_type=message_type,
            extra_data=extra_data or {},
            reply_to=reply_to,
            sent_at=datetime.utcnow()
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        # 实时推送
        self._broadcast_message(message)

        return message

    def _broadcast_message(self, message: IMMessage):
        """
        广播消息到WebSocket

        为什么: 实现实时通信
        """
        if not self.websocket_manager:
            return

        # 获取接收者列表
        recipients = self._get_message_recipients(message)

        # 构造消息数据
        message_data = {
            "id": message.id,
            "sender_id": message.sender_id,
            "group_id": message.group_id,
            "thread_id": message.thread_id,
            "content": message.content,
            "message_type": message.message_type,
            "extra_data": message.extra_data,
            "reply_to": message.reply_to,
            "sent_at": message.sent_at.isoformat()
        }

        # 推送给所有接收者
        for user_id in recipients:
            try:
                self.websocket_manager.send_to_user(
                    user_id,
                    {
                        "type": "im_message",
                        "data": message_data
                    }
                )
            except Exception as e:
                # 记录错误但不中断
                print(f"Failed to send message to user {user_id}: {e}")

    def _get_message_recipients(self, message: IMMessage) -> List[int]:
        """
        获取消息接收者列表

        为什么: 确定哪些用户应该收到消息
        """
        from .group_manager import IMGroupMember

        recipients = []

        # 群组消息
        if message.group_id:
            members = self.db.query(IMGroupMember.user_id).filter(
                IMGroupMember.group_id == message.group_id
            ).all()
            recipients = [m[0] for m in members]

        # 线程消息（继承父群组成员）
        elif message.thread_id:
            thread = self.db.query(IMThread).filter(
                IMThread.id == message.thread_id
            ).first()
            if thread and thread.parent_group_id:
                members = self.db.query(IMGroupMember.user_id).filter(
                    IMGroupMember.group_id == thread.parent_group_id
                ).all()
                recipients = [m[0] for m in members]

        return recipients

    def get_messages(
        self,
        group_id: Optional[int] = None,
        thread_id: Optional[int] = None,
        limit: int = 50,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        获取消息列表

        为什么: 支持消息历史查询和分页加载
        """
        query = self.db.query(IMMessage, User).join(
            User, IMMessage.sender_id == User.id
        )

        # 过滤条件
        if group_id:
            query = query.filter(IMMessage.group_id == group_id)
        if thread_id:
            query = query.filter(IMMessage.thread_id == thread_id)
        if before:
            query = query.filter(IMMessage.sent_at < before)
        if after:
            query = query.filter(IMMessage.sent_at > after)

        # 排序和限制
        query = query.order_by(IMMessage.sent_at.desc()).limit(limit)

        messages = query.all()

        return [
            {
                "id": msg.id,
                "sender": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                },
                "group_id": msg.group_id,
                "thread_id": msg.thread_id,
                "content": msg.content,
                "message_type": msg.message_type,
                "extra_data": msg.extra_data,
                "reply_to": msg.reply_to,
                "sent_at": msg.sent_at.isoformat()
            }
            for msg, user in reversed(messages)  # 反转为正序
        ]

    def mark_as_read(
        self,
        user_id: int,
        message_ids: List[int]
    ) -> int:
        """
        标记消息为已读

        为什么: 跟踪用户阅读状态
        """
        from ..database.models import IMMessageRead

        count = 0
        for message_id in message_ids:
            # 检查是否已标记
            existing = self.db.query(IMMessageRead).filter(
                and_(
                    IMMessageRead.message_id == message_id,
                    IMMessageRead.user_id == user_id
                )
            ).first()

            if not existing:
                read_record = IMMessageRead(
                    message_id=message_id,
                    user_id=user_id,
                    read_at=datetime.utcnow()
                )
                self.db.add(read_record)
                count += 1

        self.db.commit()
        return count

    def get_unread_count(
        self,
        user_id: int,
        group_id: Optional[int] = None,
        thread_id: Optional[int] = None
    ) -> int:
        """
        获取未读消息数

        为什么: 显示未读消息提示
        """
        from ..database.models import IMMessageRead

        # 查询消息
        query = self.db.query(IMMessage).filter(
            IMMessage.sender_id != user_id  # 排除自己发送的
        )

        if group_id:
            query = query.filter(IMMessage.group_id == group_id)
        if thread_id:
            query = query.filter(IMMessage.thread_id == thread_id)

        # 排除已读消息
        query = query.outerjoin(
            IMMessageRead,
            and_(
                IMMessageRead.message_id == IMMessage.id,
                IMMessageRead.user_id == user_id
            )
        ).filter(IMMessageRead.id.is_(None))

        return query.count()

    def search_messages(
        self,
        keyword: str,
        group_id: Optional[int] = None,
        thread_id: Optional[int] = None,
        sender_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        搜索消息

        为什么: 支持消息内容搜索
        """
        query = self.db.query(IMMessage, User).join(
            User, IMMessage.sender_id == User.id
        ).filter(
            IMMessage.content.ilike(f"%{keyword}%")
        )

        if group_id:
            query = query.filter(IMMessage.group_id == group_id)
        if thread_id:
            query = query.filter(IMMessage.thread_id == thread_id)
        if sender_id:
            query = query.filter(IMMessage.sender_id == sender_id)

        query = query.order_by(IMMessage.sent_at.desc()).limit(limit)

        messages = query.all()

        return [
            {
                "id": msg.id,
                "sender": {
                    "id": user.id,
                    "username": user.username
                },
                "group_id": msg.group_id,
                "thread_id": msg.thread_id,
                "content": msg.content,
                "message_type": msg.message_type,
                "sent_at": msg.sent_at.isoformat()
            }
            for msg, user in messages
        ]
