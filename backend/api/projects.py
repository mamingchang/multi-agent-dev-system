"""
Projects API
项目管理API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from src.database.models import UserRole
from src.project_manager import ProjectManager, PermissionError
from ..dependencies import get_db, get_current_user, get_project_manager, check_project_permission

router = APIRouter(prefix="/api/projects", tags=["Projects"])


# Pydantic模型
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime
    role: Optional[str] = None  # 当前用户在项目中的角色

    class Config:
        from_attributes = True


class MemberAdd(BaseModel):
    user_id: int
    role: str = "member"  # owner, admin, member, viewer


class MemberUpdate(BaseModel):
    role: str


class MemberResponse(BaseModel):
    user_id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    joined_at: datetime


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    current_user: dict = Depends(get_current_user),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    列出当前用户的所有项目

    Returns:
        项目列表
    """
    projects = project_manager.list_user_projects(current_user["id"])
    return projects


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    创建新项目

    Args:
        project_data: 项目信息

    Returns:
        创建的项目
    """
    project = project_manager.create_project(
        name=project_data.name,
        description=project_data.description,
        created_by=current_user["id"]
    )

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_by": project.created_by,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "role": "owner"
    }


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    获取项目详情

    Args:
        project_id: 项目ID

    Returns:
        项目详情
    """
    # 检查权限
    check_project_permission(project_id, current_user["id"], "view_project", project_manager)

    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    role = project_manager.get_user_role(project_id, current_user["id"])

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_by": project.created_by,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "role": role.value if role else None
    }


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: dict = Depends(get_current_user),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    更新项目信息

    Args:
        project_id: 项目ID
        project_data: 更新的项目信息

    Returns:
        更新后的项目
    """
    try:
        update_data = project_data.dict(exclude_unset=True)
        project = project_manager.update_project(
            project_id=project_id,
            user_id=current_user["id"],
            **update_data
        )

        role = project_manager.get_user_role(project_id, current_user["id"])

        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "created_by": project.created_by,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "role": role.value if role else None
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    删除项目

    Args:
        project_id: 项目ID
    """
    try:
        project_manager.delete_project(project_id, current_user["id"])
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{project_id}/members", response_model=List[MemberResponse])
async def list_members(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    列出项目成员

    Args:
        project_id: 项目ID

    Returns:
        成员列表
    """
    try:
        members = project_manager.list_project_members(project_id, current_user["id"])
        return members
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{project_id}/members", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_member(
    project_id: int,
    member_data: MemberAdd,
    current_user: dict = Depends(get_current_user),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    添加项目成员

    Args:
        project_id: 项目ID
        member_data: 成员信息

    Returns:
        添加结果
    """
    try:
        role = UserRole(member_data.role)
        member = project_manager.add_member(
            project_id=project_id,
            user_id=current_user["id"],
            new_member_id=member_data.user_id,
            role=role
        )
        return {"message": "Member added successfully", "member_id": member.id}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    project_id: int,
    user_id: int,
    current_user: dict = Depends(get_current_user),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    移除项目成员

    Args:
        project_id: 项目ID
        user_id: 要移除的用户ID
    """
    try:
        project_manager.remove_member(project_id, current_user["id"], user_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{project_id}/members/{user_id}", response_model=dict)
async def update_member_role(
    project_id: int,
    user_id: int,
    member_data: MemberUpdate,
    current_user: dict = Depends(get_current_user),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    更新成员角色

    Args:
        project_id: 项目ID
        user_id: 成员用户ID
        member_data: 新角色

    Returns:
        更新结果
    """
    try:
        role = UserRole(member_data.role)
        member = project_manager.update_member_role(
            project_id=project_id,
            user_id=current_user["id"],
            member_id=user_id,
            new_role=role
        )
        return {"message": "Member role updated successfully", "new_role": member.role.value}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}/stats", response_model=dict)
async def get_project_stats(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    project_manager: ProjectManager = Depends(get_project_manager)
):
    """
    获取项目统计信息

    Args:
        project_id: 项目ID

    Returns:
        统计信息
    """
    try:
        stats = project_manager.get_project_stats(project_id, current_user["id"])
        return stats
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
