"""
组织管理仓储层

提供组织和组织成员的数据访问接口。
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from .models import Organization, OrganizationMember, OrganizationRole, User


class OrganizationRepository:
    """组织仓储"""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        name: str,
        slug: str,
        description: Optional[str] = None,
        token_quota: int = 1000000,
        max_projects: int = 10,
        max_members: int = 50
    ) -> Organization:
        """
        创建组织

        Args:
            name: 组织名称
            slug: URL友好标识符
            description: 描述
            token_quota: Token配额
            max_projects: 最大项目数
            max_members: 最大成员数

        Returns:
            Organization: 创建的组织
        """
        org = Organization(
            name=name,
            slug=slug,
            description=description,
            token_quota=token_quota,
            token_used=0,
            max_projects=max_projects,
            max_members=max_members,
            is_active=True
        )

        self.session.add(org)
        self.session.commit()
        self.session.refresh(org)

        return org

    def get_by_id(self, org_id: int) -> Optional[Organization]:
        """根据ID获取组织"""
        return self.session.query(Organization).filter(
            Organization.id == org_id
        ).first()

    def get_by_slug(self, slug: str) -> Optional[Organization]:
        """根据slug获取组织"""
        return self.session.query(Organization).filter(
            Organization.slug == slug
        ).first()

    def list_all(self, active_only: bool = True) -> List[Organization]:
        """
        获取所有组织

        Args:
            active_only: 是否只返回激活的组织

        Returns:
            List[Organization]: 组织列表
        """
        query = self.session.query(Organization)

        if active_only:
            query = query.filter(Organization.is_active == True)

        return query.order_by(Organization.created_at.desc()).all()

    def update(
        self,
        org_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        token_quota: Optional[int] = None,
        max_projects: Optional[int] = None,
        max_members: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Organization]:
        """
        更新组织

        Args:
            org_id: 组织ID
            name: 新名称
            description: 新描述
            token_quota: 新配额
            max_projects: 新最大项目数
            max_members: 新最大成员数
            is_active: 是否激活

        Returns:
            Organization: 更新后的组织
        """
        org = self.get_by_id(org_id)
        if not org:
            return None

        if name is not None:
            org.name = name
        if description is not None:
            org.description = description
        if token_quota is not None:
            org.token_quota = token_quota
        if max_projects is not None:
            org.max_projects = max_projects
        if max_members is not None:
            org.max_members = max_members
        if is_active is not None:
            org.is_active = is_active

        self.session.commit()
        self.session.refresh(org)

        return org

    def delete(self, org_id: int) -> bool:
        """
        删除组织

        Args:
            org_id: 组织ID

        Returns:
            bool: 是否成功删除
        """
        org = self.get_by_id(org_id)
        if not org:
            return False

        self.session.delete(org)
        self.session.commit()

        return True

    def update_token_usage(self, org_id: int, tokens_used: int) -> Optional[Organization]:
        """
        更新Token使用量

        Args:
            org_id: 组织ID
            tokens_used: 使用的Token数（增量）

        Returns:
            Organization: 更新后的组织
        """
        org = self.get_by_id(org_id)
        if not org:
            return None

        org.token_used += tokens_used
        self.session.commit()
        self.session.refresh(org)

        return org

    def check_quota(self, org_id: int) -> dict:
        """
        检查配额使用情况

        Args:
            org_id: 组织ID

        Returns:
            dict: 配额信息
        """
        org = self.get_by_id(org_id)
        if not org:
            return None

        return {
            'token_quota': org.token_quota,
            'token_used': org.token_used,
            'token_remaining': org.token_quota - org.token_used,
            'usage_percentage': (org.token_used / org.token_quota * 100) if org.token_quota > 0 else 0,
            'max_projects': org.max_projects,
            'current_projects': len(org.projects),
            'max_members': org.max_members,
            'current_members': len(org.members)
        }


class OrganizationMemberRepository:
    """组织成员仓储"""

    def __init__(self, session: Session):
        self.session = session

    def add_member(
        self,
        organization_id: int,
        user_id: int,
        role: OrganizationRole = OrganizationRole.ORG_MEMBER
    ) -> OrganizationMember:
        """
        添加组织成员

        Args:
            organization_id: 组织ID
            user_id: 用户ID
            role: 角色

        Returns:
            OrganizationMember: 创建的成员关系
        """
        member = OrganizationMember(
            organization_id=organization_id,
            user_id=user_id,
            role=role
        )

        self.session.add(member)
        self.session.commit()
        self.session.refresh(member)

        return member

    def get_member(self, organization_id: int, user_id: int) -> Optional[OrganizationMember]:
        """
        获取组织成员

        Args:
            organization_id: 组织ID
            user_id: 用户ID

        Returns:
            OrganizationMember: 成员关系
        """
        return self.session.query(OrganizationMember).filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id
        ).first()

    def list_members(self, organization_id: int) -> List[OrganizationMember]:
        """
        获取组织所有成员

        Args:
            organization_id: 组织ID

        Returns:
            List[OrganizationMember]: 成员列表
        """
        return self.session.query(OrganizationMember).filter(
            OrganizationMember.organization_id == organization_id
        ).order_by(OrganizationMember.joined_at).all()

    def list_user_organizations(self, user_id: int) -> List[OrganizationMember]:
        """
        获取用户所属的所有组织

        Args:
            user_id: 用户ID

        Returns:
            List[OrganizationMember]: 成员关系列表
        """
        return self.session.query(OrganizationMember).filter(
            OrganizationMember.user_id == user_id
        ).order_by(OrganizationMember.joined_at.desc()).all()

    def update_role(
        self,
        organization_id: int,
        user_id: int,
        new_role: OrganizationRole
    ) -> Optional[OrganizationMember]:
        """
        更新成员角色

        Args:
            organization_id: 组织ID
            user_id: 用户ID
            new_role: 新角色

        Returns:
            OrganizationMember: 更新后的成员关系
        """
        member = self.get_member(organization_id, user_id)
        if not member:
            return None

        member.role = new_role
        self.session.commit()
        self.session.refresh(member)

        return member

    def remove_member(self, organization_id: int, user_id: int) -> bool:
        """
        移除组织成员

        Args:
            organization_id: 组织ID
            user_id: 用户ID

        Returns:
            bool: 是否成功移除
        """
        member = self.get_member(organization_id, user_id)
        if not member:
            return False

        self.session.delete(member)
        self.session.commit()

        return True

    def is_member(self, organization_id: int, user_id: int) -> bool:
        """
        检查用户是否是组织成员

        Args:
            organization_id: 组织ID
            user_id: 用户ID

        Returns:
            bool: 是否是成员
        """
        return self.get_member(organization_id, user_id) is not None

    def get_user_role(self, organization_id: int, user_id: int) -> Optional[OrganizationRole]:
        """
        获取用户在组织中的角色

        Args:
            organization_id: 组织ID
            user_id: 用户ID

        Returns:
            OrganizationRole: 角色，如果不是成员返回None
        """
        member = self.get_member(organization_id, user_id)
        return member.role if member else None
