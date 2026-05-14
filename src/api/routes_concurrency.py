"""
并发控制API路由

端点：
- GET /concurrency/scheduler/stats - 获取调度器统计信息
- GET /concurrency/scheduler/organization/{organization_id} - 获取组织调度统计
- POST /concurrency/scheduler/organization/{organization_id}/limit - 设置组织并发限制
- GET /concurrency/reservations - 获取Token预留信息
- GET /concurrency/reservations/{task_id} - 获取任务的Token预留信息
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, Optional

from ..database.models import User
from ..database.organization_repository import OrganizationMemberRepository
from ..concurrency.task_scheduler import task_scheduler
from ..concurrency.token_reservation import token_reservation_manager
from .schemas import MessageResponse
from .auth import get_current_active_user
from .dependencies import get_db
from ..database.database import Database

router = APIRouter(prefix="/concurrency", tags=["并发控制"])


@router.get("/scheduler/stats")
def get_scheduler_stats(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取调度器统计信息

    需要登录。
    """
    return task_scheduler.get_all_stats()


@router.get("/scheduler/organization/{organization_id}")
def get_organization_scheduler_stats(
    organization_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取组织的调度统计

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

    return task_scheduler.get_organization_stats(organization_id)


@router.post("/scheduler/organization/{organization_id}/limit", response_model=MessageResponse)
def set_organization_concurrent_limit(
    organization_id: int,
    limit: int = Query(..., ge=1, le=100, description="并发限制（1-100）"),
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    设置组织的并发限制

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

    # 设置并发限制
    task_scheduler.set_organization_limit(organization_id, limit)

    return MessageResponse(message=f"组织 {organization_id} 的并发限制已设置为 {limit}")


@router.get("/reservations")
def get_all_reservations(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取所有Token预留信息

    需要SuperAdmin权限。
    """
    # TODO: 检查SuperAdmin权限
    # 这里暂时允许所有登录用户查看

    reservations = token_reservation_manager.get_all_reservations()

    return {
        "total_count": len(reservations),
        "reservations": [r.to_dict() for r in reservations.values()]
    }


@router.get("/reservations/{task_id}")
def get_task_reservation(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    获取任务的Token预留信息

    需要登录。
    """
    reservation = token_reservation_manager.get_reservation(task_id)

    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到该任务的预留记录"
        )

    return reservation.to_dict()


@router.get("/reservations/organization/{organization_id}/total")
def get_organization_reserved_tokens(
    organization_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取组织的总预留Token数

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

    total_reserved = token_reservation_manager.get_organization_reserved(organization_id)

    return {
        "organization_id": organization_id,
        "total_reserved_tokens": total_reserved
    }
