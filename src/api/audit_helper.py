"""
审计日志辅助函数

提供便捷的审计日志记录功能。
"""

from typing import Optional, Dict, Any
from fastapi import Request
from sqlalchemy.orm import Session

from ..database.audit_repository import AuditLogRepository
from ..database.models import AuditAction, User


def log_audit(
    session: Session,
    action: AuditAction,
    resource_type: str,
    resource_id: str,
    user: Optional[User] = None,
    organization_id: Optional[int] = None,
    request: Optional[Request] = None,
    details: Optional[Dict[str, Any]] = None,
    status: str = "success",
    error_message: Optional[str] = None
):
    """
    记录审计日志

    Args:
        session: 数据库session
        action: 操作类型
        resource_type: 资源类型
        resource_id: 资源ID
        user: 用户对象
        organization_id: 组织ID
        request: FastAPI请求对象（用于提取IP和User-Agent）
        details: 操作详情
        status: 状态
        error_message: 错误信息
    """
    try:
        # 提取用户信息
        user_id = user.id if user else None
        username = user.username if user else None

        # 提取请求信息
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

        # 记录日志
        audit_repo = AuditLogRepository(session)
        audit_repo.create(
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
    except Exception as e:
        # 审计日志记录失败不应该影响正常业务
        print(f"审计日志记录失败: {e}")
        import traceback
        traceback.print_exc()
