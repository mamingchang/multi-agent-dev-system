"""
群组管理器

管理项目群组、任务线程、成员权限
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..database.models import (
    IMGroup, IMGroupMember, IMThread, User, Project, Task
)


class GroupType:
    """群组类型"""
    PROJECT = "project"  # 项目群组
    TASK = "task"  # 任务线程
    DIRECT = "direct"  # 私聊


class MemberRole:
    """成员角色"""
    OWNER = "owner"  # 群主
    ADMIN = "admin"  # 管理员
    MEMBER = "member"  # 普通成员
    OBSERVER = "observer"  # 观察者（只读）


class GroupManager:
    """群组管理器"""

    def __init__(self, db: Session):
        self.db = db

    def create_project_group(
        self,
        project_id: int,
        creator_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> IMGroup:
        """
        创建项目群组

        为什么: 每个项目需要一个主群组用于团队沟通
        """
        # 检查项目是否存在
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # 检查是否已有群组
        existing = self.db.query(IMGroup).filter(
            and_(
                IMGroup.project_id == project_id,
                IMGroup.group_type == GroupType.PROJECT
            )
        ).first()
        if existing:
            return existing

        # 创建群组
        group = IMGroup(
            project_id=project_id,
            group_type=GroupType.PROJECT,
            name=name or f"{project.name} - 项目群组",
            description=description or f"项目 {project.name} 的主群组",
            created_by=creator_id,
            created_at=datetime.utcnow()
        )
        self.db.add(group)
        self.db.flush()

        # 添加创建者为群主
        self._add_member(group.id, creator_id, MemberRole.OWNER)

        # 自动添加项目成员
        self._auto_add_project_members(group.id, project_id)

        self.db.commit()
        return group

    def create_task_thread(
        self,
        task_id: int,
        creator_id: int,
        parent_group_id: Optional[int] = None
    ) -> IMThread:
        """
        创建任务线程

        为什么: 任务讨论需要独立线程，避免主群组混乱
        """
        # 检查任务是否存在
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # 如果没有指定父群组，使用项目群组
        if not parent_group_id:
            parent_group = self.db.query(IMGroup).filter(
                and_(
                    IMGroup.project_id == task.project_id,
                    IMGroup.group_type == GroupType.PROJECT
                )
            ).first()
            if parent_group:
                parent_group_id = parent_group.id

        # 创建线程
        thread = IMThread(
            task_id=task_id,
            parent_group_id=parent_group_id,
            name=f"任务: {task.title}",
            created_by=creator_id,
            created_at=datetime.utcnow()
        )
        self.db.add(thread)
        self.db.commit()

        return thread

    def add_member(
        self,
        group_id: int,
        user_id: int,
        role: str = MemberRole.MEMBER,
        added_by: Optional[int] = None
    ) -> IMGroupMember:
        """
        添加群组成员

        为什么: 支持动态添加成员到群组
        """
        return self._add_member(group_id, user_id, role, added_by)

    def _add_member(
        self,
        group_id: int,
        user_id: int,
        role: str = MemberRole.MEMBER,
        added_by: Optional[int] = None
    ) -> IMGroupMember:
        """内部方法: 添加成员"""
        # 检查是否已是成员
        existing = self.db.query(IMGroupMember).filter(
            and_(
                IMGroupMember.group_id == group_id,
                IMGroupMember.user_id == user_id
            )
        ).first()
        if existing:
            return existing

        # 添加成员
        member = IMGroupMember(
            group_id=group_id,
            user_id=user_id,
            role=role,
            added_by=added_by,
            joined_at=datetime.utcnow()
        )
        self.db.add(member)
        self.db.flush()
        return member

    def _auto_add_project_members(self, group_id: int, project_id: int):
        """
        自动添加项目成员到群组

        为什么: 项目成员应该自动加入项目群组
        """
        # 获取项目的所有成员（通过任务关联）
        members = self.db.query(User).join(
            Task, Task.assigned_to == User.id
        ).filter(
            Task.project_id == project_id
        ).distinct().all()

        for member in members:
            self._add_member(group_id, member.id, MemberRole.MEMBER)

    def remove_member(self, group_id: int, user_id: int) -> bool:
        """
        移除群组成员

        为什么: 支持成员退出或被移除
        """
        member = self.db.query(IMGroupMember).filter(
            and_(
                IMGroupMember.group_id == group_id,
                IMGroupMember.user_id == user_id
            )
        ).first()

        if member:
            self.db.delete(member)
            self.db.commit()
            return True
        return False

    def update_member_role(
        self,
        group_id: int,
        user_id: int,
        new_role: str
    ) -> IMGroupMember:
        """
        更新成员角色

        为什么: 支持权限管理
        """
        member = self.db.query(IMGroupMember).filter(
            and_(
                IMGroupMember.group_id == group_id,
                IMGroupMember.user_id == user_id
            )
        ).first()

        if not member:
            raise ValueError(f"Member not found in group {group_id}")

        member.role = new_role
        self.db.commit()
        return member

    def get_group_members(self, group_id: int) -> List[Dict[str, Any]]:
        """
        获取群组成员列表

        为什么: 显示群组成员信息
        """
        members = self.db.query(IMGroupMember, User).join(
            User, IMGroupMember.user_id == User.id
        ).filter(
            IMGroupMember.group_id == group_id
        ).all()

        return [
            {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "role": member.role,
                "joined_at": member.joined_at.isoformat()
            }
            for member, user in members
        ]

    def check_permission(
        self,
        group_id: int,
        user_id: int,
        required_role: str = MemberRole.MEMBER
    ) -> bool:
        """
        检查用户权限

        为什么: 权限控制，确保只有授权用户可以操作
        """
        member = self.db.query(IMGroupMember).filter(
            and_(
                IMGroupMember.group_id == group_id,
                IMGroupMember.user_id == user_id
            )
        ).first()

        if not member:
            return False

        # 角色权限等级: OWNER > ADMIN > MEMBER > OBSERVER
        role_levels = {
            MemberRole.OWNER: 4,
            MemberRole.ADMIN: 3,
            MemberRole.MEMBER: 2,
            MemberRole.OBSERVER: 1
        }

        return role_levels.get(member.role, 0) >= role_levels.get(required_role, 0)
