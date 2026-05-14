"""
Database Models using SQLAlchemy ORM
多用户多项目多租户人机协作系统的数据模型
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Boolean,
    JSON, Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class OrganizationRole(enum.Enum):
    """组织角色"""
    SUPER_ADMIN = "super_admin"  # 超级管理员（跨组织）
    ORG_ADMIN = "org_admin"      # 组织管理员
    ORG_MEMBER = "org_member"    # 组织成员
    ORG_VIEWER = "org_viewer"    # 组织访客


class UserRole(enum.Enum):
    """项目成员角色"""
    OWNER = "owner"      # 项目所有者
    ADMIN = "admin"      # 管理员
    MEMBER = "member"    # 普通成员
    VIEWER = "viewer"    # 只读访问


class SessionStatus(enum.Enum):
    """会话状态"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(enum.Enum):
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


class DecisionStatus(enum.Enum):
    """决策状态"""
    PENDING = "pending"
    RESOLVED = "resolved"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class AuditAction(enum.Enum):
    """审计操作类型"""
    # 用户操作
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"

    # 组织操作
    ORG_CREATE = "org_create"
    ORG_UPDATE = "org_update"
    ORG_DELETE = "org_delete"
    ORG_MEMBER_ADD = "org_member_add"
    ORG_MEMBER_REMOVE = "org_member_remove"
    ORG_MEMBER_ROLE_UPDATE = "org_member_role_update"

    # 项目操作
    PROJECT_CREATE = "project_create"
    PROJECT_UPDATE = "project_update"
    PROJECT_DELETE = "project_delete"
    PROJECT_MEMBER_ADD = "project_member_add"
    PROJECT_MEMBER_REMOVE = "project_member_remove"

    # 工作流操作
    SESSION_CREATE = "session_create"
    TASK_CREATE = "task_create"
    TASK_EXECUTE = "task_execute"
    TASK_UPDATE = "task_update"

    # 配额操作
    QUOTA_UPDATE = "quota_update"
    TOKEN_USAGE = "token_usage"


class QuotaAlertLevel(enum.Enum):
    """配额告警级别"""
    WARNING = "warning"      # 警告（80%）
    CRITICAL = "critical"    # 严重（90%）
    EXCEEDED = "exceeded"    # 超限（100%）


class RateLimitPeriod(enum.Enum):
    """限流周期"""
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


class NotificationType(enum.Enum):
    """通知类型"""
    QUOTA_ALERT = "quota_alert"           # 配额告警
    TASK_COMPLETED = "task_completed"     # 任务完成
    TASK_FAILED = "task_failed"           # 任务失败
    APPROVAL_REQUEST = "approval_request" # 审批请求
    SYSTEM_ALERT = "system_alert"         # 系统告警
    MEMBER_ADDED = "member_added"         # 成员添加
    MEMBER_REMOVED = "member_removed"     # 成员移除


class NotificationChannel(enum.Enum):
    """通知渠道"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"


class NotificationStatus(enum.Enum):
    """通知状态"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


class Organization(Base):
    """组织表（多租户）"""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(50), unique=True, nullable=False, index=True)  # URL友好的标识符
    description = Column(Text)

    # 配额设置
    token_quota = Column(Integer, default=1000000)  # Token总配额
    token_used = Column(Integer, default=0)  # 已使用Token
    max_projects = Column(Integer, default=10)  # 最大项目数
    max_members = Column(Integer, default=50)  # 最大成员数
    max_concurrent_tasks = Column(Integer, default=3)  # 最大并发任务数

    # 状态
    is_active = Column(Boolean, default=True)  # 是否激活

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="organization", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}', slug='{self.slug}')>"


