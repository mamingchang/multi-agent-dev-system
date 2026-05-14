"""
通知系统API路由

端点：
- POST /notifications/send - 发送通知
- GET /notifications/configs - 获取通知配置列表
- POST /notifications/configs - 创建通知配置
- PUT /notifications/configs/{config_id} - 更新通知配置
- DELETE /notifications/configs/{config_id} - 删除通知配置
- GET /notifications/history - 获取通知历史
- GET /notifications/stats - 获取通知统计
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime

from ..database.database import Database
from ..database.notification_repository import (
    NotificationConfigRepository, NotificationHistoryRepository
)
from ..database.models import (
    User, NotificationType, NotificationChannel, NotificationStatus
)
from ..notifications.notification_service import (
    EmailNotifier, SlackNotifier, NotificationService
)
from .schemas import (
    NotificationSendRequest, NotificationConfigCreate, NotificationConfigUpdate,
    NotificationConfigResponse, NotificationHistoryResponse, NotificationStatsResponse,
    MessageResponse
)
from .auth import get_current_active_user
from .dependencies import get_db

router = APIRouter(prefix="/notifications", tags=["通知系统"])


@router.post("/send", response_model=MessageResponse)
def send_notification(
    notification_data: NotificationSendRequest,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    发送通知

    支持邮件和Slack两种渠道。
    """
    with db.get_session() as session:
        history_repo = NotificationHistoryRepository(session)

        # 创建历史记录
        history = history_repo.create_history(
            user_id=current_user.id,
            organization_id=notification_data.organization_id,
            notification_type=NotificationType[notification_data.notification_type.upper()],
            channel=NotificationChannel[notification_data.channel.upper()],
            subject=notification_data.subject,
            content=notification_data.content,
            status=NotificationStatus.PENDING,
            extra_data=notification_data.metadata
        )

        # 根据渠道发送通知
        success = False
        error_message = None

        try:
            if notification_data.channel == "email":
                # 发送邮件
                if not notification_data.email_config:
                    raise ValueError("邮件配置不能为空")

                notifier = EmailNotifier(
                    smtp_host=notification_data.email_config.get("smtp_host"),
                    smtp_port=notification_data.email_config.get("smtp_port"),
                    smtp_user=notification_data.email_config.get("smtp_user"),
                    smtp_password=notification_data.email_config.get("smtp_password"),
                    from_email=notification_data.email_config.get("from_email"),
                    use_tls=notification_data.email_config.get("use_tls", True)
                )

                success = notifier.send(
                    to_email=notification_data.email_config.get("to_email"),
                    subject=notification_data.subject,
                    content=notification_data.content,
                    html=notification_data.email_config.get("html", False)
                )

            elif notification_data.channel == "slack":
                # 发送Slack消息
                if not notification_data.slack_config:
                    raise ValueError("Slack配置不能为空")

                notifier = SlackNotifier(
                    webhook_url=notification_data.slack_config.get("webhook_url")
                )

                success = notifier.send(
                    text=notification_data.content,
                    blocks=notification_data.slack_config.get("blocks"),
                    attachments=notification_data.slack_config.get("attachments")
                )

            else:
                raise ValueError(f"不支持的通知渠道: {notification_data.channel}")

        except Exception as e:
            success = False
            error_message = str(e)

        # 更新发送状态
        if success:
            history_repo.update_status(history.id, NotificationStatus.SENT)
        else:
            history_repo.update_status(
                history.id,
                NotificationStatus.FAILED,
                error_message=error_message
            )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"通知发送失败: {error_message}"
            )

        return MessageResponse(message="通知发送成功")


