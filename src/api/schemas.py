"""
API数据模型 - Pydantic Schemas

定义API的请求和响应模型，用于：
1. 数据验证
2. API文档生成
3. 类型提示

为什么使用Pydantic：
- 自动数据验证
- 自动生成OpenAPI文档
- 类型安全
- 易于序列化/反序列化
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== 枚举类型 ====================

class OrganizationRoleEnum(str, Enum):
    """组织角色"""
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    ORG_MEMBER = "org_member"
    ORG_VIEWER = "org_viewer"


class UserRoleEnum(str, Enum):
    """用户角色"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class SessionStatusEnum(str, Enum):
    """会话状态"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatusEnum(str, Enum):
    """任务状态"""
    CREATED = "created"
    IN_REQUIREMENT = "in_requirement"
    IN_DESIGN = "in_design"
    IN_DEVELOPMENT = "in_development"
    IN_REVIEW = "in_review"
    IN_TESTING = "in_testing"
    IN_DEPLOYMENT = "in_deployment"
    COMPLETED = "completed"
    REJECTED = "rejected"


# ==================== 用户相关 ====================

class UserCreate(BaseModel):
    """创建用户请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, description="密码")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ==================== 项目相关 ====================

class ProjectCreate(BaseModel):
    """创建项目请求"""
    name: str = Field(..., min_length=1, max_length=100, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    organization_id: int = Field(..., description="所属组织ID")


class ProjectUpdate(BaseModel):
    """更新项目请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    """项目响应"""
    id: int
    name: str
    description: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectMemberAdd(BaseModel):
    """添加项目成员请求"""
    user_id: int = Field(..., description="用户ID")
    role: UserRoleEnum = Field(UserRoleEnum.MEMBER, description="角色")


class ProjectMemberResponse(BaseModel):
    """项目成员响应"""
    id: int
    user_id: int
    role: UserRoleEnum
    joined_at: datetime

    class Config:
        from_attributes = True


# ==================== 会话相关 ====================

class SessionCreate(BaseModel):
    """创建会话请求"""
    project_id: int = Field(..., description="项目ID")
    meta_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")


class SessionResponse(BaseModel):
    """会话响应"""
    id: str
    project_id: int
    status: SessionStatusEnum
    meta_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 任务相关 ====================

class TaskCreate(BaseModel):
    """创建任务请求"""
    session_id: str = Field(..., description="会话ID")
    title: str = Field(..., min_length=1, max_length=200, description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")


class TaskResponse(BaseModel):
    """任务响应"""
    id: str
    session_id: str
    title: str
    description: Optional[str]
    status: TaskStatusEnum
    current_agent: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskEventResponse(BaseModel):
    """任务事件响应"""
    id: int
    task_id: str
    agent_name: str
    agent_type: str
    event_type: str
    content: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class ArtifactResponse(BaseModel):
    """产物响应"""
    id: int
    task_id: str
    artifact_type: str
    name: str
    content: Optional[str]
    meta_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 工作流执行 ====================

class WorkflowExecuteRequest(BaseModel):
    """执行工作流请求"""
    agents: List[str] = Field(..., description="Agent列表", example=["RequirementAnalyst", "Developer", "CodeReviewer"])
    max_iterations: int = Field(5, ge=1, le=10, description="最大迭代次数")
    llm_config: Optional[Dict[str, Any]] = Field(None, description="LLM配置")


class WorkflowExecuteResponse(BaseModel):
    """执行工作流响应"""
    success: bool
    message: str
    final_status: str
    iteration_count: Dict[str, int] = {}
    artifacts_count: int = 0


class HumanMessageRequest(BaseModel):
    """人工消息请求"""
    content: str = Field(..., description="消息内容")
    mentioned_agents: List[str] = Field(default_factory=list, description="@提及的Agent列表")
    action: str = Field("continue", description="操作类型: continue/cancel/retry")


class CeleryTaskStatusResponse(BaseModel):
    """Celery任务状态响应"""
    celery_task_id: str
    state: str
    ready: bool
    successful: Optional[bool] = None
    failed: Optional[bool] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None


# ==================== 决策相关 ====================

class DecisionResponse(BaseModel):
    """决策响应"""
    id: int
    task_id: str
    agent_name: str
    decision_type: str
    context: Dict[str, Any]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DecisionResolve(BaseModel):
    """解决决策请求"""
    response: Dict[str, Any] = Field(..., description="决策结果")


# ==================== 通用响应 ====================

class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


# ==================== 组织管理 ====================

class OrganizationCreate(BaseModel):
    """创建组织请求"""
    name: str = Field(..., min_length=1, max_length=100, description="组织名称")
    slug: str = Field(..., min_length=1, max_length=50, description="URL友好标识符")
    description: Optional[str] = Field(None, description="组织描述")
    token_quota: int = Field(1000000, ge=0, description="Token配额")
    max_projects: int = Field(10, ge=1, description="最大项目数")
    max_members: int = Field(50, ge=1, description="最大成员数")


class OrganizationUpdate(BaseModel):
    """更新组织请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    token_quota: Optional[int] = Field(None, ge=0)
    max_projects: Optional[int] = Field(None, ge=1)
    max_members: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class OrganizationResponse(BaseModel):
    """组织响应"""
    id: int
    name: str
    slug: str
    description: Optional[str]
    token_quota: int
    token_used: int
    max_projects: int
    max_members: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizationQuotaResponse(BaseModel):
    """组织配额响应"""
    token_quota: int
    token_used: int
    token_remaining: int
    usage_percentage: float
    max_projects: int
    current_projects: int
    max_members: int
    current_members: int


class OrganizationMemberAdd(BaseModel):
    """添加组织成员请求"""
    user_id: int = Field(..., description="用户ID")
    role: OrganizationRoleEnum = Field(OrganizationRoleEnum.ORG_MEMBER, description="角色")


class OrganizationMemberUpdate(BaseModel):
    """更新组织成员请求"""
    role: OrganizationRoleEnum = Field(..., description="新角色")


class OrganizationMemberResponse(BaseModel):
    """组织成员响应"""
    id: int
    organization_id: int
    user_id: int
    role: str
    joined_at: datetime
    user: Optional[Dict[str, Any]] = None  # 用户信息

    class Config:
        from_attributes = True


# ==================== 审计日志 ====================

class AuditLogResponse(BaseModel):
    """审计日志响应"""
    id: int
    action: str
    resource_type: str
    resource_id: str
    user_id: Optional[int]
    username: Optional[str]
    organization_id: Optional[int]
    ip_address: Optional[str]
    user_agent: Optional[str]
    details: Dict[str, Any]
    status: str
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListRequest(BaseModel):
    """审计日志查询请求"""
    user_id: Optional[int] = Field(None, description="用户ID")
    organization_id: Optional[int] = Field(None, description="组织ID")
    resource_type: Optional[str] = Field(None, description="资源类型")
    resource_id: Optional[str] = Field(None, description="资源ID")
    action: Optional[str] = Field(None, description="操作类型")
    status: Optional[str] = Field(None, description="状态")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    limit: int = Field(100, ge=1, le=1000, description="返回数量")
    offset: int = Field(0, ge=0, description="偏移量")


class AuditLogListResponse(BaseModel):
    """审计日志列表响应"""
    total: int
    logs: List[AuditLogResponse]
    limit: int
    offset: int


# ==================== 配额管理 ====================

class QuotaUsageResponse(BaseModel):
    """配额使用响应"""
    id: int
    organization_id: int
    tokens_used: int
    api_calls: int
    resource_type: Optional[str]
    resource_id: Optional[str]
    user_id: Optional[int]
    created_at: datetime
    period: str

    class Config:
        from_attributes = True


class QuotaStatsResponse(BaseModel):
    """配额统计响应"""
    total_tokens: int
    total_calls: int
    record_count: int


class QuotaDailyUsageResponse(BaseModel):
    """每日使用量响应"""
    date: str
    tokens: int
    calls: int


class QuotaInfoResponse(BaseModel):
    """配额信息响应"""
    token_quota: int
    token_used: int
    token_remaining: int
    usage_percentage: float
    is_exceeded: bool


class RateLimitConfigCreate(BaseModel):
    """创建限流配置请求"""
    max_requests: int = Field(..., ge=1, description="最大请求数")
    period: str = Field(..., description="时间周期(second/minute/hour/day)")
    organization_id: Optional[int] = Field(None, description="组织ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    endpoint: Optional[str] = Field(None, description="API端点")


class RateLimitConfigUpdate(BaseModel):
    """更新限流配置请求"""
    max_requests: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class RateLimitConfigResponse(BaseModel):
    """限流配置响应"""
    id: int
    organization_id: Optional[int]
    user_id: Optional[int]
    endpoint: Optional[str]
    max_requests: int
    period: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuotaAlertResponse(BaseModel):
    """配额告警响应"""
    id: int
    organization_id: int
    alert_level: str
    usage_percentage: int
    tokens_used: int
    tokens_quota: int
    message: str
    is_resolved: bool
    resolved_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 通知系统 ====================

class NotificationSendRequest(BaseModel):
    """发送通知请求"""
    notification_type: str = Field(..., description="通知类型")
    channel: str = Field(..., description="通知渠道(email/slack)")
    subject: str = Field(..., description="通知主题")
    content: str = Field(..., description="通知内容")
    organization_id: Optional[int] = Field(None, description="组织ID")
    email_config: Optional[Dict[str, Any]] = Field(None, description="邮件配置")
    slack_config: Optional[Dict[str, Any]] = Field(None, description="Slack配置")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class NotificationConfigCreate(BaseModel):
    """创建通知配置请求"""
    notification_type: str = Field(..., description="通知类型")
    channel: str = Field(..., description="通知渠道")
    is_enabled: bool = Field(True, description="是否启用")
    organization_id: Optional[int] = Field(None, description="组织ID")
    config: Optional[Dict[str, Any]] = Field(None, description="配置信息")


class NotificationConfigUpdate(BaseModel):
    """更新通知配置请求"""
    is_enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class NotificationConfigResponse(BaseModel):
    """通知配置响应"""
    id: int
    user_id: int
    organization_id: Optional[int]
    notification_type: str
    channel: str
    is_enabled: bool
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationHistoryResponse(BaseModel):
    """通知历史响应"""
    id: int
    user_id: int
    organization_id: Optional[int]
    notification_type: str
    channel: str
    subject: str
    content: str
    status: str
    sent_at: Optional[datetime]
    error_message: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationStatsResponse(BaseModel):
    """通知统计响应"""
    total: int
    by_status: Dict[str, int]
    by_channel: Dict[str, int]
    by_type: Dict[str, int]

