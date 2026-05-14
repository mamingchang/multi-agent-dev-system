"""
组织管理API路由

端点：
- POST /organizations - 创建组织
- GET /organizations - 获取组织列表
- GET /organizations/{org_id} - 获取组织详情
- PUT /organizations/{org_id} - 更新组织
- DELETE /organizations/{org_id} - 删除组织
- GET /organizations/{org_id}/quota - 获取配额信息
- POST /organizations/{org_id}/members - 添加成员
- GET /organizations/{org_id}/members - 获取成员列表
- PUT /organizations/{org_id}/members/{user_id} - 更新成员角色
- DELETE /organizations/{org_id}/members/{user_id} - 移除成员
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List

from ..database.database import Database
from ..database.organization_repository import OrganizationRepository, OrganizationMemberRepository
from ..database.models import User, OrganizationRole, AuditAction
from .schemas import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrganizationQuotaResponse, OrganizationMemberAdd,
    OrganizationMemberUpdate, OrganizationMemberResponse
)
from .auth import get_current_active_user
from .dependencies import get_db
from .audit_helper import log_audit

router = APIRouter(prefix="/organizations", tags=["组织管理"])


def check_org_admin(current_user: User, org_id: int, db: Database):
    """
    检查用户是否是组织管理员

    Args:
        current_user: 当前用户
        org_id: 组织ID
        db: 数据库连接

    Raises:
        HTTPException: 如果用户不是管理员
    """
    with db.get_session() as session:
        member_repo = OrganizationMemberRepository(session)
        role = member_repo.get_user_role(org_id, current_user.id)

        if not role or role not in [OrganizationRole.ORG_ADMIN, OrganizationRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要组织管理员权限"
            )


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    org_data: OrganizationCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    创建组织

    创建新组织，创建者自动成为组织管理员。
    """
    with db.get_session() as session:
        org_repo = OrganizationRepository(session)

        # 检查slug是否已存在
        existing = org_repo.get_by_slug(org_data.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"组织标识符 '{org_data.slug}' 已存在"
            )

        # 创建组织
        org = org_repo.create(
            name=org_data.name,
            slug=org_data.slug,
            description=org_data.description,
            token_quota=org_data.token_quota,
            max_projects=org_data.max_projects,
            max_members=org_data.max_members
        )

        # 添加创建者为管理员
        member_repo = OrganizationMemberRepository(session)
        member_repo.add_member(
            organization_id=org.id,
            user_id=current_user.id,
            role=OrganizationRole.ORG_ADMIN
        )

        # 记录审计日志
        log_audit(
            session=session,
            action=AuditAction.ORG_CREATE,
            resource_type="organization",
            resource_id=str(org.id),
            user=current_user,
            organization_id=org.id,
            request=request,
            details={
                "name": org.name,
                "slug": org.slug,
                "token_quota": org.token_quota
            }
        )

        # 构造响应对象（在session内）
        return OrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            description=org.description,
            token_quota=org.token_quota,
            token_used=org.token_used,
            max_projects=org.max_projects,
            max_members=org.max_members,
            is_active=org.is_active,
            created_at=org.created_at,
            updated_at=org.updated_at
        )


@router.get("", response_model=List[OrganizationResponse])
def list_organizations(
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取组织列表

    返回当前用户所属的所有组织。
    """
    with db.get_session() as session:
        member_repo = OrganizationMemberRepository(session)

        # 获取用户所属的组织
        memberships = member_repo.list_user_organizations(current_user.id)

        # 构造响应列表（在session内）
        return [
            OrganizationResponse(
                id=m.organization.id,
                name=m.organization.name,
                slug=m.organization.slug,
                description=m.organization.description,
                token_quota=m.organization.token_quota,
                token_used=m.organization.token_used,
                max_projects=m.organization.max_projects,
                max_members=m.organization.max_members,
                is_active=m.organization.is_active,
                created_at=m.organization.created_at,
                updated_at=m.organization.updated_at
            )
            for m in memberships
        ]


@router.get("/{org_id}", response_model=OrganizationResponse)
def get_organization(
    org_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取组织详情

    返回指定组织的详细信息。
    """
    with db.get_session() as session:
        org_repo = OrganizationRepository(session)
        member_repo = OrganizationMemberRepository(session)

        # 检查用户是否是组织成员
        if not member_repo.is_member(org_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此组织"
            )

        org = org_repo.get_by_id(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="组织不存在"
            )

        return OrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            description=org.description,
            token_quota=org.token_quota,
            token_used=org.token_used,
            max_projects=org.max_projects,
            max_members=org.max_members,
            is_active=org.is_active,
            created_at=org.created_at,
            updated_at=org.updated_at
        )


