"""
用户体验优化API路由

端点：
- GET /ux/templates - 列出任务模板
- GET /ux/templates/{template_id} - 获取模板详情
- POST /ux/templates - 创建模板
- PUT /ux/templates/{template_id} - 更新模板
- DELETE /ux/templates/{template_id} - 删除模板
- POST /ux/templates/{template_id}/use - 使用模板
- POST /ux/estimate - 预估任务耗时
- POST /ux/estimate/update - 更新预估
- GET /ux/estimate/milestones - 获取里程碑预估
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from ..database.models import User
from ..ux.template_manager import template_manager, TaskTemplate, TemplateCategory, TemplateScope
from ..ux.progress_estimator import progress_estimator
from .auth import get_current_active_user
from .schemas import MessageResponse

router = APIRouter(prefix="/ux", tags=["用户体验"])


class CreateTemplateRequest(BaseModel):
    """创建模板请求"""
    id: str
    name: str
    description: str
    category: str
    title_template: str
    description_template: str
    workflow: List[str]
    tech_stacks: List[str] = []
    estimated_hours: Optional[int] = None
    priority: int = 50
    parameters: Dict[str, Any] = {}
    scope: str = "user"
    tags: List[str] = []


class UseTemplateRequest(BaseModel):
    """使用模板请求"""
    parameters: Dict[str, Any]


class EstimateRequest(BaseModel):
    """预估请求"""
    task_type: str
    workflow: List[str]
    task_description: str = ""


class UpdateEstimateRequest(BaseModel):
    """更新预估请求"""
    task_id: int
    current_progress: float
    elapsed_hours: float
    initial_estimate: float


@router.get("/templates")
def list_templates(
    category: Optional[str] = Query(None, description="分类"),
    scope: Optional[str] = Query(None, description="作用域"),
    tech_stack: Optional[str] = Query(None, description="技术栈"),
    tags: Optional[str] = Query(None, description="标签（逗号分隔）"),
    current_user: User = Depends(get_current_active_user)
):
    """
    列出任务模板

    需要登录。
    """
    # 解析参数
    category_enum = TemplateCategory(category) if category else None
    scope_enum = TemplateScope(scope) if scope else None
    tag_list = tags.split(",") if tags else None

    # 获取模板
    templates = template_manager.list_templates(
        category=category_enum,
        scope=scope_enum,
        tech_stack=tech_stack,
        tags=tag_list
    )

    return {
        "total": len(templates),
        "templates": [t.to_dict() for t in templates]
    }


@router.get("/templates/{template_id}")
def get_template(
    template_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    获取模板详情

    需要登录。
    """
    template = template_manager.get_template(template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板不存在: {template_id}"
        )

    return template.to_dict()


@router.post("/templates")
def create_template(
    request: CreateTemplateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    创建模板

    需要登录。
    """
    # 创建模板
    template = TaskTemplate(
        id=request.id,
        name=request.name,
        description=request.description,
        category=TemplateCategory(request.category),
        title_template=request.title_template,
        description_template=request.description_template,
        workflow=request.workflow,
        tech_stacks=request.tech_stacks,
        estimated_hours=request.estimated_hours,
        priority=request.priority,
        parameters=request.parameters,
        scope=TemplateScope(request.scope),
        scope_id=current_user.id if request.scope == "user" else None,
        author=current_user.username,
        tags=request.tags
    )

    # 添加模板
    success = template_manager.add_template(template)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"模板已存在: {request.id}"
        )

    return {
        "message": "模板创建成功",
        "template": template.to_dict()
    }


@router.put("/templates/{template_id}")
def update_template(
    template_id: str,
    request: CreateTemplateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    更新模板

    需要登录。
    """
    # 检查模板是否存在
    existing = template_manager.get_template(template_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板不存在: {template_id}"
        )

    # 检查权限
    if existing.scope == TemplateScope.USER and existing.scope_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此模板"
        )

    # 更新模板
    template = TaskTemplate(
        id=template_id,
        name=request.name,
        description=request.description,
        category=TemplateCategory(request.category),
        title_template=request.title_template,
        description_template=request.description_template,
        workflow=request.workflow,
        tech_stacks=request.tech_stacks,
        estimated_hours=request.estimated_hours,
        priority=request.priority,
        parameters=request.parameters,
        scope=existing.scope,
        scope_id=existing.scope_id,
        author=existing.author,
        tags=request.tags,
        usage_count=existing.usage_count,
        created_at=existing.created_at
    )

    template_manager.update_template(template)

    return {
        "message": "模板更新成功",
        "template": template.to_dict()
    }


@router.delete("/templates/{template_id}")
def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    删除模板

    需要登录。
    """
    # 检查模板是否存在
    existing = template_manager.get_template(template_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板不存在: {template_id}"
        )

    # 检查权限
    if existing.scope == TemplateScope.USER and existing.scope_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此模板"
        )

    # 删除模板
    template_manager.delete_template(template_id)

    return MessageResponse(message=f"模板 {template_id} 已删除")


@router.post("/templates/{template_id}/use")
def use_template(
    template_id: str,
    request: UseTemplateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    使用模板

    需要登录。
    """
    try:
        task_data = template_manager.use_template(template_id, request.parameters)
        return {
            "message": "模板渲染成功",
            "task_data": task_data
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/estimate")
def estimate_task(
    request: EstimateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    预估任务耗时

    需要登录。
    """
    estimate = progress_estimator.estimate_task_duration(
        task_type=request.task_type,
        workflow=request.workflow,
        task_description=request.task_description
    )

    return estimate


@router.post("/estimate/update")
def update_estimate(
    request: UpdateEstimateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    更新预估

    需要登录。
    """
    estimate = progress_estimator.update_estimate(
        task_id=request.task_id,
        current_progress=request.current_progress,
        elapsed_hours=request.elapsed_hours,
        initial_estimate=request.initial_estimate
    )

    return estimate


@router.get("/estimate/milestones")
def get_milestones(
    workflow: str = Query(..., description="工作流（逗号分隔）"),
    total_estimate: float = Query(..., description="总预估（小时）"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取里程碑预估

    需要登录。
    """
    workflow_list = workflow.split(",")

    milestones = progress_estimator.get_milestone_estimates(
        workflow=workflow_list,
        total_estimate=total_estimate
    )

    return {
        "workflow": workflow_list,
        "total_estimate": total_estimate,
        "milestones": milestones
    }
