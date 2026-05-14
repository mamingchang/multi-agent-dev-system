"""
审计日志仓储层

提供审计日志的数据访问接口。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from .models import AuditLog, AuditAction


class AuditLogRepository:
    """审计日志仓储"""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        organization_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> AuditLog:
        """
        创建审计日志

        Args:
            action: 操作类型
            resource_type: 资源类型（organization, project, task等）
            resource_id: 资源ID
            user_id: 用户ID
            username: 用户名（冗余存储）
            organization_id: 组织ID（用于多租户隔离）
            ip_address: IP地址
            user_agent: User-Agent
            details: 操作详情（JSON）
            status: 状态（success, failed, error）
            error_message: 错误信息

        Returns:
            AuditLog: 创建的审计日志
        """
        log = AuditLog(
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            user_id=user_id,
            username=username,
            organization_id=organization_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            status=status,
            error_message=error_message
        )

        self.session.add(log)
        self.session.flush()

        return log

    def get_by_id(self, log_id: int) -> Optional[AuditLog]:
        """根据ID获取审计日志"""
        return self.session.query(AuditLog).filter(AuditLog.id == log_id).first()

    def list_logs(
        self,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        查询审计日志

        Args:
            user_id: 用户ID过滤
            organization_id: 组织ID过滤
            resource_type: 资源类型过滤
            resource_id: 资源ID过滤
            action: 操作类型过滤
            status: 状态过滤
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[AuditLog]: 审计日志列表
        """
        query = self.session.query(AuditLog)

        # 应用过滤条件
        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)

        if organization_id is not None:
            query = query.filter(AuditLog.organization_id == organization_id)

        if resource_type is not None:
            query = query.filter(AuditLog.resource_type == resource_type)

        if resource_id is not None:
            query = query.filter(AuditLog.resource_id == str(resource_id))

        if action is not None:
            query = query.filter(AuditLog.action == action)

        if status is not None:
            query = query.filter(AuditLog.status == status)

        if start_time is not None:
            query = query.filter(AuditLog.created_at >= start_time)

        if end_time is not None:
            query = query.filter(AuditLog.created_at <= end_time)

        # 按时间倒序排列
        query = query.order_by(AuditLog.created_at.desc())

        # 分页
        query = query.limit(limit).offset(offset)

        return query.all()

    def count_logs(
        self,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """
        统计审计日志数量

        Args:
            user_id: 用户ID过滤
            organization_id: 组织ID过滤
            resource_type: 资源类型过滤
            action: 操作类型过滤
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            int: 日志数量
        """
        query = self.session.query(AuditLog)

        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)

        if organization_id is not None:
            query = query.filter(AuditLog.organization_id == organization_id)

        if resource_type is not None:
            query = query.filter(AuditLog.resource_type == resource_type)

        if action is not None:
            query = query.filter(AuditLog.action == action)

        if start_time is not None:
            query = query.filter(AuditLog.created_at >= start_time)

        if end_time is not None:
            query = query.filter(AuditLog.created_at <= end_time)

        return query.count()

    def get_user_activity(
        self,
        user_id: int,
        days: int = 30
    ) -> List[AuditLog]:
        """
        获取用户最近的活动记录

        Args:
            user_id: 用户ID
            days: 最近天数

        Returns:
            List[AuditLog]: 活动记录列表
        """
        start_time = datetime.utcnow() - timedelta(days=days)

        return self.list_logs(
            user_id=user_id,
            start_time=start_time,
            limit=1000
        )

    def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        获取资源的操作历史

        Args:
            resource_type: 资源类型
            resource_id: 资源ID
            limit: 返回数量限制

        Returns:
            List[AuditLog]: 操作历史列表
        """
        return self.list_logs(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit
        )

    def delete_old_logs(self, days: int = 90) -> int:
        """
        删除旧的审计日志（用于定期清理）

        Args:
            days: 保留天数

        Returns:
            int: 删除的日志数量
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        deleted = self.session.query(AuditLog).filter(
            AuditLog.created_at < cutoff_time
        ).delete()

        self.session.flush()

        return deleted
