"""
备份API路由

端点：
- POST /backup/create - 创建备份
- GET /backup/list - 列出备份
- GET /backup/{backup_id}/verify - 验证备份
- POST /backup/{backup_id}/restore - 恢复备份
- DELETE /backup/cleanup - 清理旧备份
- GET /backup/schedule - 获取调度信息
- POST /backup/schedule/trigger - 手动触发备份
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel

from ..database.models import User
from ..backup.backup_manager import backup_manager, BackupType, BackupRecord
from ..backup.scheduler import backup_scheduler
from .schemas import MessageResponse
from .auth import get_current_active_user

router = APIRouter(prefix="/backup", tags=["数据备份"])


class CreateBackupRequest(BaseModel):
    """创建备份请求"""
    backup_type: str = "full"  # full 或 incremental
    include_redis: bool = True
    include_files: bool = True


class BackupResponse(BaseModel):
    """备份响应"""
    backup_id: str
    backup_type: str
    timestamp: str
    file_path: str
    file_size: int
    checksum: str
    status: str


class RestoreBackupRequest(BaseModel):
    """恢复备份请求"""
    target_db: Optional[str] = None


class TriggerBackupRequest(BaseModel):
    """触发备份请求"""
    backup_type: str = "full"


@router.post("/create", response_model=BackupResponse)
def create_backup(
    request: CreateBackupRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    创建备份

    需要SuperAdmin权限。
    """
    # TODO: 检查SuperAdmin权限

    try:
        # 解析备份类型
        backup_type = BackupType(request.backup_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的备份类型: {request.backup_type}"
        )

    try:
        record = backup_manager.create_backup(
            backup_type=backup_type,
            include_redis=request.include_redis,
            include_files=request.include_files
        )

        return BackupResponse(**record.to_dict())

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建备份失败: {str(e)}"
        )


@router.get("/list", response_model=List[BackupResponse])
def list_backups(
    backup_type: Optional[str] = Query(None, description="备份类型"),
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
    current_user: User = Depends(get_current_active_user)
):
    """
    列出备份

    需要登录。
    """
    # 解析备份类型
    backup_type_enum = None
    if backup_type:
        try:
            backup_type_enum = BackupType(backup_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的备份类型: {backup_type}"
            )

    records = backup_manager.list_backups(
        backup_type=backup_type_enum,
        limit=limit
    )

    return [BackupResponse(**r.to_dict()) for r in records]


@router.get("/{backup_id}/verify")
def verify_backup(
    backup_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    验证备份

    需要登录。
    """
    is_valid = backup_manager.verify_backup(backup_id)

    return {
        "backup_id": backup_id,
        "is_valid": is_valid
    }


@router.post("/{backup_id}/restore", response_model=MessageResponse)
def restore_backup(
    backup_id: str,
    request: RestoreBackupRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    恢复备份

    需要SuperAdmin权限。
    """
    # TODO: 检查SuperAdmin权限

    success = backup_manager.restore_backup(
        backup_id=backup_id,
        target_db=request.target_db
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="恢复备份失败"
        )

    return MessageResponse(message=f"备份 {backup_id} 已恢复")


@router.delete("/cleanup", response_model=MessageResponse)
def cleanup_old_backups(
    keep_days: int = Query(30, ge=1, le=365, description="保留天数"),
    current_user: User = Depends(get_current_active_user)
):
    """
    清理旧备份

    需要SuperAdmin权限。
    """
    # TODO: 检查SuperAdmin权限

    deleted = backup_manager.cleanup_old_backups(keep_days=keep_days)

    return MessageResponse(message=f"已删除 {deleted} 个旧备份")


@router.get("/schedule")
def get_schedule_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取调度信息

    需要登录。
    """
    next_run_times = backup_scheduler.get_next_run_times()

    return {
        "scheduler_running": backup_scheduler.scheduler.running,
        "next_run_times": next_run_times
    }


@router.post("/schedule/trigger", response_model=MessageResponse)
def trigger_backup(
    request: TriggerBackupRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    手动触发备份

    需要SuperAdmin权限。
    """
    # TODO: 检查SuperAdmin权限

    try:
        backup_type = BackupType(request.backup_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的备份类型: {request.backup_type}"
        )

    backup_scheduler.trigger_backup(backup_type)

    return MessageResponse(message=f"已触发 {backup_type.value} 备份")
