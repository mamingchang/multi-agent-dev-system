"""
版本管理API路由

端点：
- POST /artifacts/versions - 创建新版本
- GET /artifacts/{task_id}/{artifact_name}/versions - 列出所有版本
- GET /artifacts/{task_id}/{artifact_name}/versions/{version} - 获取指定版本
- GET /artifacts/{task_id}/{artifact_name}/diff - 对比两个版本
- POST /artifacts/{task_id}/{artifact_name}/versions/{version}/mark-key - 标记为关键版本
- POST /artifacts/{task_id}/{artifact_name}/rollback - 回滚到指定版本
- DELETE /artifacts/{task_id}/{artifact_name}/cleanup - 清理旧版本
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel

from ..database.models import User, Artifact
from ..database.database import Database
from ..versioning.version_manager import VersionManager
from .schemas import MessageResponse
from .auth import get_current_active_user
from .dependencies import get_db

router = APIRouter(prefix="/artifacts", tags=["产物版本管理"])


# ==================== Pydantic模型 ====================

class ArtifactVersionCreate(BaseModel):
    """创建版本请求"""
    task_id: str
    artifact_name: str
    artifact_type: str
    content: str
    parent_version: Optional[str] = None
    is_key_version: bool = False
    version_description: Optional[str] = None


class ArtifactVersionResponse(BaseModel):
    """版本响应"""
    id: int
    task_id: str
    name: str
    artifact_type: str
    version: str
    parent_version: Optional[str]
    is_key_version: bool
    version_description: Optional[str]
    content: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class VersionDiffResponse(BaseModel):
    """版本对比响应"""
    from_version: str
    to_version: str
    diff: str
    added_lines: int
    removed_lines: int
    changed_lines: int
    total_changes: int
    semantic_description: str


class MarkKeyVersionRequest(BaseModel):
    """标记关键版本请求"""
    description: Optional[str] = None


class RollbackRequest(BaseModel):
    """回滚请求"""
    target_version: str


# ==================== API端点 ====================

@router.post("/versions", response_model=ArtifactVersionResponse, status_code=status.HTTP_201_CREATED)
def create_artifact_version(
    version_data: ArtifactVersionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    创建新版本

    需要登录。
    """
    with db.get_session() as session:
        version_manager = VersionManager(session)

        artifact = version_manager.create_version(
            task_id=version_data.task_id,
            artifact_name=version_data.artifact_name,
            artifact_type=version_data.artifact_type,
            content=version_data.content,
            parent_version=version_data.parent_version,
            is_key_version=version_data.is_key_version,
            version_description=version_data.version_description,
            created_by=current_user.id
        )

        return ArtifactVersionResponse(
            id=artifact.id,
            task_id=artifact.task_id,
            name=artifact.name,
            artifact_type=artifact.artifact_type,
            version=artifact.version,
            parent_version=artifact.parent_version,
            is_key_version=artifact.is_key_version,
            version_description=artifact.version_description,
            content=artifact.content,
            created_at=artifact.created_at.isoformat()
        )


@router.get("/{task_id}/{artifact_name}/versions", response_model=List[ArtifactVersionResponse])
def list_artifact_versions(
    task_id: str,
    artifact_name: str,
    key_versions_only: bool = Query(False, description="只返回关键版本"),
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    列出所有版本

    需要登录。
    """
    with db.get_session() as session:
        version_manager = VersionManager(session)

        versions = version_manager.list_versions(
            task_id=task_id,
            artifact_name=artifact_name,
            key_versions_only=key_versions_only
        )

        return [
            ArtifactVersionResponse(
                id=v.id,
                task_id=v.task_id,
                name=v.name,
                artifact_type=v.artifact_type,
                version=v.version,
                parent_version=v.parent_version,
                is_key_version=v.is_key_version,
                version_description=v.version_description,
                content=v.content,
                created_at=v.created_at.isoformat()
            )
            for v in versions
        ]


@router.get("/{task_id}/{artifact_name}/versions/{version}", response_model=ArtifactVersionResponse)
def get_artifact_version(
    task_id: str,
    artifact_name: str,
    version: str,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取指定版本

    需要登录。
    """
    with db.get_session() as session:
        version_manager = VersionManager(session)

        artifact = version_manager.get_version(task_id, artifact_name, version)

        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="版本不存在"
            )

        return ArtifactVersionResponse(
            id=artifact.id,
            task_id=artifact.task_id,
            name=artifact.name,
            artifact_type=artifact.artifact_type,
            version=artifact.version,
            parent_version=artifact.parent_version,
            is_key_version=artifact.is_key_version,
            version_description=artifact.version_description,
            content=artifact.content,
            created_at=artifact.created_at.isoformat()
        )


@router.get("/{task_id}/{artifact_name}/diff", response_model=VersionDiffResponse)
def compare_artifact_versions(
    task_id: str,
    artifact_name: str,
    from_version: str = Query(..., description="起始版本"),
    to_version: str = Query(..., description="目标版本"),
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    对比两个版本

    需要登录。
    """
    with db.get_session() as session:
        version_manager = VersionManager(session)

        try:
            diff_result = version_manager.compare_versions(
                task_id=task_id,
                artifact_name=artifact_name,
                from_version=from_version,
                to_version=to_version
            )

            return VersionDiffResponse(**diff_result)

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )


@router.post("/{task_id}/{artifact_name}/versions/{version}/mark-key", response_model=MessageResponse)
def mark_as_key_version(
    task_id: str,
    artifact_name: str,
    version: str,
    request_data: MarkKeyVersionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    标记为关键版本

    需要登录。
    """
    with db.get_session() as session:
        version_manager = VersionManager(session)

        success = version_manager.mark_as_key_version(
            task_id=task_id,
            artifact_name=artifact_name,
            version=version,
            description=request_data.description
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="版本不存在"
            )

        return MessageResponse(message=f"版本 {version} 已标记为关键版本")


@router.post("/{task_id}/{artifact_name}/rollback", response_model=ArtifactVersionResponse)
def rollback_artifact_version(
    task_id: str,
    artifact_name: str,
    rollback_data: RollbackRequest,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    回滚到指定版本

    需要登录。
    """
    with db.get_session() as session:
        version_manager = VersionManager(session)

        try:
            new_artifact = version_manager.rollback_to_version(
                task_id=task_id,
                artifact_name=artifact_name,
                target_version=rollback_data.target_version
            )

            return ArtifactVersionResponse(
                id=new_artifact.id,
                task_id=new_artifact.task_id,
                name=new_artifact.name,
                artifact_type=new_artifact.artifact_type,
                version=new_artifact.version,
                parent_version=new_artifact.parent_version,
                is_key_version=new_artifact.is_key_version,
                version_description=new_artifact.version_description,
                content=new_artifact.content,
                created_at=new_artifact.created_at.isoformat()
            )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )


@router.delete("/{task_id}/{artifact_name}/cleanup", response_model=MessageResponse)
def cleanup_old_versions(
    task_id: str,
    artifact_name: str,
    keep_days: int = Query(30, ge=1, le=365, description="保留天数"),
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    清理旧版本

    保留关键版本和最近N天的版本。需要登录。
    """
    with db.get_session() as session:
        version_manager = VersionManager(session)

        deleted_count = version_manager.cleanup_old_versions(
            task_id=task_id,
            artifact_name=artifact_name,
            keep_days=keep_days
        )

        return MessageResponse(message=f"已清理 {deleted_count} 个旧版本")
