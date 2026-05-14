"""
项目管理API路由

端点：
- POST /projects - 创建项目
- GET /projects - 获取用户的项目列表
- GET /projects/{project_id} - 获取项目详情
- PUT /projects/{project_id} - 更新项目
- DELETE /projects/{project_id} - 删除项目
- POST /projects/{project_id}/members - 添加项目成员
- GET /projects/{project_id}/members - 获取项目成员列表
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List

from ..database.database import Database, ProjectRepository
from ..database.models import User, UserRole, AuditAction
from ..database.organization_repository import OrganizationRepository, OrganizationMemberRepository
from .schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    ProjectMemberAdd, ProjectMemberResponse, MessageResponse
)
from .auth import get_current_active_user, check_project_permission
from .dependencies import get_db
from .audit_helper import log_audit
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/projects", tags=["项目管理"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    创建项目

    创建新项目，创建者自动成为项目Owner。
    需要指定organization_id，且用户必须是该组织成员。
    """
    with db.get_session() as session:
        # 检查用户是否是组织成员
        member_repo = OrganizationMemberRepository(session)
        if not member_repo.is_member(project_data.organization_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您不是该组织的成员"
            )

        # 检查组织项目数限制
        org_repo = OrganizationRepository(session)
        org = org_repo.get_by_id(project_data.organization_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="组织不存在"
            )

        if len(org.projects) >= org.max_projects:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"组织项目数已达上限（{org.max_projects}）"
            )

        project_repo = ProjectRepository(session)

        # 创建项目（包含organization_id）
        project = project_repo.create(
            name=project_data.name,
            description=project_data.description,
            created_by=current_user.id,
            organization_id=project_data.organization_id
        )

        # 创建项目代码目录
        from ..project_code import ProjectCodeManager
        code_manager = ProjectCodeManager()
        try:
            code_path = code_manager.create_project_directory(
                organization_id=project_data.organization_id,
                project_id=project.id,
                project_name=project_data.name
            )

            # 更新项目的代码路径
            project.code_path = code_path
            project.project_type = "manual"
            session.commit()

        except Exception as e:
            print(f"Warning: Failed to create project directory: {e}")

        # 添加创建者为Owner
        project_repo.add_member(
            project_id=project.id,
            user_id=current_user.id,
            role=UserRole.OWNER
        )

        # 记录审计日志
        log_audit(
            session=session,
            action=AuditAction.PROJECT_CREATE,
            resource_type="project",
            resource_id=str(project.id),
            user=current_user,
            organization_id=project_data.organization_id,
            request=request,
            details={
                "name": project.name,
                "description": project.description,
                "organization_id": project_data.organization_id,
                "code_path": code_path
            }
        )

        # 立即构造响应对象
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            created_by=project.created_by,
            created_at=project.created_at,
            updated_at=project.updated_at
        )


@router.get("", response_model=List[ProjectResponse])
def list_projects(
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取用户的项目列表

    返回当前用户拥有或参与的所有项目。
    """
    with db.get_session() as session:
        project_repo = ProjectRepository(session)
        projects = project_repo.get_user_projects(current_user.id)

        # 转换为响应模型
        return [
            ProjectResponse(
                id=p.id,
                name=p.name,
                description=p.description,
                created_by=p.created_by,
                created_at=p.created_at,
                updated_at=p.updated_at
            )
            for p in projects
        ]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取项目详情

    需要是项目成员。
    """
    # 检查权限
    check_project_permission(current_user, project_id, db)

    with db.get_session() as session:
        project_repo = ProjectRepository(session)
        project = project_repo.get_by_id(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )

        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            created_by=project.created_by,
            created_at=project.created_at,
            updated_at=project.updated_at
        )


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    更新项目

    需要Admin或Owner权限。
    """
    # 检查权限（需要admin权限）
    check_project_permission(current_user, project_id, db, required_role="admin")

    with db.get_session() as session:
        project_repo = ProjectRepository(session)
        project = project_repo.get_by_id(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )

        # 更新字段
        if project_data.name is not None:
            project.name = project_data.name
        if project_data.description is not None:
            project.description = project_data.description

        session.flush()

        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            created_by=project.created_by,
            created_at=project.created_at,
            updated_at=project.updated_at
        )


@router.delete("/{project_id}", response_model=MessageResponse)
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    删除项目

    需要Owner权限。会级联删除所有相关数据。
    """
    # 检查权限（需要owner权限）
    check_project_permission(current_user, project_id, db, required_role="owner")

    with db.get_session() as session:
        project_repo = ProjectRepository(session)
        project = project_repo.get_by_id(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )

        session.delete(project)
        session.flush()

        return MessageResponse(message="项目已删除")


