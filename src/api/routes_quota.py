"""
配额管理API路由

端点：
- GET /quota/usage - 获取配额使用统计
- GET /quota/usage/daily - 获取每日使用量
- GET /quota/usage/users - 获取用户使用统计
- GET /quota/info - 获取配额信息
- POST /quota/rate-limits - 创建限流配置
- GET /quota/rate-limits - 获取限流配置列表
- PUT /quota/rate-limits/{config_id} - 更新限流配置
- DELETE /quota/rate-limits/{config_id} - 删除限流配置
- GET /quota/alerts - 获取配额告警列表
- POST /quota/alerts/{alert_id}/resolve - 解决告警
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, timedelta

from ..database.database import Database
from ..database.quota_repository import (
    QuotaUsageRepository, RateLimitRepository, QuotaAlertRepository
)
from ..database.models import User, RateLimitPeriod, QuotaAlertLevel
from ..database.organization_repository import OrganizationMemberRepository
from .schemas import (
    QuotaStatsResponse, QuotaDailyUsageResponse, QuotaInfoResponse,
    RateLimitConfigCreate, RateLimitConfigUpdate, RateLimitConfigResponse,
    QuotaAlertResponse, MessageResponse
)
from .auth import get_current_active_user
from .dependencies import get_db
from .quota_helper import get_quota_info

router = APIRouter(prefix="/quota", tags=["配额管理"])


def check_quota_permission(current_user: User, organization_id: int, db: Database):
    """
    检查配额管理权限

    只有组织管理员可以管理配额

    Args:
        current_user: 当前用户
        organization_id: 组织ID
        db: 数据库连接

    Raises:
        HTTPException: 如果用户没有权限
    """
    with db.get_session() as session:
        member_repo = OrganizationMemberRepository(session)
        if not member_repo.is_member(organization_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要组织成员权限"
            )


@router.get("/usage", response_model=QuotaStatsResponse)
def get_quota_usage(
    organization_id: int = Query(..., description="组织ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    period: str = Query("monthly", description="统计周期"),
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取配额使用统计

    需要组织成员权限。
    """
    # 检查权限
    check_quota_permission(current_user, organization_id, db)

    with db.get_session() as session:
        usage_repo = QuotaUsageRepository(session)

        stats = usage_repo.get_usage_stats(
            organization_id=organization_id,
            start_time=start_time,
            end_time=end_time,
            period=period
        )

        return QuotaStatsResponse(**stats)


