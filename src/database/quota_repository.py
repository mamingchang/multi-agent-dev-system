"""
配额管理仓储层

提供配额使用、限流配置、告警的数据访问接口。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from .models import (
    QuotaUsage, RateLimitConfig, QuotaAlert,
    QuotaAlertLevel, RateLimitPeriod, Organization
)


class QuotaUsageRepository:
    """配额使用仓储"""

    def __init__(self, session: Session):
        self.session = session

    def record_usage(
        self,
        organization_id: int,
        tokens_used: int = 0,
        api_calls: int = 1,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[int] = None,
        period: str = "monthly"
    ) -> QuotaUsage:
        """
        记录配额使用

        Args:
            organization_id: 组织ID
            tokens_used: 使用的Token数
            api_calls: API调用次数
            resource_type: 资源类型
            resource_id: 资源ID
            user_id: 用户ID
            period: 统计周期

        Returns:
            QuotaUsage: 使用记录
        """
        usage = QuotaUsage(
            organization_id=organization_id,
            tokens_used=tokens_used,
            api_calls=api_calls,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            period=period
        )

        self.session.add(usage)
        self.session.flush()

        # 更新组织的token_used
        org = self.session.query(Organization).filter(
            Organization.id == organization_id
        ).first()
        if org:
            org.token_used += tokens_used
            self.session.flush()

        return usage

    def get_usage_stats(
        self,
        organization_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        period: str = "monthly"
    ) -> Dict[str, Any]:
        """
        获取使用统计

        Args:
            organization_id: 组织ID
            start_time: 开始时间
            end_time: 结束时间
            period: 统计周期

        Returns:
            dict: 统计信息
        """
        query = self.session.query(
            func.sum(QuotaUsage.tokens_used).label('total_tokens'),
            func.sum(QuotaUsage.api_calls).label('total_calls'),
            func.count(QuotaUsage.id).label('record_count')
        ).filter(
            QuotaUsage.organization_id == organization_id,
            QuotaUsage.period == period
        )

        if start_time:
            query = query.filter(QuotaUsage.created_at >= start_time)
        if end_time:
            query = query.filter(QuotaUsage.created_at <= end_time)

        result = query.first()

        return {
            'total_tokens': result.total_tokens or 0,
            'total_calls': result.total_calls or 0,
            'record_count': result.record_count or 0
        }

    def get_daily_usage(
        self,
        organization_id: int,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取每日使用量

        Args:
            organization_id: 组织ID
            days: 天数

        Returns:
            List[dict]: 每日使用量列表
        """
        start_time = datetime.utcnow() - timedelta(days=days)

        results = self.session.query(
            func.date(QuotaUsage.created_at).label('date'),
            func.sum(QuotaUsage.tokens_used).label('tokens'),
            func.sum(QuotaUsage.api_calls).label('calls')
        ).filter(
            QuotaUsage.organization_id == organization_id,
            QuotaUsage.created_at >= start_time
        ).group_by(
            func.date(QuotaUsage.created_at)
        ).order_by(
            func.date(QuotaUsage.created_at)
        ).all()

        return [
            {
                'date': str(r.date),
                'tokens': r.tokens or 0,
                'calls': r.calls or 0
            }
            for r in results
        ]

    def get_user_usage(
        self,
        organization_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        获取用户使用统计

        Args:
            organization_id: 组织ID
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            List[dict]: 用户使用统计
        """
        query = self.session.query(
            QuotaUsage.user_id,
            func.sum(QuotaUsage.tokens_used).label('tokens'),
            func.sum(QuotaUsage.api_calls).label('calls')
        ).filter(
            QuotaUsage.organization_id == organization_id,
            QuotaUsage.user_id.isnot(None)
        )

        if start_time:
            query = query.filter(QuotaUsage.created_at >= start_time)
        if end_time:
            query = query.filter(QuotaUsage.created_at <= end_time)

        results = query.group_by(QuotaUsage.user_id).all()

        return [
            {
                'user_id': r.user_id,
                'tokens': r.tokens or 0,
                'calls': r.calls or 0
            }
            for r in results
        ]


class RateLimitRepository:
    """限流配置仓储"""

    def __init__(self, session: Session):
        self.session = session

    def create_config(
        self,
        max_requests: int,
        period: RateLimitPeriod,
        organization_id: Optional[int] = None,
        user_id: Optional[int] = None,
        endpoint: Optional[str] = None
    ) -> RateLimitConfig:
        """
        创建限流配置

        Args:
            max_requests: 最大请求数
            period: 时间周期
            organization_id: 组织ID
            user_id: 用户ID
            endpoint: API端点

        Returns:
            RateLimitConfig: 限流配置
        """
        config = RateLimitConfig(
            max_requests=max_requests,
            period=period,
            organization_id=organization_id,
            user_id=user_id,
            endpoint=endpoint
        )

        self.session.add(config)
        self.session.flush()

        return config

    def get_config(
        self,
        organization_id: Optional[int] = None,
        user_id: Optional[int] = None,
        endpoint: Optional[str] = None
    ) -> Optional[RateLimitConfig]:
        """
        获取限流配置

        Args:
            organization_id: 组织ID
            user_id: 用户ID
            endpoint: API端点

        Returns:
            RateLimitConfig: 限流配置
        """
        query = self.session.query(RateLimitConfig).filter(
            RateLimitConfig.is_active == True
        )

        if organization_id is not None:
            query = query.filter(RateLimitConfig.organization_id == organization_id)
        if user_id is not None:
            query = query.filter(RateLimitConfig.user_id == user_id)
        if endpoint is not None:
            query = query.filter(RateLimitConfig.endpoint == endpoint)

        return query.first()

    def list_configs(
        self,
        organization_id: Optional[int] = None,
        active_only: bool = True
    ) -> List[RateLimitConfig]:
        """
        列出限流配置

        Args:
            organization_id: 组织ID
            active_only: 只返回激活的配置

        Returns:
            List[RateLimitConfig]: 配置列表
        """
        query = self.session.query(RateLimitConfig)

        if organization_id is not None:
            query = query.filter(RateLimitConfig.organization_id == organization_id)
        if active_only:
            query = query.filter(RateLimitConfig.is_active == True)

        return query.all()

    def update_config(
        self,
        config_id: int,
        max_requests: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> Optional[RateLimitConfig]:
        """
        更新限流配置

        Args:
            config_id: 配置ID
            max_requests: 最大请求数
            is_active: 是否激活

        Returns:
            RateLimitConfig: 更新后的配置
        """
        config = self.session.query(RateLimitConfig).filter(
            RateLimitConfig.id == config_id
        ).first()

        if not config:
            return None

        if max_requests is not None:
            config.max_requests = max_requests
        if is_active is not None:
            config.is_active = is_active

        self.session.flush()

        return config

    def delete_config(self, config_id: int) -> bool:
        """
        删除限流配置

        Args:
            config_id: 配置ID

        Returns:
            bool: 是否成功删除
        """
        config = self.session.query(RateLimitConfig).filter(
            RateLimitConfig.id == config_id
        ).first()

        if not config:
            return False

        self.session.delete(config)
        self.session.flush()

        return True


class QuotaAlertRepository:
    """配额告警仓储"""

    def __init__(self, session: Session):
        self.session = session

    def create_alert(
        self,
        organization_id: int,
        alert_level: QuotaAlertLevel,
        usage_percentage: int,
        tokens_used: int,
        tokens_quota: int,
        message: str
    ) -> QuotaAlert:
        """
        创建配额告警

        Args:
            organization_id: 组织ID
            alert_level: 告警级别
            usage_percentage: 使用百分比
            tokens_used: 已使用Token
            tokens_quota: Token配额
            message: 告警消息

        Returns:
            QuotaAlert: 告警记录
        """
        alert = QuotaAlert(
            organization_id=organization_id,
            alert_level=alert_level,
            usage_percentage=usage_percentage,
            tokens_used=tokens_used,
            tokens_quota=tokens_quota,
            message=message
        )

        self.session.add(alert)
        self.session.flush()

        return alert

    def get_unresolved_alerts(
        self,
        organization_id: Optional[int] = None
    ) -> List[QuotaAlert]:
        """
        获取未解决的告警

        Args:
            organization_id: 组织ID

        Returns:
            List[QuotaAlert]: 告警列表
        """
        query = self.session.query(QuotaAlert).filter(
            QuotaAlert.is_resolved == False
        )

        if organization_id is not None:
            query = query.filter(QuotaAlert.organization_id == organization_id)

        return query.order_by(QuotaAlert.created_at.desc()).all()

    def resolve_alert(self, alert_id: int) -> Optional[QuotaAlert]:
        """
        解决告警

        Args:
            alert_id: 告警ID

        Returns:
            QuotaAlert: 更新后的告警
        """
        alert = self.session.query(QuotaAlert).filter(
            QuotaAlert.id == alert_id
        ).first()

        if not alert:
            return None

        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        self.session.flush()

        return alert

    def list_alerts(
        self,
        organization_id: Optional[int] = None,
        alert_level: Optional[QuotaAlertLevel] = None,
        resolved: Optional[bool] = None,
        limit: int = 100
    ) -> List[QuotaAlert]:
        """
        列出告警

        Args:
            organization_id: 组织ID
            alert_level: 告警级别
            resolved: 是否已解决
            limit: 返回数量

        Returns:
            List[QuotaAlert]: 告警列表
        """
        query = self.session.query(QuotaAlert)

        if organization_id is not None:
            query = query.filter(QuotaAlert.organization_id == organization_id)
        if alert_level is not None:
            query = query.filter(QuotaAlert.alert_level == alert_level)
        if resolved is not None:
            query = query.filter(QuotaAlert.is_resolved == resolved)

        return query.order_by(QuotaAlert.created_at.desc()).limit(limit).all()