@router.post("/{project_id}/members", response_model=ProjectMemberResponse, status_code=status.HTTP_201_CREATED)
def add_project_member(
    project_id: int,
    member_data: ProjectMemberAdd,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    添加项目成员

    需要Admin或Owner权限。
    """
    # 检查权限
    check_project_permission(current_user, project_id, db, required_role="admin")

    with db.get_session() as session:
        project_repo = ProjectRepository(session)

        # 检查项目是否存在
        project = project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )

        # 添加成员
        try:
            member = project_repo.add_member(
                project_id=project_id,
                user_id=member_data.user_id,
                role=member_data.role
            )

            return ProjectMemberResponse(
                id=member.id,
                user_id=member.user_id,
                role=member.role,
                joined_at=member.joined_at
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"添加成员失败: {str(e)}"
            )


@router.get("/{project_id}/members", response_model=List[ProjectMemberResponse])
def list_project_members(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取项目成员列表

    需要是项目成员。
    """
    # 检查权限
    check_project_permission(current_user, project_id, db)

    with db.get_session() as session:
        from ..database.models import ProjectMember

        members = session.query(ProjectMember).filter(
            ProjectMember.project_id == project_id
        ).all()

        return [
            ProjectMemberResponse(
                id=m.id,
                user_id=m.user_id,
                role=m.role,
                joined_at=m.joined_at
            )
            for m in members
        ]


class ProjectStatsResponse(BaseModel):
    """项目统计响应"""
    project_id: int
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    total_members: int
    created_at: datetime


@router.get("/{project_id}/stats", response_model=ProjectStatsResponse)
def get_project_stats(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取项目统计信息
    
    返回项目的任务数、成员数等统计数据。
    """
    # 检查权限
    check_project_permission(current_user, project_id, db)
    
    with db.get_session() as session:
        from ..database.models import Project, ProjectMember, Task, Session as WorkflowSession
        from ..database.models import TaskStatus
        
        # 获取项目
        project = session.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )
        
        # 统计成员数
        total_members = session.query(ProjectMember).filter(
            ProjectMember.project_id == project_id
        ).count()
        
        # 获取项目的所有会话
        sessions = session.query(WorkflowSession).filter(
            WorkflowSession.project_id == project_id
        ).all()
        session_ids = [s.id for s in sessions]
        
        # 统计任务数
        if session_ids:
            total_tasks = session.query(Task).filter(
                Task.session_id.in_(session_ids)
            ).count()
            
            completed_tasks = session.query(Task).filter(
                Task.session_id.in_(session_ids),
                Task.status == TaskStatus.COMPLETED
            ).count()
            
            in_progress_tasks = session.query(Task).filter(
                Task.session_id.in_(session_ids),
                Task.status.in_([
                    TaskStatus.IN_REQUIREMENT,
                    TaskStatus.IN_DESIGN,
                    TaskStatus.IN_DEVELOPMENT,
                    TaskStatus.IN_REVIEW,
                    TaskStatus.IN_TESTING,
                    TaskStatus.IN_DEPLOYMENT
                ])
            ).count()
        else:
            total_tasks = 0
            completed_tasks = 0
            in_progress_tasks = 0
        
        return ProjectStatsResponse(
            project_id=project_id,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            total_members=total_members,
            created_at=project.created_at
        )
