"""
Database Models using SQLAlchemy ORM
多用户多项目人机协作系统的数据模型
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    JSON, Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


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


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    owned_projects = relationship("Project", back_populates="owner", foreign_keys="Project.created_by")
    project_memberships = relationship("ProjectMember", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Project(Base):
    """项目表"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    owner = relationship("User", back_populates="owned_projects", foreign_keys=[created_by])
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"


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
    metadata = Column(JSON, default=dict)
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
    current_agent = Column(String(50))
    artifacts = Column(JSON, default=dict)  # 存储各阶段产物
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    session = relationship("Session", back_populates="tasks")
    events = relationship("TaskEvent", back_populates="task", cascade="all, delete-orphan")
    decisions = relationship("PendingDecision", back_populates="task", cascade="all, delete-orphan")

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