@router.get("/configs", response_model=List[NotificationConfigResponse])
def list_notification_configs(
    organization_id: Optional[int] = Query(None, description="组织ID"),
    notification_type: Optional[str] = Query(None, description="通知类型"),
    channel: Optional[str] = Query(None, description="通知渠道"),
    enabled_only: bool = Query(True, description="只返回启用的配置"),
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取通知配置列表

    返回当前用户的通知配置。
    """
    with db.get_session() as session:
        config_repo = NotificationConfigRepository(session)

        # 转换枚举
        notification_type_enum = None
        if notification_type:
            try:
                notification_type_enum = NotificationType[notification_type.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的通知类型: {notification_type}"
                )

        channel_enum = None
        if channel:
            try:
                channel_enum = NotificationChannel[channel.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的通知渠道: {channel}"
                )

        configs = config_repo.get_user_configs(
            user_id=current_user.id,
            organization_id=organization_id,
            notification_type=notification_type_enum,
            channel=channel_enum,
            enabled_only=enabled_only
        )

        return [
            NotificationConfigResponse(
                id=config.id,
                user_id=config.user_id,
                organization_id=config.organization_id,
                notification_type=config.notification_type.value,
                channel=config.channel.value,
                is_enabled=config.is_enabled,
                config=config.config,
                created_at=config.created_at,
                updated_at=config.updated_at
            )
            for config in configs
        ]


@router.post("/configs", response_model=NotificationConfigResponse, status_code=status.HTTP_201_CREATED)
def create_notification_config(
    config_data: NotificationConfigCreate,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    创建通知配置

    配置用户的通知偏好。
    """
    with db.get_session() as session:
        config_repo = NotificationConfigRepository(session)

        # 转换枚举
        try:
            notification_type_enum = NotificationType[config_data.notification_type.upper()]
            channel_enum = NotificationChannel[config_data.channel.upper()]
        except KeyError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的枚举值: {str(e)}"
            )

        config = config_repo.create_config(
            user_id=current_user.id,
            organization_id=config_data.organization_id,
            notification_type=notification_type_enum,
            channel=channel_enum,
            is_enabled=config_data.is_enabled,
            config=config_data.config
        )

        return NotificationConfigResponse(
            id=config.id,
            user_id=config.user_id,
            organization_id=config.organization_id,
            notification_type=config.notification_type.value,
            channel=config.channel.value,
            is_enabled=config.is_enabled,
            config=config.config,
            created_at=config.created_at,
            updated_at=config.updated_at
        )


@router.put("/configs/{config_id}", response_model=NotificationConfigResponse)
def update_notification_config(
    config_id: int,
    config_data: NotificationConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    更新通知配置

    只能更新自己的配置。
    """
    with db.get_session() as session:
        config_repo = NotificationConfigRepository(session)

        # 检查配置是否存在且属于当前用户
        existing_config = config_repo.get_config(config_id)
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="通知配置不存在"
            )

        if existing_config.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权修改此配置"
            )

        config = config_repo.update_config(
            config_id=config_id,
            is_enabled=config_data.is_enabled,
            config=config_data.config
        )

        return NotificationConfigResponse(
            id=config.id,
            user_id=config.user_id,
            organization_id=config.organization_id,
            notification_type=config.notification_type.value,
            channel=config.channel.value,
            is_enabled=config.is_enabled,
            config=config.config,
            created_at=config.created_at,
            updated_at=config.updated_at
        )


@router.delete("/configs/{config_id}", response_model=MessageResponse)
def delete_notification_config(
    config_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    删除通知配置

    只能删除自己的配置。
    """
    with db.get_session() as session:
        config_repo = NotificationConfigRepository(session)

        # 检查配置是否存在且属于当前用户
        existing_config = config_repo.get_config(config_id)
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="通知配置不存在"
            )

        if existing_config.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此配置"
            )

        success = config_repo.delete_config(config_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除失败"
            )

        return MessageResponse(message="通知配置已删除")


@router.get("/history", response_model=List[NotificationHistoryResponse])
def list_notification_history(
    organization_id: Optional[int] = Query(None, description="组织ID"),
    notification_type: Optional[str] = Query(None, description="通知类型"),
    channel: Optional[str] = Query(None, description="通知渠道"),
    status_filter: Optional[str] = Query(None, alias="status", description="发送状态"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取通知历史

    返回当前用户的通知历史记录。
    """
    with db.get_session() as session:
        history_repo = NotificationHistoryRepository(session)

        # 转换枚举
        notification_type_enum = None
        if notification_type:
            try:
                notification_type_enum = NotificationType[notification_type.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的通知类型: {notification_type}"
                )

        channel_enum = None
        if channel:
            try:
                channel_enum = NotificationChannel[channel.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的通知渠道: {channel}"
                )

        status_enum = None
        if status_filter:
            try:
                status_enum = NotificationStatus[status_filter.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的状态: {status_filter}"
                )

        history_list = history_repo.list_history(
            user_id=current_user.id,
            organization_id=organization_id,
            notification_type=notification_type_enum,
            channel=channel_enum,
            status=status_enum,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )

        return [
            NotificationHistoryResponse(
                id=history.id,
                user_id=history.user_id,
                organization_id=history.organization_id,
                notification_type=history.notification_type.value,
                channel=history.channel.value,
                subject=history.subject,
                content=history.content,
                status=history.status.value,
                sent_at=history.sent_at,
                error_message=history.error_message,
                metadata=history.extra_data,
                created_at=history.created_at
            )
            for history in history_list
        ]


@router.get("/stats", response_model=NotificationStatsResponse)
def get_notification_stats(
    organization_id: Optional[int] = Query(None, description="组织ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取通知统计

    返回当前用户的通知统计信息。
    """
    with db.get_session() as session:
        history_repo = NotificationHistoryRepository(session)

        stats = history_repo.get_stats(
            user_id=current_user.id,
            organization_id=organization_id,
            start_time=start_time,
            end_time=end_time
        )

        return NotificationStatsResponse(**stats)
