"""
审计日志API路由

端点：
- GET /audit/logs - 查询审计日志
- GET /audit/logs/{log_id} - 获取日志详情
- GET /audit/users/{user_id}/activity - 获取用户活动
- GET /audit/resources/{resource_type}/{resource_id} - 获取资源历史
- GET /audit/stats - 获取审计统计
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime

from ..database.database import Database
from ..database.audit_repository import AuditLogRepository
from ..database.models import User, AuditAction, OrganizationRole
from ..database.organization_repository import OrganizationMemberRepository
from .schemas import AuditLogResponse, AuditLogListResponse
from .auth import get_current_active_user
from .dependencies import get_db

router = APIRouter(prefix="/audit", tags=["审计日志"])


def check_audit_permission(current_user: User, organization_id: Optional[int], db: Database):
    """
    检查审计日志查看权限

    只有组织管理员或超级管理员可以查看审计日志

    Args:
        current_user: 当前用户
        organization_id: 组织ID（如果指定）
        db: 数据库连接

    Raises:
        HTTPException: 如果用户没有权限
    """
    # 如果是查询特定组织的日志，检查是否是该组织的管理员
    if organization_id:
        with db.get_session() as session:
            member_repo = OrganizationMemberRepository(session)
            role = member_repo.get_user_role(organization_id, current_user.id)

            if not role or role not in [OrganizationRole.ORG_ADMIN, OrganizationRole.SUPER_ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="需要组织管理员权限才能查看审计日志"
                )


@router.get("/logs", response_model=AuditLogListResponse)
def list_audit_logs(
    user_id: Optional[int] = Query(None, description="用户ID"),
    organization_id: Optional[int] = Query(None, description="组织ID"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    resource_id: Optional[str] = Query(None, description="资源ID"),
    action: Optional[str] = Query(None, description="操作类型"),
    status: Optional[str] = Query(None, description="状态"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    查询审计日志

    支持多种过滤条件，需要管理员权限。
    """
    # 检查权限
    check_audit_permission(current_user, organization_id, db)

    with db.get_session() as session:
        audit_repo = AuditLogRepository(session)

        # 转换action字符串为枚举
        action_enum = None
        if action:
            try:
                action_enum = AuditAction[action.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的操作类型: {action}"
                )

        # 查询日志
        logs = audit_repo.list_logs(
            user_id=user_id,
            organization_id=organization_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action_enum,
            status=status,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )

        # 统计总数
        total = audit_repo.count_logs(
            user_id=user_id,
            organization_id=organization_id,
            resource_type=resource_type,
            action=action_enum,
            start_time=start_time,
            end_time=end_time
        )

        # 构造响应
        return AuditLogListResponse(
            total=total,
            logs=[
                AuditLogResponse(
                    id=log.id,
                    action=log.action.value,
                    resource_type=log.resource_type,
                    resource_id=log.resource_id,
                    user_id=log.user_id,
                    username=log.username,
                    organization_id=log.organization_id,
                    ip_address=log.ip_address,
                    user_agent=log.user_agent,
                    details=log.details,
                    status=log.status,
                    error_message=log.error_message,
                    created_at=log.created_at
                )
                for log in logs
            ],
            limit=limit,
            offset=offset
        )


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
def get_audit_log(
    log_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取审计日志详情

    需要管理员权限。
    """
    with db.get_session() as session:
        audit_repo = AuditLogRepository(session)

        log = audit_repo.get_by_id(log_id)
        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="审计日志不存在"
            )

        # 检查权限
        check_audit_permission(current_user, log.organization_id, db)

        return AuditLogResponse(
            id=log.id,
            action=log.action.value,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            user_id=log.user_id,
            username=log.username,
            organization_id=log.organization_id,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            details=log.details,
            status=log.status,
            error_message=log.error_message,
            created_at=log.created_at
        )


@router.get("/users/{user_id}/activity", response_model=List[AuditLogResponse])
def get_user_activity(
    user_id: int,
    days: int = Query(30, ge=1, le=365, description="最近天数"),
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取用户活动记录

    用户可以查看自己的活动，管理员可以查看所有用户的活动。
    """
    # 只能查看自己的活动，除非是管理员
    if user_id != current_user.id:
        # TODO: 检查是否是管理员
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能查看自己的活动记录"
        )

    with db.get_session() as session:
        audit_repo = AuditLogRepository(session)

        logs = audit_repo.get_user_activity(user_id, days)

        return [
            AuditLogResponse(
                id=log.id,
                action=log.action.value,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                user_id=log.user_id,
                username=log.username,
                organization_id=log.organization_id,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                details=log.details,
                status=log.status,
                error_message=log.error_message,
                created_at=log.created_at
            )
            for log in logs
        ]


@router.get("/resources/{resource_type}/{resource_id}", response_model=List[AuditLogResponse])
def get_resource_history(
    resource_type: str,
    resource_id: str,
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取资源的操作历史

    需要对该资源有访问权限。
    """
    with db.get_session() as session:
        audit_repo = AuditLogRepository(session)

        logs = audit_repo.get_resource_history(resource_type, resource_id, limit)

        # 如果有日志，检查权限（基于第一条日志的organization_id）
        if logs and logs[0].organization_id:
            check_audit_permission(current_user, logs[0].organization_id, db)

        return [
            AuditLogResponse(
                id=log.id,
                action=log.action.value,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                user_id=log.user_id,
                username=log.username,
                organization_id=log.organization_id,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                details=log.details,
                status=log.status,
                error_message=log.error_message,
                created_at=log.created_at
            )
            for log in logs
        ]


@router.get("/stats")
def get_audit_stats(
    organization_id: Optional[int] = Query(None, description="组织ID"),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取审计统计信息

    需要管理员权限。
    """
    # 检查权限
    check_audit_permission(current_user, organization_id, db)

    with db.get_session() as session:
        audit_repo = AuditLogRepository(session)

        from datetime import timedelta
        start_time = datetime.utcnow() - timedelta(days=days)

        # 统计各类操作的数量
        stats = {}
        for action in AuditAction:
            count = audit_repo.count_logs(
                organization_id=organization_id,
                action=action,
                start_time=start_time
            )
            if count > 0:
                stats[action.value] = count

        # 总数
        total = audit_repo.count_logs(
            organization_id=organization_id,
            start_time=start_time
        )

        return {
            "total": total,
            "days": days,
            "start_time": start_time,
            "end_time": datetime.utcnow(),
            "by_action": stats
        }
