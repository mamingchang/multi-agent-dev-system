"""
Agent扩展API路由

端点：
- GET /agents - 列出所有Agent
- GET /agents/{agent_name} - 获取Agent详情
- POST /agents/register - 注册新Agent
- DELETE /agents/{agent_name} - 注销Agent
- GET /agents/search - 搜索Agent
- POST /agents/workflow/select - 选择工作流
- POST /agents/workflow/adjust - 调整工作流
- POST /agents/workflow/validate - 验证工作流
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel

from ..database.models import User
from ..agents.registry import agent_registry
from ..agents.capability import AgentCapability, AgentScope
from ..agents.workflow_selector import workflow_selector
from .auth import get_current_active_user

router = APIRouter(prefix="/agents", tags=["Agent扩展"])


class RegisterAgentRequest(BaseModel):
    """注册Agent请求"""
    name: str
    display_name: str
    description: str
    version: str
    author: str
    task_types: List[str] = []
    tech_stacks: List[str] = []
    domains: List[str] = []
    required_inputs: List[str] = []
    output_artifacts: List[str] = []
    depends_on: List[str] = []
    config_schema: dict = {}
    default_config: dict = {}
    scope: str = "global"
    scope_id: Optional[int] = None
    tags: List[str] = []


class SelectWorkflowRequest(BaseModel):
    """选择工作流请求"""
    task_description: str
    task_type: str
    project_tech_stack: List[str]
    organization_id: int
    project_id: Optional[int] = None
    user_preference: Optional[List[str]] = None


class AdjustWorkflowRequest(BaseModel):
    """调整工作流请求"""
    current_workflow: List[str]
    current_step: int
    adjustment_type: str  # add/skip/replace
    agent_name: Optional[str] = None
    reason: str = ""


@router.get("")
def list_agents(
    scope: Optional[str] = Query(None, description="作用域"),
    scope_id: Optional[int] = Query(None, description="作用域ID"),
    current_user: User = Depends(get_current_active_user)
):
    """
    列出所有Agent

    需要登录。
    """
    if scope:
        try:
            scope_enum = AgentScope(scope)
            agents = agent_registry.list_by_scope(scope_enum, scope_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的作用域: {scope}"
            )
    else:
        agents = agent_registry.list_all()

    return {
        "total": len(agents),
        "agents": [agent.to_dict() for agent in agents]
    }


@router.get("/{agent_name}")
def get_agent(
    agent_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    获取Agent详情

    需要登录。
    """
    agent = agent_registry.get(agent_name)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent不存在: {agent_name}"
        )

    return agent.to_dict()


@router.post("/register")
def register_agent(
    request: RegisterAgentRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    注册新Agent

    需要SuperAdmin权限。
    """
    # TODO: 检查SuperAdmin权限

    # 创建能力声明
    capability = AgentCapability(
        name=request.name,
        display_name=request.display_name,
        description=request.description,
        version=request.version,
        author=request.author,
        task_types=request.task_types,
        tech_stacks=request.tech_stacks,
        domains=request.domains,
        required_inputs=request.required_inputs,
        output_artifacts=request.output_artifacts,
        depends_on=request.depends_on,
        config_schema=request.config_schema,
        default_config=request.default_config,
        scope=AgentScope(request.scope),
        scope_id=request.scope_id,
        tags=request.tags
    )

    # 注册
    success = agent_registry.register(capability)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agent已存在: {request.name}"
        )

    return {
        "message": f"Agent {request.name} 注册成功",
        "agent": capability.to_dict()
    }


@router.delete("/{agent_name}")
def unregister_agent(
    agent_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    注销Agent

    需要SuperAdmin权限。
    """
    # TODO: 检查SuperAdmin权限

    success = agent_registry.unregister(agent_name)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent不存在: {agent_name}"
        )

    return {"message": f"Agent {agent_name} 已注销"}


@router.get("/search")
def search_agents(
    task_type: Optional[str] = Query(None, description="任务类型"),
    tech_stack: Optional[str] = Query(None, description="技术栈"),
    domain: Optional[str] = Query(None, description="领域"),
    tags: Optional[str] = Query(None, description="标签（逗号分隔）"),
    current_user: User = Depends(get_current_active_user)
):
    """
    搜索Agent

    需要登录。
    """
    tag_list = tags.split(",") if tags else None

    agents = agent_registry.search(
        task_type=task_type,
        tech_stack=tech_stack,
        domain=domain,
        tags=tag_list
    )

    return {
        "total": len(agents),
        "agents": [agent.to_dict() for agent in agents]
    }


@router.post("/workflow/select")
def select_workflow(
    request: SelectWorkflowRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    选择工作流

    需要登录。
    """
    result = workflow_selector.select_workflow(
        task_description=request.task_description,
        task_type=request.task_type,
        project_tech_stack=request.project_tech_stack,
        organization_id=request.organization_id,
        project_id=request.project_id,
        user_preference=request.user_preference
    )

    return result


@router.post("/workflow/adjust")
def adjust_workflow(
    request: AdjustWorkflowRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    调整工作流

    需要登录。
    """
    result = workflow_selector.adjust_workflow(
        current_workflow=request.current_workflow,
        current_step=request.current_step,
        adjustment_type=request.adjustment_type,
        agent_name=request.agent_name,
        reason=request.reason
    )

    return result


@router.post("/workflow/validate")
def validate_workflow(
    workflow: List[str],
    current_user: User = Depends(get_current_active_user)
):
    """
    验证工作流

    需要登录。
    """
    result = agent_registry.validate_workflow(workflow)

    return result


@router.get("/dependency/graph")
def get_dependency_graph(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取Agent依赖图

    需要登录。
    """
    graph = agent_registry.get_dependency_graph()

    return {"graph": graph}
