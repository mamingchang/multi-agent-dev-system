"""
配额管理辅助函数

提供配额检查、使用记录、告警等功能。
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..database.quota_repository import (
    QuotaUsageRepository, QuotaAlertRepository
)
from ..database.organization_repository import OrganizationRepository
from ..database.models import QuotaAlertLevel
from .notification_helper import send_quota_alert_notification


def check_quota(
    session: Session,
    organization_id: int,
    tokens_needed: int = 0
) -> bool:
    """
    检查配额是否足够

    Args:
        session: 数据库session
        organization_id: 组织ID
        tokens_needed: 需要的Token数

    Returns:
        bool: 是否有足够配额

    Raises:
        HTTPException: 如果配额不足
    """
    org_repo = OrganizationRepository(session)
    org = org_repo.get_by_id(organization_id)

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="组织不存在"
        )

    # 检查配额
    remaining = org.token_quota - org.token_used

    if tokens_needed > remaining:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Token配额不足。剩余: {remaining}, 需要: {tokens_needed}"
        )

    return True


def record_quota_usage(
    session: Session,
    organization_id: int,
    tokens_used: int = 0,
    api_calls: int = 1,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    user_id: Optional[int] = None
):
    """
    记录配额使用

    Args:
        session: 数据库session
        organization_id: 组织ID
        tokens_used: 使用的Token数
        api_calls: API调用次数
        resource_type: 资源类型
        resource_id: 资源ID
        user_id: 用户ID
    """
    try:
        usage_repo = QuotaUsageRepository(session)
        usage_repo.record_usage(
            organization_id=organization_id,
            tokens_used=tokens_used,
            api_calls=api_calls,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id
        )

        # 检查是否需要发送告警
        check_and_create_alert(session, organization_id)

    except Exception as e:
        print(f"记录配额使用失败: {e}")
        import traceback
        traceback.print_exc()


def check_and_create_alert(
    session: Session,
    organization_id: int
):
    """
    检查配额使用情况并创建告警

    Args:
        session: 数据库session
        organization_id: 组织ID
    """
    try:
        org_repo = OrganizationRepository(session)
        org = org_repo.get_by_id(organization_id)

        if not org or org.token_quota == 0:
            return

        # 计算使用百分比
        usage_percentage = int((org.token_used / org.token_quota) * 100)

        # 确定告警级别
        alert_level = None
        if usage_percentage >= 100:
            alert_level = QuotaAlertLevel.EXCEEDED
        elif usage_percentage >= 90:
            alert_level = QuotaAlertLevel.CRITICAL
        elif usage_percentage >= 80:
            alert_level = QuotaAlertLevel.WARNING

        if not alert_level:
            return

        # 检查是否已有相同级别的未解决告警
        alert_repo = QuotaAlertRepository(session)
        existing_alerts = alert_repo.get_unresolved_alerts(organization_id)

        for alert in existing_alerts:
            if alert.alert_level == alert_level:
                # 已有相同级别的告警，不重复创建
                return

        # 创建告警
        message = f"组织 {org.name} 的Token使用量已达 {usage_percentage}%"
        if alert_level == QuotaAlertLevel.EXCEEDED:
            message += "，已超过配额限制！"
        elif alert_level == QuotaAlertLevel.CRITICAL:
            message += "，即将超过配额限制！"
        else:
            message += "，请注意配额使用情况。"

        alert_repo.create_alert(
            organization_id=organization_id,
            alert_level=alert_level,
            usage_percentage=usage_percentage,
            tokens_used=org.token_used,
            tokens_quota=org.token_quota,
            message=message
        )

        print(f"创建配额告警: {message}")

        # 发送通知
        send_quota_alert_notification(
            session=session,
            organization_id=organization_id,
            usage_percentage=usage_percentage,
            tokens_used=org.token_used,
            tokens_quota=org.token_quota,
            alert_level=alert_level.value
        )

    except Exception as e:
        print(f"检查配额告警失败: {e}")
        import traceback
        traceback.print_exc()


def get_quota_info(
    session: Session,
    organization_id: int
) -> dict:
    """
    获取配额信息

    Args:
        session: 数据库session
        organization_id: 组织ID

    Returns:
        dict: 配额信息
    """
    org_repo = OrganizationRepository(session)
    org = org_repo.get_by_id(organization_id)

    if not org:
        return None

    remaining = org.token_quota - org.token_used
    usage_percentage = (org.token_used / org.token_quota * 100) if org.token_quota > 0 else 0

    return {
        'token_quota': org.token_quota,
        'token_used': org.token_used,
        'token_remaining': remaining,
        'usage_percentage': round(usage_percentage, 2),
        'is_exceeded': org.token_used >= org.token_quota
    }