@router.get("/usage/daily", response_model=List[QuotaDailyUsageResponse])
def get_daily_usage(
    organization_id: int = Query(..., description="组织ID"),
    days: int = Query(30, ge=1, le=365, description="天数"),
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取每日使用量

    需要组织成员权限。
    """
    # 检查权限
    check_quota_permission(current_user, organization_id, db)

    with db.get_session() as session:
        usage_repo = QuotaUsageRepository(session)

        daily_usage = usage_repo.get_daily_usage(
            organization_id=organization_id,
            days=days
        )

        return [QuotaDailyUsageResponse(**item) for item in daily_usage]


@router.get("/usage/users")
def get_user_usage(
    organization_id: int = Query(..., description="组织ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取用户使用统计

    需要组织成员权限。
    """
    # 检查权限
    check_quota_permission(current_user, organization_id, db)

    with db.get_session() as session:
        usage_repo = QuotaUsageRepository(session)

        user_usage = usage_repo.get_user_usage(
            organization_id=organization_id,
            start_time=start_time,
            end_time=end_time
        )

        return user_usage


@router.get("/info", response_model=QuotaInfoResponse)
def get_quota_information(
    organization_id: int = Query(..., description="组织ID"),
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取配额信息

    需要组织成员权限。
    """
    # 检查权限
    check_quota_permission(current_user, organization_id, db)

    with db.get_session() as session:
        quota_info = get_quota_info(session, organization_id)

        if not quota_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="组织不存在"
            )

        return QuotaInfoResponse(**quota_info)


@router.post("/rate-limits", response_model=RateLimitConfigResponse, status_code=status.HTTP_201_CREATED)
def create_rate_limit_config(
    config_data: RateLimitConfigCreate,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    创建限流配置

    需要组织管理员权限。
    """
    # 如果指定了组织，检查权限
    if config_data.organization_id:
        check_quota_permission(current_user, config_data.organization_id, db)

    with db.get_session() as session:
        rate_limit_repo = RateLimitRepository(session)

        # 转换period字符串为枚举
        try:
            period_enum = RateLimitPeriod[config_data.period.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的时间周期: {config_data.period}"
            )

        config = rate_limit_repo.create_config(
            max_requests=config_data.max_requests,
            period=period_enum,
            organization_id=config_data.organization_id,
            user_id=config_data.user_id,
            endpoint=config_data.endpoint
        )

        return RateLimitConfigResponse(
            id=config.id,
            organization_id=config.organization_id,
            user_id=config.user_id,
            endpoint=config.endpoint,
            max_requests=config.max_requests,
            period=config.period.value,
            is_active=config.is_active,
            created_at=config.created_at,
            updated_at=config.updated_at
        )


@router.get("/rate-limits", response_model=List[RateLimitConfigResponse])
def list_rate_limit_configs(
    organization_id: Optional[int] = Query(None, description="组织ID"),
    active_only: bool = Query(True, description="只返回激活的配置"),
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取限流配置列表

    需要组织成员权限。
    """
    # 如果指定了组织，检查权限
    if organization_id:
        check_quota_permission(current_user, organization_id, db)

    with db.get_session() as session:
        rate_limit_repo = RateLimitRepository(session)

        configs = rate_limit_repo.list_configs(
            organization_id=organization_id,
            active_only=active_only
        )

        return [
            RateLimitConfigResponse(
                id=config.id,
                organization_id=config.organization_id,
                user_id=config.user_id,
                endpoint=config.endpoint,
                max_requests=config.max_requests,
                period=config.period.value,
                is_active=config.is_active,
                created_at=config.created_at,
                updated_at=config.updated_at
            )
            for config in configs
        ]


@router.put("/rate-limits/{config_id}", response_model=RateLimitConfigResponse)
def update_rate_limit_config(
    config_id: int,
    config_data: RateLimitConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    更新限流配置

    需要组织管理员权限。
    """
    with db.get_session() as session:
        rate_limit_repo = RateLimitRepository(session)

        config = rate_limit_repo.update_config(
            config_id=config_id,
            max_requests=config_data.max_requests,
            is_active=config_data.is_active
        )

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="限流配置不存在"
            )

        return RateLimitConfigResponse(
            id=config.id,
            organization_id=config.organization_id,
            user_id=config.user_id,
            endpoint=config.endpoint,
            max_requests=config.max_requests,
            period=config.period.value,
            is_active=config.is_active,
            created_at=config.created_at,
            updated_at=config.updated_at
        )


@router.delete("/rate-limits/{config_id}", response_model=MessageResponse)
def delete_rate_limit_config(
    config_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    删除限流配置

    需要组织管理员权限。
    """
    with db.get_session() as session:
        rate_limit_repo = RateLimitRepository(session)

        success = rate_limit_repo.delete_config(config_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="限流配置不存在"
            )

        return MessageResponse(message="限流配置已删除")


@router.get("/alerts", response_model=List[QuotaAlertResponse])
def list_quota_alerts(
    organization_id: Optional[int] = Query(None, description="组织ID"),
    alert_level: Optional[str] = Query(None, description="告警级别"),
    resolved: Optional[bool] = Query(None, description="是否已解决"),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取配额告警列表

    需要组织成员权限。
    """
    # 如果指定了组织，检查权限
    if organization_id:
        check_quota_permission(current_user, organization_id, db)

    with db.get_session() as session:
        alert_repo = QuotaAlertRepository(session)

        # 转换alert_level字符串为枚举
        alert_level_enum = None
        if alert_level:
            try:
                alert_level_enum = QuotaAlertLevel[alert_level.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的告警级别: {alert_level}"
                )

        alerts = alert_repo.list_alerts(
            organization_id=organization_id,
            alert_level=alert_level_enum,
            resolved=resolved,
            limit=limit
        )

        return [
            QuotaAlertResponse(
                id=alert.id,
                organization_id=alert.organization_id,
                alert_level=alert.alert_level.value,
                usage_percentage=alert.usage_percentage,
                tokens_used=alert.tokens_used,
                tokens_quota=alert.tokens_quota,
                message=alert.message,
                is_resolved=alert.is_resolved,
                resolved_at=alert.resolved_at,
                created_at=alert.created_at
            )
            for alert in alerts
        ]


@router.post("/alerts/{alert_id}/resolve", response_model=QuotaAlertResponse)
def resolve_quota_alert(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    解决配额告警

    需要组织管理员权限。
    """
    with db.get_session() as session:
        alert_repo = QuotaAlertRepository(session)

        alert = alert_repo.resolve_alert(alert_id)

        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="告警不存在"
            )

        # 检查权限
        check_quota_permission(current_user, alert.organization_id, db)

        return QuotaAlertResponse(
            id=alert.id,
            organization_id=alert.organization_id,
            alert_level=alert.alert_level.value,
            usage_percentage=alert.usage_percentage,
            tokens_used=alert.tokens_used,
            tokens_quota=alert.tokens_quota,
            message=alert.message,
            is_resolved=alert.is_resolved,
            resolved_at=alert.resolved_at,
            created_at=alert.created_at
        )
