"""
通知配置和历史记录Repository

提供通知配置管理和历史记录查询功能。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from .models import (
    NotificationConfig, NotificationHistory,
    NotificationType, NotificationChannel, NotificationStatus
)


class NotificationConfigRepository:
    """通知配置Repository"""

    def __init__(self, session: Session):
        """
        初始化Repository

        Args:
            session: SQLAlchemy会话
        """
        self.session = session

    def create_config(
        self,
        user_id: int,
        notification_type: NotificationType,
        channel: NotificationChannel,
        is_enabled: bool = True,
        config: Optional[Dict[str, Any]] = None,
        organization_id: Optional[int] = None
    ) -> NotificationConfig:
        """
        创建通知配置

        Args:
            user_id: 用户ID
            notification_type: 通知类型
            channel: 通知渠道
            is_enabled: 是否启用
            config: 配置信息（如邮箱地址、Slack webhook等）
            organization_id: 组织ID（可选）

        Returns:
            NotificationConfig: 创建的配置
        """
        notification_config = NotificationConfig(
            user_id=user_id,
            organization_id=organization_id,
            notification_type=notification_type,
            channel=channel,
            is_enabled=is_enabled,
            config=config or {}
        )

        self.session.add(notification_config)
        self.session.commit()
        self.session.refresh(notification_config)

        return notification_config

    def get_config(self, config_id: int) -> Optional[NotificationConfig]:
        """
        获取通知配置

        Args:
            config_id: 配置ID

        Returns:
            Optional[NotificationConfig]: 配置对象，不存在返回None
        """
        return self.session.query(NotificationConfig).filter(
            NotificationConfig.id == config_id
        ).first()

    def get_user_configs(
        self,
        user_id: int,
        organization_id: Optional[int] = None,
        notification_type: Optional[NotificationType] = None,
        channel: Optional[NotificationChannel] = None,
        enabled_only: bool = True
    ) -> List[NotificationConfig]:
        """
        获取用户的通知配置列表

        Args:
            user_id: 用户ID
            organization_id: 组织ID（可选）
            notification_type: 通知类型（可选）
            channel: 通知渠道（可选）
            enabled_only: 只返回启用的配置

        Returns:
            List[NotificationConfig]: 配置列表
        """
        query = self.session.query(NotificationConfig).filter(
            NotificationConfig.user_id == user_id
        )

        if organization_id is not None:
            query = query.filter(NotificationConfig.organization_id == organization_id)

        if notification_type is not None:
            query = query.filter(NotificationConfig.notification_type == notification_type)

        if channel is not None:
            query = query.filter(NotificationConfig.channel == channel)

        if enabled_only:
            query = query.filter(NotificationConfig.is_enabled == True)

        return query.all()

    def update_config(
        self,
        config_id: int,
        is_enabled: Optional[bool] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[NotificationConfig]:
        """
        更新通知配置

        Args:
            config_id: 配置ID
            is_enabled: 是否启用
            config: 配置信息

        Returns:
            Optional[NotificationConfig]: 更新后的配置，不存在返回None
        """
        notification_config = self.get_config(config_id)

        if not notification_config:
            return None

        if is_enabled is not None:
            notification_config.is_enabled = is_enabled

        if config is not None:
            notification_config.config = config

        notification_config.updated_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(notification_config)

        return notification_config

    def delete_config(self, config_id: int) -> bool:
        """
        删除通知配置

        Args:
            config_id: 配置ID

        Returns:
            bool: 是否删除成功
        """
        notification_config = self.get_config(config_id)

        if not notification_config:
            return False

        self.session.delete(notification_config)
        self.session.commit()

        return True


class NotificationHistoryRepository:
    """通知历史Repository"""

    def __init__(self, session: Session):
        """
        初始化Repository

        Args:
            session: SQLAlchemy会话
        """
        self.session = session

    def create_history(
        self,
        user_id: int,
        notification_type: NotificationType,
        channel: NotificationChannel,
        subject: str,
        content: str,
        status: NotificationStatus = NotificationStatus.PENDING,
        organization_id: Optional[int] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> NotificationHistory:
        """
        创建通知历史记录

        Args:
            user_id: 用户ID
            notification_type: 通知类型
            channel: 通知渠道
            subject: 通知主题
            content: 通知内容
            status: 发送状态
            organization_id: 组织ID（可选）
            extra_data: 额外数据（可选）

        Returns:
            NotificationHistory: 创建的历史记录
        """
        history = NotificationHistory(
            user_id=user_id,
            organization_id=organization_id,
            notification_type=notification_type,
            channel=channel,
            subject=subject,
            content=content,
            status=status,
            extra_data=extra_data or {}
        )

        self.session.add(history)
        self.session.commit()
        self.session.refresh(history)

        return history

    def update_status(
        self,
        history_id: int,
        status: NotificationStatus,
        error_message: Optional[str] = None
    ) -> Optional[NotificationHistory]:
        """
        更新通知发送状态

        Args:
            history_id: 历史记录ID
            status: 新状态
            error_message: 错误信息（如果失败）

        Returns:
            Optional[NotificationHistory]: 更新后的记录，不存在返回None
        """
        history = self.session.query(NotificationHistory).filter(
            NotificationHistory.id == history_id
        ).first()

        if not history:
            return None

        history.status = status

        if status == NotificationStatus.SENT:
            history.sent_at = datetime.utcnow()
        elif status == NotificationStatus.FAILED and error_message:
            history.error_message = error_message

        self.session.commit()
        self.session.refresh(history)

        return history

    def list_history(
        self,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        notification_type: Optional[NotificationType] = None,
        channel: Optional[NotificationChannel] = None,
        status: Optional[NotificationStatus] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[NotificationHistory]:
        """
        查询通知历史记录

        Args:
            user_id: 用户ID（可选）
            organization_id: 组织ID（可选）
            notification_type: 通知类型（可选）
            channel: 通知渠道（可选）
            status: 发送状态（可选）
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[NotificationHistory]: 历史记录列表
        """
        query = self.session.query(NotificationHistory)

        if user_id is not None:
            query = query.filter(NotificationHistory.user_id == user_id)

        if organization_id is not None:
            query = query.filter(NotificationHistory.organization_id == organization_id)

        if notification_type is not None:
            query = query.filter(NotificationHistory.notification_type == notification_type)

        if channel is not None:
            query = query.filter(NotificationHistory.channel == channel)

        if status is not None:
            query = query.filter(NotificationHistory.status == status)

        if start_time is not None:
            query = query.filter(NotificationHistory.created_at >= start_time)

        if end_time is not None:
            query = query.filter(NotificationHistory.created_at <= end_time)

        return query.order_by(NotificationHistory.created_at.desc()).limit(limit).offset(offset).all()

    def get_stats(
        self,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取通知统计信息

        Args:
            user_id: 用户ID（可选）
            organization_id: 组织ID（可选）
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）

        Returns:
            Dict[str, Any]: 统计信息
        """
        query = self.session.query(NotificationHistory)

        if user_id is not None:
            query = query.filter(NotificationHistory.user_id == user_id)

        if organization_id is not None:
            query = query.filter(NotificationHistory.organization_id == organization_id)

        if start_time is not None:
            query = query.filter(NotificationHistory.created_at >= start_time)

        if end_time is not None:
            query = query.filter(NotificationHistory.created_at <= end_time)

        # 总数
        total = query.count()

        # 按状态统计
        status_stats = {}
        for status in NotificationStatus:
            count = query.filter(NotificationHistory.status == status).count()
            status_stats[status.value] = count

        # 按渠道统计
        channel_stats = {}
        for channel in NotificationChannel:
            count = query.filter(NotificationHistory.channel == channel).count()
            channel_stats[channel.value] = count

        # 按类型统计
        type_stats = {}
        for ntype in NotificationType:
            count = query.filter(NotificationHistory.notification_type == ntype).count()
            type_stats[ntype.value] = count

        return {
            "total": total,
            "by_status": status_stats,
            "by_channel": channel_stats,
            "by_type": type_stats
        }
