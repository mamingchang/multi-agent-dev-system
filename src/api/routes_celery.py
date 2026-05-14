"""
使用Celery的工作流执行API

提供基于Celery的异步任务执行端点。

优势：
1. 可靠性：任务持久化到Redis
2. 可扩展：支持多worker并行处理
3. 监控：可以查询任务状态和进度
4. 重试：自动重试失败任务
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
import uuid

from ..database.database import Database, SessionRepository, TaskRepository
from ..database.models import User, TaskStatus as DBTaskStatus
from .schemas import (
    TaskCreate, TaskResponse,
    WorkflowExecuteRequest, WorkflowExecuteResponse,
    CeleryTaskStatusResponse
)
from .auth import get_current_active_user, check_project_permission
from .dependencies import get_db

router = APIRouter(prefix="/celery", tags=["Celery任务"])


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_celery_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    创建任务（Celery版本）

    创建任务并返回任务ID，但不立即执行。
    """
    with db.get_session() as session:
        # 验证会话存在并检查权限
        session_repo = SessionRepository(session)
        db_session = session_repo.get_by_id(task_data.session_id)

        if not db_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )

        check_project_permission(current_user, db_session.project_id, db)

        # 创建任务
        task_repo = TaskRepository(session)
        task_id = f"task-{uuid.uuid4().hex[:12]}"

        task = task_repo.create(
            task_id=task_id,
            session_id=task_data.session_id,
            title=task_data.title,
            description=task_data.description
        )

        return TaskResponse(
            id=task.id,
            session_id=task.session_id,
            title=task.title,
            description=task.description,
            status=task.status,
            current_agent=task.current_agent,
            created_at=task.created_at,
            updated_at=task.updated_at
        )


@router.post("/tasks/{task_id}/execute", response_model=WorkflowExecuteResponse)
async def execute_celery_workflow(
    task_id: str,
    execute_request: WorkflowExecuteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    执行工作流（Celery版本）

    将任务提交到Celery队列异步执行。

    返回Celery任务ID，可以用于查询执行状态。
    """
    # 验证任务存在和权限
    with db.get_session() as session:
        task_repo = TaskRepository(session)
        task = task_repo.get_by_id(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )

        # 检查权限
        session_repo = SessionRepository(session)
        db_session = session_repo.get_by_id(task.session_id)
        check_project_permission(current_user, db_session.project_id, db)

        # 检查任务状态
        if task.status != DBTaskStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"任务状态不允许执行: {task.status}"
            )

        # 提交到Celery
        from ..tasks.workflow_tasks import execute_workflow_task

        celery_task = execute_workflow_task.delay(
            task_id=task_id,
            db_url=db.database_url
        )

        # 更新任务状态
        task.status = DBTaskStatus.IN_PROGRESS
        task.meta_data = task.meta_data or {}
        task.meta_data['celery_task_id'] = celery_task.id
        session.commit()

        return WorkflowExecuteResponse(
            task_id=task_id,
            status="submitted",
            message="任务已提交到队列",
            celery_task_id=celery_task.id
        )


@router.get("/tasks/{celery_task_id}/status", response_model=CeleryTaskStatusResponse)
async def get_celery_task_status(
    celery_task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    查询Celery任务状态

    Args:
        celery_task_id: Celery任务ID（不是业务任务ID）

    Returns:
        任务状态信息
    """
    from ..celery_config import celery_app
    from celery.result import AsyncResult

    # 获取任务结果
    result = AsyncResult(celery_task_id, app=celery_app)

    response = {
        'celery_task_id': celery_task_id,
        'state': result.state,
        'ready': result.ready(),
        'successful': result.successful() if result.ready() else None,
        'failed': result.failed() if result.ready() else None
    }

    # 如果任务完成，返回结果
    if result.ready():
        if result.successful():
            response['result'] = result.result
        else:
            response['error'] = str(result.info)
    # 如果任务进行中，返回进度
    elif result.state == 'PROGRESS':
        response['progress'] = result.info

    return CeleryTaskStatusResponse(**response)


@router.post("/tasks/{celery_task_id}/revoke")
async def revoke_celery_task(
    celery_task_id: str,
    terminate: bool = False,
    current_user: User = Depends(get_current_active_user)
):
    """
    撤销Celery任务

    Args:
        celery_task_id: Celery任务ID
        terminate: 是否强制终止（默认False，只是标记为撤销）

    Returns:
        撤销结果
    """
    from ..celery_config import celery_app

    celery_app.control.revoke(celery_task_id, terminate=terminate)

    return {
        'celery_task_id': celery_task_id,
        'status': 'revoked',
        'message': '任务已撤销' if not terminate else '任务已强制终止'
    }


@router.get("/workers/status")
async def get_workers_status(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取Worker状态

    返回所有活跃的Celery worker信息。
    """
    from ..celery_config import celery_app

    # 获取活跃的workers
    inspect = celery_app.control.inspect()

    active_workers = inspect.active()
    registered_tasks = inspect.registered()
    stats = inspect.stats()

    return {
        'active_workers': list(active_workers.keys()) if active_workers else [],
        'worker_count': len(active_workers) if active_workers else 0,
        'registered_tasks': registered_tasks,
        'stats': stats
    }


@router.get("/queue/stats")
async def get_queue_stats(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取队列统计信息

    返回各个队列的任务数量。
    """
    from ..celery_config import celery_app

    inspect = celery_app.control.inspect()

    # 获取队列中的任务
    reserved = inspect.reserved()
    active = inspect.active()
    scheduled = inspect.scheduled()

    return {
        'reserved': reserved,  # 已预留的任务
        'active': active,      # 正在执行的任务
        'scheduled': scheduled  # 已调度的任务
    }