@router.put("/{org_id}", response_model=OrganizationResponse)
def update_organization(
    org_id: int,
    org_data: OrganizationUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    更新组织

    更新组织信息，需要管理员权限。
    """
    # 检查权限
    check_org_admin(current_user, org_id, db)

    with db.get_session() as session:
        org_repo = OrganizationRepository(session)

        org = org_repo.update(
            org_id=org_id,
            name=org_data.name,
            description=org_data.description,
            token_quota=org_data.token_quota,
            max_projects=org_data.max_projects,
            max_members=org_data.max_members,
            is_active=org_data.is_active
        )

        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="组织不存在"
            )

        # 记录审计日志
        log_audit(
            session=session,
            action=AuditAction.ORG_UPDATE,
            resource_type="organization",
            resource_id=str(org_id),
            user=current_user,
            organization_id=org_id,
            request=request,
            details={
                "name": org_data.name,
                "description": org_data.description,
                "token_quota": org_data.token_quota
            }
        )

        return OrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            description=org.description,
            token_quota=org.token_quota,
            token_used=org.token_used,
            max_projects=org.max_projects,
            max_members=org.max_members,
            is_active=org.is_active,
            created_at=org.created_at,
            updated_at=org.updated_at
        )


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(
    org_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    删除组织

    删除组织及其所有关联数据，需要管理员权限。

    ⚠️ 警告：此操作不可逆！
    """
    # 检查权限
    check_org_admin(current_user, org_id, db)

    with db.get_session() as session:
        org_repo = OrganizationRepository(session)

        success = org_repo.delete(org_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="组织不存在"
            )


@router.get("/{org_id}/quota", response_model=OrganizationQuotaResponse)
def get_organization_quota(
    org_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取组织配额信息

    返回组织的Token配额、项目数、成员数等信息。
    """
    with db.get_session() as session:
        member_repo = OrganizationMemberRepository(session)

        # 检查用户是否是组织成员
        if not member_repo.is_member(org_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此组织"
            )

        org_repo = OrganizationRepository(session)
        quota_info = org_repo.check_quota(org_id)

        if not quota_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="组织不存在"
            )

        return quota_info


@router.post("/{org_id}/members", response_model=OrganizationMemberResponse, status_code=status.HTTP_201_CREATED)
def add_organization_member(
    org_id: int,
    member_data: OrganizationMemberAdd,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    添加组织成员

    将用户添加到组织，需要管理员权限。
    """
    # 检查权限
    check_org_admin(current_user, org_id, db)

    with db.get_session() as session:
        org_repo = OrganizationRepository(session)
        member_repo = OrganizationMemberRepository(session)

        # 检查组织是否存在
        org = org_repo.get_by_id(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="组织不存在"
            )

        # 检查是否已是成员
        existing = member_repo.get_member(org_id, member_data.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户已是组织成员"
            )

        # 检查成员数限制
        if len(org.members) >= org.max_members:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"组织成员数已达上限（{org.max_members}）"
            )

        # 添加成员
        member = member_repo.add_member(
            organization_id=org_id,
            user_id=member_data.user_id,
            role=OrganizationRole[member_data.role.value.upper()]
        )

        return OrganizationMemberResponse(
            id=member.id,
            organization_id=member.organization_id,
            user_id=member.user_id,
            role=member.role.value,
            joined_at=member.joined_at
        )


@router.get("/{org_id}/members", response_model=List[OrganizationMemberResponse])
def list_organization_members(
    org_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取组织成员列表

    返回组织的所有成员。
    """
    with db.get_session() as session:
        member_repo = OrganizationMemberRepository(session)

        # 检查用户是否是组织成员
        if not member_repo.is_member(org_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此组织"
            )

        members = member_repo.list_members(org_id)

        # 添加用户信息
        result = []
        for member in members:
            member_dict = {
                'id': member.id,
                'organization_id': member.organization_id,
                'user_id': member.user_id,
                'role': member.role.value,
                'joined_at': member.joined_at,
                'user': {
                    'id': member.user.id,
                    'username': member.user.username,
                    'email': member.user.email,
                    'full_name': member.user.full_name
                }
            }
            result.append(member_dict)

        return result


@router.put("/{org_id}/members/{user_id}", response_model=OrganizationMemberResponse)
def update_organization_member(
    org_id: int,
    user_id: int,
    member_data: OrganizationMemberUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    更新组织成员角色

    修改成员的角色，需要管理员权限。
    """
    # 检查权限
    check_org_admin(current_user, org_id, db)

    with db.get_session() as session:
        member_repo = OrganizationMemberRepository(session)

        member = member_repo.update_role(
            organization_id=org_id,
            user_id=user_id,
            new_role=OrganizationRole[member_data.role.value.upper()]
        )

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="成员不存在"
            )

        return OrganizationMemberResponse(
            id=member.id,
            organization_id=member.organization_id,
            user_id=member.user_id,
            role=member.role.value,
            joined_at=member.joined_at
        )


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_organization_member(
    org_id: int,
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    移除组织成员

    将用户从组织中移除，需要管理员权限。
    """
    # 检查权限
    check_org_admin(current_user, org_id, db)

    # 不能移除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能移除自己"
        )

    with db.get_session() as session:
        member_repo = OrganizationMemberRepository(session)

        success = member_repo.remove_member(org_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="成员不存在"
            )
