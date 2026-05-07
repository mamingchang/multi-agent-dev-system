"""
Project Manager
项目和权限管理
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .database.models import (
    User, Project, ProjectMember, UserRole,
    DBSession as SessionModel, Task
)


class PermissionError(Exception):
    """权限错误"""
    pass


class ProjectManager:
    """项目管理器"""

    # 权限定义：每个角色可以执行的操作
    PERMISSIONS = {
        UserRole.OWNER: {
            'create_session', 'delete_session', 'execute_task',
            'add_member', 'remove_member', 'update_member_role',
            'update_project', 'delete_project', 'view_project'
        },
        UserRole.ADMIN: {
            'create_session', 'delete_session', 'execute_task',
            'add_member', 'remove_member', 'update_member_role',
            'update_project', 'view_project'
        },
        UserRole.MEMBER: {
            'create_session', 'execute_task', 'view_project'
        },
        UserRole.VIEWER: {
            'view_project'
        }
    }

    def __init__(self, db_session: Session):
        """
        初始化项目管理器

        Args:
            db_session: 数据库会话
        """
        self.db = db_session

    def create_project(self, name: str, description: str, created_by: int) -> Project:
        """
        创建项目

        Args:
            name: 项目名称
            description: 项目描述
            created_by: 创建者用户ID

        Returns:
            创建的项目对象
        """
        project = Project(
            name=name,
            description=description,
            created_by=created_by
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        # 自动添加创建者为Owner
        member = ProjectMember(
            project_id=project.id,
            user_id=created_by,
            role=UserRole.OWNER
        )
        self.db.add(member)
        self.db.commit()

        return project

    def get_project(self, project_id: int) -> Optional[Project]:
        """获取项目"""
        return self.db.query(Project).filter_by(id=project_id).first()

    def update_project(self, project_id: int, user_id: int, **kwargs) -> Project:
        """
        更新项目信息

        Args:
            project_id: 项目ID
            user_id: 操作用户ID
            **kwargs: 要更新的字段

        Returns:
            更新后的项目对象

        Raises:
            PermissionError: 无权限
        """
        if not self.check_permission(project_id, user_id, 'update_project'):
            raise PermissionError(f"用户 {user_id} 无权更新项目 {project_id}")

        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")

        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)

        self.db.commit()
        self.db.refresh(project)
        return project

    def delete_project(self, project_id: int, user_id: int) -> bool:
        """
        删除项目

        Args:
            project_id: 项目ID
            user_id: 操作用户ID

        Returns:
            是否成功删除

        Raises:
            PermissionError: 无权限
        """
        if not self.check_permission(project_id, user_id, 'delete_project'):
            raise PermissionError(f"用户 {user_id} 无权删除项目 {project_id}")

        project = self.get_project(project_id)
        if not project:
            return False

        self.db.delete(project)
        self.db.commit()
        return True

    def add_member(self, project_id: int, user_id: int, new_member_id: int, role: UserRole = UserRole.MEMBER) -> ProjectMember:
        """
        添加项目成员

        Args:
            project_id: 项目ID
            user_id: 操作用户ID
            new_member_id: 新成员用户ID
            role: 角色

        Returns:
            成员关系对象

        Raises:
            PermissionError: 无权限
        """
        if not self.check_permission(project_id, user_id, 'add_member'):
            raise PermissionError(f"用户 {user_id} 无权添加成员到项目 {project_id}")

        try:
            member = ProjectMember(
                project_id=project_id,
                user_id=new_member_id,
                role=role
            )
            self.db.add(member)
            self.db.commit()
            self.db.refresh(member)
            return member
        except IntegrityError:
            self.db.rollback()
            raise ValueError(f"用户 {new_member_id} 已经是项目 {project_id} 的成员")

    def remove_member(self, project_id: int, user_id: int, member_id: int) -> bool:
        """
        移除项目成员

        Args:
            project_id: 项目ID
            user_id: 操作用户ID
            member_id: 要移除的成员用户ID

        Returns:
            是否成功移除

        Raises:
            PermissionError: 无权限
        """
        if not self.check_permission(project_id, user_id, 'remove_member'):
            raise PermissionError(f"用户 {user_id} 无权移除项目 {project_id} 的成员")

        # 不能移除Owner
        member = self.db.query(ProjectMember).filter_by(
            project_id=project_id,
            user_id=member_id
        ).first()

        if not member:
            return False

        if member.role == UserRole.OWNER:
            raise ValueError("不能移除项目所有者")

        self.db.delete(member)
        self.db.commit()
        return True

    def update_member_role(self, project_id: int, user_id: int, member_id: int, new_role: UserRole) -> ProjectMember:
        """
        更新成员角色

        Args:
            project_id: 项目ID
            user_id: 操作用户ID
            member_id: 要更新的成员用户ID
            new_role: 新角色

        Returns:
            更新后的成员关系对象

        Raises:
            PermissionError: 无权限
        """
        if not self.check_permission(project_id, user_id, 'update_member_role'):
            raise PermissionError(f"用户 {user_id} 无权更新项目 {project_id} 的成员角色")

        member = self.db.query(ProjectMember).filter_by(
            project_id=project_id,
            user_id=member_id
        ).first()

        if not member:
            raise ValueError(f"用户 {member_id} 不是项目 {project_id} 的成员")

        # 不能修改Owner角色
        if member.role == UserRole.OWNER:
            raise ValueError("不能修改项目所有者的角色")

        member.role = new_role
        self.db.commit()
        self.db.refresh(member)
        return member

    def get_user_role(self, project_id: int, user_id: int) -> Optional[UserRole]:
        """
        获取用户在项目中的角色

        Args:
            project_id: 项目ID
            user_id: 用户ID

        Returns:
            用户角色，如果不是成员则返回None
        """
        member = self.db.query(ProjectMember).filter_by(
            project_id=project_id,
            user_id=user_id
        ).first()

        return member.role if member else None

    def check_permission(self, project_id: int, user_id: int, action: str) -> bool:
        """
        检查用户是否有权限执行某个操作

        Args:
            project_id: 项目ID
            user_id: 用户ID
            action: 操作名称

        Returns:
            是否有权限
        """
        role = self.get_user_role(project_id, user_id)
        if not role:
            return False

        return action in self.PERMISSIONS.get(role, set())

    def list_user_projects(self, user_id: int) -> List[Dict[str, Any]]:
        """
        列出用户参与的所有项目

        Args:
            user_id: 用户ID

        Returns:
            项目列表
        """
        memberships = self.db.query(ProjectMember).filter_by(user_id=user_id).all()

        projects = []
        for membership in memberships:
            project = membership.project
            projects.append({
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'role': membership.role.value,
                'created_at': project.created_at.isoformat(),
                'updated_at': project.updated_at.isoformat()
            })

        return projects

    def list_project_members(self, project_id: int, user_id: int) -> List[Dict[str, Any]]:
        """
        列出项目的所有成员

        Args:
            project_id: 项目ID
            user_id: 操作用户ID

        Returns:
            成员列表

        Raises:
            PermissionError: 无权限
        """
        if not self.check_permission(project_id, user_id, 'view_project'):
            raise PermissionError(f"用户 {user_id} 无权查看项目 {project_id}")

        members = self.db.query(ProjectMember).filter_by(project_id=project_id).all()

        result = []
        for member in members:
            user = member.user
            result.append({
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': member.role.value,
                'joined_at': member.joined_at.isoformat()
            })

        return result

    def get_project_stats(self, project_id: int, user_id: int) -> Dict[str, Any]:
        """
        获取项目统计信息

        Args:
            project_id: 项目ID
            user_id: 操作用户ID

        Returns:
            统计信息

        Raises:
            PermissionError: 无权限
        """
        if not self.check_permission(project_id, user_id, 'view_project'):
            raise PermissionError(f"用户 {user_id} 无权查看项目 {project_id}")

        # 统计会话数
        session_count = self.db.query(SessionModel).filter_by(project_id=project_id).count()

        # 统计任务数
        task_count = self.db.query(Task).join(SessionModel).filter(
            SessionModel.project_id == project_id
        ).count()

        # 统计成员数
        member_count = self.db.query(ProjectMember).filter_by(project_id=project_id).count()

        return {
            'session_count': session_count,
            'task_count': task_count,
            'member_count': member_count
        }