class OrganizationMember(Base):
    """组织成员关系表"""
    __tablename__ = "organization_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(SQLEnum(OrganizationRole), default=OrganizationRole.ORG_MEMBER, nullable=False)

    # 时间戳
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 唯一约束：一个用户在一个组织中只能有一个角色
    __table_args__ = (
        UniqueConstraint('organization_id', 'user_id', name='uq_org_user'),
        Index('idx_org_member_org', 'organization_id'),
        Index('idx_org_member_user', 'user_id'),
    )

    # 关系
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="organization_memberships")

    def __repr__(self):
        return f"<OrganizationMember(org_id={self.organization_id}, user_id={self.user_id}, role={self.role.value})>"


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))

    # 全局角色（可选，用于跨组织管理）
    global_role = Column(SQLEnum(OrganizationRole), default=OrganizationRole.ORG_MEMBER)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    organization_memberships = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")
    owned_projects = relationship("Project", back_populates="owner", foreign_keys="Project.created_by")
    project_memberships = relationship("ProjectMember", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Project(Base):
    """项目表"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)  # 数据隔离关键
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 代码仓库相关字段
    code_path = Column(String(500))  # 项目代码存储路径
    repo_url = Column(String(500))   # Git仓库URL（如果是导入的）
    repo_branch = Column(String(100))  # Git分支
    project_type = Column(String(50), default="manual")  # 项目类型：manual(手动创建) / imported(导入)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 索引：组织ID用于数据隔离查询
    __table_args__ = (
        Index('idx_project_org', 'organization_id'),
    )

    # 关系
    organization = relationship("Organization", back_populates="projects")
    owner = relationship("User", back_populates="owned_projects", foreign_keys=[created_by])
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', org_id={self.organization_id})>"


class ProjectMember(Base):
    """项目成员关系表"""
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.MEMBER)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")

    # 约束：同一用户在同一项目中只能有一个角色
    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='uq_project_user'),
        Index('idx_project_member', 'project_id', 'user_id'),
    )

    def __repr__(self):
        return f"<ProjectMember(project_id={self.project_id}, user_id={self.user_id}, role={self.role.value})>"


class Session(Base):
    """会话表"""
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)  # UUID
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    status = Column(SQLEnum(SessionStatus), nullable=False, default=SessionStatus.ACTIVE)
    meta_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    project = relationship("Project", back_populates="sessions")
    tasks = relationship("Task", back_populates="session", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index('idx_session_project', 'project_id'),
        Index('idx_session_status', 'status'),
    )

    def __repr__(self):
        return f"<Session(id='{self.id}', project_id={self.project_id}, status={self.status.value})>"


class Task(Base):
    """任务表"""
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True)  # UUID
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(TaskStatus), nullable=False, default=TaskStatus.CREATED)
    priority = Column(Integer, default=50)  # 优先级（0-100），默认50
    current_agent = Column(String(50))
    artifacts = Column(JSON, default=dict)  # 存储各阶段产物
    error_message = Column(Text, nullable=True)  # 错误信息
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    session = relationship("Session", back_populates="tasks")
    events = relationship("TaskEvent", back_populates="task", cascade="all, delete-orphan")
    decisions = relationship("PendingDecision", back_populates="task", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="task", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index('idx_task_session', 'session_id'),
        Index('idx_task_status', 'status'),
    )

    def __repr__(self):
        return f"<Task(id='{self.id}', title='{self.title}', status={self.status.value})>"


class TaskEvent(Base):
    """任务事件日志表"""
    __tablename__ = "task_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    agent_name = Column(String(50), nullable=False)
    agent_type = Column(String(20), nullable=False)  # 'ai' or 'human'
    event_type = Column(String(50), nullable=False)  # 'start', 'complete', 'artifact', 'feedback', 'decision'
    content = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by_user = Column(Integer, ForeignKey("users.id"), nullable=True)  # 人工操作时记录用户

    # 关系
    task = relationship("Task", back_populates="events")
    user = relationship("User")

    # 索引
    __table_args__ = (
        Index('idx_event_task', 'task_id'),
        Index('idx_event_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<TaskEvent(id={self.id}, task_id='{self.task_id}', event_type='{self.event_type}')>"


class PendingDecision(Base):
    """待办决策表"""
    __tablename__ = "pending_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    agent_name = Column(String(50), nullable=False)
    decision_type = Column(String(50), nullable=False)  # 'approval', 'review', 'input'
    context = Column(JSON, default=dict)  # 决策上下文信息
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)  # 指定处理人
    status = Column(SQLEnum(DecisionStatus), nullable=False, default=DecisionStatus.PENDING)
    response = Column(JSON, default=dict)  # 决策结果
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 关系
    task = relationship("Task", back_populates="decisions")
    assignee = relationship("User", foreign_keys=[assigned_to])
    resolver = relationship("User", foreign_keys=[resolved_by])

    # 索引
    __table_args__ = (
        Index('idx_decision_task', 'task_id'),
        Index('idx_decision_status', 'status'),
        Index('idx_decision_assigned', 'assigned_to'),
    )

    def __repr__(self):
        return f"<PendingDecision(id={self.id}, task_id='{self.task_id}', status={self.status.value})>"


class Artifact(Base):
    """任务产物表"""
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    artifact_type = Column(String(50), nullable=False)  # 'code', 'document', 'test', 'config'
    name = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)

    # 版本管理
    version = Column(String(50), nullable=False)  # 版本号，如 v20260509_143022
    parent_version = Column(String(50), nullable=True)  # 父版本号
    is_key_version = Column(Boolean, default=False)  # 是否为关键版本
    version_description = Column(Text, nullable=True)  # 版本描述

    meta_data = Column(JSON, default=dict)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    task = relationship("Task", back_populates="artifacts")
    creator = relationship("User")

    # 索引
    __table_args__ = (
        Index('idx_artifact_task', 'task_id'),
        Index('idx_artifact_type', 'artifact_type'),
        Index('idx_artifact_version', 'version'),
        Index('idx_artifact_key_version', 'is_key_version'),
    )

    def __repr__(self):
        return f"<Artifact(id={self.id}, name='{self.name}', version={self.version})>"


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 操作信息
    action = Column(SQLEnum(AuditAction), nullable=False)
    resource_type = Column(String(50), nullable=False)  # 'organization', 'project', 'task', 'user'
    resource_id = Column(String(100), nullable=False)  # 资源ID（可能是int或uuid）

    # 用户信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 执行操作的用户
    username = Column(String(50), nullable=True)  # 冗余存储，防止用户删除后无法追溯

    # 组织信息（用于多租户数据隔离）
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    # 请求信息
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(String(500), nullable=True)

    # 操作详情
    details = Column(JSON, default=dict)  # 操作前后的数据变化、额外信息
    status = Column(String(20), default="success")  # 'success', 'failed', 'error'
    error_message = Column(Text, nullable=True)  # 失败时的错误信息

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 关系
    user = relationship("User")
    organization = relationship("Organization")

    # 索引（用于高效查询）
    __table_args__ = (
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_org', 'organization_id'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_created', 'created_at'),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action.value}, user={self.username}, resource={self.resource_type}:{self.resource_id})>"


class QuotaUsage(Base):
    """配额使用记录表"""
    __tablename__ = "quota_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 组织信息
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # 使用信息
    tokens_used = Column(Integer, default=0, nullable=False)  # 本次使用的Token数
    api_calls = Column(Integer, default=1, nullable=False)    # API调用次数

    # 资源信息
    resource_type = Column(String(50), nullable=True)  # 'task', 'session', 'workflow'
    resource_id = Column(String(100), nullable=True)   # 资源ID

    # 用户信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    period = Column(String(20), nullable=False)  # 'daily', 'monthly' - 用于统计周期

    # 关系
    organization = relationship("Organization")
    user = relationship("User")

    # 索引
    __table_args__ = (
        Index('idx_quota_org', 'organization_id'),
        Index('idx_quota_user', 'user_id'),
        Index('idx_quota_period', 'period', 'created_at'),
    )

    def __repr__(self):
        return f"<QuotaUsage(id={self.id}, org_id={self.organization_id}, tokens={self.tokens_used})>"


class RateLimitConfig(Base):
    """限流配置表"""
    __tablename__ = "rate_limit_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 限流目标
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)  # 组织级限流
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)                  # 用户级限流

    # 限流规则
    endpoint = Column(String(200), nullable=True)  # API端点（null表示全局）
    max_requests = Column(Integer, nullable=False)  # 最大请求数
    period = Column(SQLEnum(RateLimitPeriod), nullable=False)  # 时间周期

    # 状态
    is_active = Column(Boolean, default=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    organization = relationship("Organization")
    user = relationship("User")

    # 索引
    __table_args__ = (
        Index('idx_ratelimit_org', 'organization_id'),
        Index('idx_ratelimit_user', 'user_id'),
    )

    def __repr__(self):
        return f"<RateLimitConfig(id={self.id}, max={self.max_requests}/{self.period.value})>"


class QuotaAlert(Base):
    """配额告警记录表"""
    __tablename__ = "quota_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 组织信息
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # 告警信息
    alert_level = Column(SQLEnum(QuotaAlertLevel), nullable=False)
    usage_percentage = Column(Integer, nullable=False)  # 使用百分比
    tokens_used = Column(Integer, nullable=False)
    tokens_quota = Column(Integer, nullable=False)

    # 告警消息
    message = Column(Text, nullable=False)

    # 是否已处理
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 关系
    organization = relationship("Organization")

    # 索引
    __table_args__ = (
        Index('idx_alert_org', 'organization_id'),
        Index('idx_alert_level', 'alert_level'),
        Index('idx_alert_resolved', 'is_resolved'),
    )

    def __repr__(self):
        return f"<QuotaAlert(id={self.id}, org_id={self.organization_id}, level={self.alert_level.value}, usage={self.usage_percentage}%)>"


class NotificationConfig(Base):
    """通知配置表"""
    __tablename__ = "notification_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 用户/组织
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    # 通知渠道配置
    channel = Column(SQLEnum(NotificationChannel), nullable=False)

    # 渠道配置（JSON）
    config = Column(JSON, default=dict)  # email: {smtp_host, smtp_port, ...}, slack: {webhook_url}

    # 通知类型开关
    enabled_types = Column(JSON, default=list)  # ['quota_alert', 'task_completed', ...]

    # 状态
    is_active = Column(Boolean, default=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User")
    organization = relationship("Organization")

    # 索引
    __table_args__ = (
        Index('idx_notif_config_user', 'user_id'),
        Index('idx_notif_config_org', 'organization_id'),
    )

    def __repr__(self):
        return f"<NotificationConfig(id={self.id}, channel={self.channel.value}, active={self.is_active})>"


class NotificationHistory(Base):
    """通知历史表"""
    __tablename__ = "notification_history"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 接收者
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    # 通知信息
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    channel = Column(SQLEnum(NotificationChannel), nullable=False)

    # 内容
    subject = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    extra_data = Column(JSON, default=dict)  # 额外信息（避免与SQLAlchemy的metadata冲突）

    # 状态
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)

    # 关系
    user = relationship("User")
    organization = relationship("Organization")

    # 索引
    __table_args__ = (
        Index('idx_notif_history_user', 'user_id'),
        Index('idx_notif_history_org', 'organization_id'),
        Index('idx_notif_history_type', 'notification_type'),
        Index('idx_notif_history_status', 'status'),
    )

    def __repr__(self):
        return f"<NotificationHistory(id={self.id}, type={self.notification_type.value}, status={self.status.value})>"


# ============================================================================
# IM群聊系统模型
# ============================================================================

class IMGroup(Base):
    """IM群组表"""
    __tablename__ = "im_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 群组信息
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    group_type = Column(String(20), nullable=False)  # 'project', 'task', 'direct'
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # 创建信息
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    project = relationship("Project")
    creator = relationship("User")
    members = relationship("IMGroupMember", back_populates="group")
    messages = relationship("IMMessage", back_populates="group")

    # 索引
    __table_args__ = (
        Index('idx_im_group_project', 'project_id'),
        Index('idx_im_group_type', 'group_type'),
    )

    def __repr__(self):
        return f"<IMGroup(id={self.id}, name='{self.name}', type={self.group_type})>"


class IMGroupMember(Base):
    """IM群组成员表"""
    __tablename__ = "im_group_members"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联
    group_id = Column(Integer, ForeignKey("im_groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 角色
    role = Column(String(20), nullable=False)  # 'owner', 'admin', 'member', 'observer'

    # 加入信息
    added_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    group = relationship("IMGroup", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    adder = relationship("User", foreign_keys=[added_by])

    # 索引和约束
    __table_args__ = (
        UniqueConstraint('group_id', 'user_id', name='uq_group_member'),
        Index('idx_im_member_group', 'group_id'),
        Index('idx_im_member_user', 'user_id'),
    )

    def __repr__(self):
        return f"<IMGroupMember(group_id={self.group_id}, user_id={self.user_id}, role={self.role})>"


class IMThread(Base):
    """IM线程表（任务讨论线程）"""
    __tablename__ = "im_threads"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    parent_group_id = Column(Integer, ForeignKey("im_groups.id"), nullable=True)

    # 线程信息
    name = Column(String(100), nullable=False)

    # 创建信息
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    task = relationship("Task")
    parent_group = relationship("IMGroup")
    creator = relationship("User")
    messages = relationship("IMMessage", back_populates="thread")

    # 索引
    __table_args__ = (
        Index('idx_im_thread_task', 'task_id'),
        Index('idx_im_thread_parent', 'parent_group_id'),
    )

    def __repr__(self):
        return f"<IMThread(id={self.id}, task_id={self.task_id}, name='{self.name}')>"


class IMMessage(Base):
    """IM消息表"""
    __tablename__ = "im_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 发送者
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 目标（群组或线程）
    group_id = Column(Integer, ForeignKey("im_groups.id"), nullable=True)
    thread_id = Column(Integer, ForeignKey("im_threads.id"), nullable=True)

    # 消息内容
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")  # 'text', 'image', 'file', 'code', 'system'
    extra_data = Column(JSON, default=dict)  # 附加信息（文件URL、代码语言等）

    # 回复关系
    reply_to = Column(Integer, ForeignKey("im_messages.id"), nullable=True)

    # 时间戳
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 关系
    sender = relationship("User")
    group = relationship("IMGroup", back_populates="messages")
    thread = relationship("IMThread", back_populates="messages")
    mentions = relationship("IMMention", back_populates="message")
    read_records = relationship("IMMessageRead", back_populates="message")

    # 索引
    __table_args__ = (
        Index('idx_im_message_sender', 'sender_id'),
        Index('idx_im_message_group', 'group_id'),
        Index('idx_im_message_thread', 'thread_id'),
        Index('idx_im_message_sent_at', 'sent_at'),
    )

    def __repr__(self):
        return f"<IMMessage(id={self.id}, sender_id={self.sender_id}, type={self.message_type})>"


class IMMention(Base):
    """IM @提及表"""
    __tablename__ = "im_mentions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联
    message_id = Column(Integer, ForeignKey("im_messages.id"), nullable=False)
    mentioned_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mentioned_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 状态
    is_read = Column(Boolean, default=False)

    # 时间戳
    mentioned_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    message = relationship("IMMessage", back_populates="mentions")
    mentioned_user = relationship("User", foreign_keys=[mentioned_user_id])
    mentioner = relationship("User", foreign_keys=[mentioned_by])

    # 索引
    __table_args__ = (
        Index('idx_im_mention_message', 'message_id'),
        Index('idx_im_mention_user', 'mentioned_user_id'),
        Index('idx_im_mention_read', 'is_read'),
    )

    def __repr__(self):
        return f"<IMMention(id={self.id}, message_id={self.message_id}, user_id={self.mentioned_user_id})>"


class IMMessageRead(Base):
    """IM消息已读记录表"""
    __tablename__ = "im_message_reads"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联
    message_id = Column(Integer, ForeignKey("im_messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 时间戳
    read_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    message = relationship("IMMessage", back_populates="read_records")
    user = relationship("User")

    # 索引和约束
    __table_args__ = (
        UniqueConstraint('message_id', 'user_id', name='uq_message_read'),
        Index('idx_im_read_message', 'message_id'),
        Index('idx_im_read_user', 'user_id'),
    )

    def __repr__(self):
        return f"<IMMessageRead(message_id={self.message_id}, user_id={self.user_id})>"


class InterventionRequest(Base):
    """人工介入请求表"""
    __tablename__ = "intervention_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    agent_name = Column(String(50), nullable=False)

    # 介入级别
    level = Column(String(20), nullable=False)  # 'level_1', 'level_2', 'level_3'

    # 请求信息
    reason = Column(Text, nullable=False)
    context = Column(JSON, default=dict)
    suggested_actions = Column(JSON, default=list)

    # 状态
    status = Column(String(20), default="pending")  # 'pending', 'in_progress', 'resolved', 'cancelled'

    # 分配信息
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, nullable=True)

    # 解决信息
    resolution = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # 时间戳
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 关系
    task = relationship("Task")
    assignee = relationship("User")

    # 索引
    __table_args__ = (
        Index('idx_intervention_task', 'task_id'),
        Index('idx_intervention_status', 'status'),
        Index('idx_intervention_level', 'level'),
    )

    def __repr__(self):
        return f"<InterventionRequest(id={self.id}, task_id={self.task_id}, level={self.level}, status={self.status})>"
