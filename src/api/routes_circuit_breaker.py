"""
熔断器管理API路由

端点：
- GET /circuit-breaker/status - 获取所有熔断器状态
- GET /circuit-breaker/{organization_id}/status - 获取指定组织的熔断器状态
- POST /circuit-breaker/{organization_id}/reset - 重置指定组织的熔断器
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from ..database.models import User
from ..database.organization_repository import OrganizationMemberRepository
from ..utils.circuit_breaker import circuit_breaker_manager
from .schemas import MessageResponse
from .auth import get_current_active_user
from .dependencies import get_db
from ..database.database import Database

router = APIRouter(prefix="/circuit-breaker", tags=["熔断器管理"])


@router.get("/status", response_model=Dict[int, Dict[str, Any]])
def get_all_circuit_breaker_status(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取所有熔断器状态

    需要SuperAdmin权限。
    """
    # TODO: 检查SuperAdmin权限
    # 这里暂时允许所有登录用户查看

    return circuit_breaker_manager.get_all_states()


@router.get("/{organization_id}/status")
def get_circuit_breaker_status(
    organization_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取指定组织的熔断器状态

    需要组织成员权限。
    """
    # 检查权限
    with db.get_session() as session:
        member_repo = OrganizationMemberRepository(session)
        if not member_repo.is_member(organization_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要组织成员权限"
            )

    breaker = circuit_breaker_manager.get_breaker(organization_id)
    return breaker.get_state()


@router.post("/{organization_id}/reset", response_model=MessageResponse)
def reset_circuit_breaker(
    organization_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    重置指定组织的熔断器

    需要组织管理员权限。
    """
    # 检查权限
    with db.get_session() as session:
        member_repo = OrganizationMemberRepository(session)
        member = member_repo.get_member(organization_id, current_user.id)

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要组织成员权限"
            )

        # 检查是否是管理员
        if member.role not in ["super_admin", "org_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要组织管理员权限"
            )

    # 重置熔断器
    circuit_breaker_manager.reset_breaker(organization_id)

    return MessageResponse(message=f"组织 {organization_id} 的熔断器已重置")
