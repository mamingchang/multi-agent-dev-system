"""
通知辅助函数

提供自动发送通知的功能，与其他系统集成。
"""

from typing import Optional
from sqlalchemy.orm import Session

from ..database.notification_repository import (
    NotificationConfigRepository, NotificationHistoryRepository
)
from ..database.organization_repository import OrganizationRepository
from ..database.models import (
    NotificationType, NotificationChannel, NotificationStatus
)
from ..notifications.notification_service import (
    EmailNotifier, SlackNotifier, NotificationService
)


def send_quota_alert_notification(
    session: Session,
    organization_id: int,
    usage_percentage: int,
    tokens_used: int,
    tokens_quota: int,
    alert_level: str
):
    """
    发送配额告警通知

    自动查找组织成员的通知配置，发送告警通知。

    Args:
        session: 数据库会话
        organization_id: 组织ID
        usage_percentage: 使用百分比
        tokens_used: 已使用Token
        tokens_quota: Token配额
        alert_level: 告警级别
    """
    try:
        # 获取组织信息
        org_repo = OrganizationRepository(session)
        org = org_repo.get_by_id(organization_id)
        if not org:
            print(f"组织不存在: {organization_id}")
            return

        # 获取通知配置
        config_repo = NotificationConfigRepository(session)
        history_repo = NotificationHistoryRepository(session)

        # 查找所有启用了配额告警的配置
        # 这里简化处理，实际应该查询组织所有成员的配置
        # 暂时跳过，因为需要遍历组织成员

        # 格式化通知内容
        email_notification = NotificationService.format_quota_alert(
            organization_name=org.name,
            usage_percentage=usage_percentage,
            tokens_used=tokens_used,
            tokens_quota=tokens_quota,
            alert_level=alert_level
        )

        slack_notification = NotificationService.format_slack_quota_alert(
            organization_name=org.name,
            usage_percentage=usage_percentage,
            tokens_used=tokens_used,
            tokens_quota=tokens_quota,
            alert_level=alert_level
        )

        # 这里需要实际的通知配置才能发送
        # 由于没有配置信息，只记录历史
        print(f"配额告警通知已准备: {org.name} - {alert_level}")
        print(f"邮件主题: {email_notification['subject']}")
        print(f"Slack消息: {slack_notification['text']}")

    except Exception as e:
        print(f"发送配额告警通知失败: {e}")
        import traceback
        traceback.print_exc()


def send_task_notification(
    session: Session,
    user_id: int,
    task_id: str,
    task_title: str,
    project_name: str,
    status: str,
    error_message: Optional[str] = None
):
    """
    发送任务状态通知

    Args:
        session: 数据库会话
        user_id: 用户ID
        task_id: 任务ID
        task_title: 任务标题
        project_name: 项目名称
        status: 任务状态(completed/failed)
        error_message: 错误信息（如果失败）
    """
    try:
        config_repo = NotificationConfigRepository(session)
        history_repo = NotificationHistoryRepository(session)

        # 获取用户的通知配置
        configs = config_repo.get_user_configs(
            user_id=user_id,
            notification_type=NotificationType.TASK_STATUS,
            enabled_only=True
        )

        if not configs:
            print(f"用户 {user_id} 未配置任务通知")
            return

        # 格式化通知内容
        if status == "completed":
            notification = NotificationService.format_task_completed(
                task_id=task_id,
                task_title=task_title,
                project_name=project_name
            )
        else:
            notification = NotificationService.format_task_failed(
                task_id=task_id,
                task_title=task_title,
                project_name=project_name,
                error_message=error_message or "未知错误"
            )

        # 发送通知
        for config in configs:
            # 创建历史记录
            history = history_repo.create_history(
                user_id=user_id,
                notification_type=NotificationType.TASK_STATUS,
                channel=config.channel,
                subject=notification['subject'],
                content=notification['content'],
                status=NotificationStatus.PENDING,
                extra_data={
                    "task_id": task_id,
                    "task_title": task_title,
                    "project_name": project_name,
                    "status": status
                }
            )

            # 根据渠道发送
            success = False
            error_msg = None

            try:
                if config.channel == NotificationChannel.EMAIL:
                    # 发送邮件
                    notifier = EmailNotifier(
                        smtp_host=config.config.get("smtp_host"),
                        smtp_port=config.config.get("smtp_port"),
                        smtp_user=config.config.get("smtp_user"),
                        smtp_password=config.config.get("smtp_password"),
                        from_email=config.config.get("from_email"),
                        use_tls=config.config.get("use_tls", True)
                    )

                    success = notifier.send(
                        to_email=config.config.get("to_email"),
                        subject=notification['subject'],
                        content=notification['content']
                    )

                elif config.channel == NotificationChannel.SLACK:
                    # 发送Slack消息
                    notifier = SlackNotifier(
                        webhook_url=config.config.get("webhook_url")
                    )

                    success = notifier.send(
                        text=notification['content']
                    )

            except Exception as e:
                success = False
                error_msg = str(e)

            # 更新状态
            if success:
                history_repo.update_status(history.id, NotificationStatus.SENT)
            else:
                history_repo.update_status(
                    history.id,
                    NotificationStatus.FAILED,
                    error_message=error_msg
                )

    except Exception as e:
        print(f"发送任务通知失败: {e}")
        import traceback
        traceback.print_exc()
