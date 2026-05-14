"""
数据库操作层 - MVP版本

提供统一的数据库访问接口，封装SQLAlchemy操作。

设计原则：
1. 使用上下文管理器管理会话生命周期
2. 提供简单的CRUD接口
3. 支持SQLite（开发）和PostgreSQL（生产）
4. 自动处理事务和异常

为什么这样设计：
- 上下文管理器：自动管理session的创建和关闭，避免资源泄漏
- 工厂模式：根据配置创建不同的数据库引擎
- 仓储模式：每个实体有对应的Repository类，封装数据访问逻辑
"""

from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os

from .models import Base, User, Project, ProjectMember, Session as DBSession
from .models import Task, TaskEvent, PendingDecision, Artifact
from .models import UserRole, SessionStatus, TaskStatus, DecisionStatus


class Database:
    """
    数据库管理类

    负责：
    1. 数据库引擎的创建和配置
    2. Session工厂的管理
    3. 数据库初始化
    """

    def __init__(self, database_url: str = None, echo: bool = False):
        """
        初始化数据库连接

        Args:
            database_url: 数据库连接URL，默认使用SQLite内存数据库
            echo: 是否打印SQL语句（调试用）
        """
        # 默认使用SQLite内存数据库（适合测试）
        if database_url is None:
            database_url = "sqlite:///:memory:"

        self.database_url = database_url

        # 创建引擎
        # SQLite内存数据库需要特殊配置：
        # - check_same_thread=False: 允许多线程访问
        # - StaticPool: 保持连接不关闭（内存数据库关闭连接后数据会丢失）
        if database_url.startswith("sqlite:///:memory:"):
            self.engine = create_engine(
                database_url,
                echo=echo,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
        else:
            self.engine = create_engine(database_url, echo=echo)

        # 创建Session工厂
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def init_db(self):
        """
        初始化数据库（创建所有表）
        """
        Base.metadata.create_all(bind=self.engine)

    def drop_all(self):
        """
        删除所有表（慎用！仅用于测试）
        """
        Base.metadata.drop_all(bind=self.engine)

    @contextmanager
    def get_session(self):
        """
        获取数据库Session的上下文管理器

        使用方式：
        ```python
        with db.get_session() as session:
            user = session.query(User).first()
        ```

        自动处理：
        - Session的创建和关闭
        - 事务的提交和回滚
        - 异常处理
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


class UserRepository:
    """
    用户数据访问层

    封装User相关的数据库操作
    """

    def __init__(self, session: Session):
        self.session = session

    def create(self, username: str, email: str, password_hash: str,
               full_name: str = None) -> User:
        """创建用户"""
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name
        )
        self.session.add(user)
        self.session.flush()  # 获取自动生成的ID
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return self.session.query(User).filter(User.id == user_id).first()

    def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.session.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return self.session.query(User).filter(User.email == email).first()


class ProjectRepository:
    """
    项目数据访问层
    """

    def __init__(self, session: Session):
        self.session = session

    def create(self, name: str, created_by: int, organization_id: int, description: str = None) -> Project:
        """创建项目"""
        project = Project(
            name=name,
            description=description,
            created_by=created_by,
            organization_id=organization_id
        )
        self.session.add(project)
        self.session.flush()
        return project

    def get_by_id(self, project_id: int) -> Optional[Project]:
        """根据ID获取项目"""
        return self.session.query(Project).filter(Project.id == project_id).first()

    def get_user_projects(self, user_id: int) -> List[Project]:
        """获取用户的所有项目（包括拥有的和参与的）"""
        return self.session.query(Project).join(ProjectMember).filter(
            ProjectMember.user_id == user_id
        ).all()

    def add_member(self, project_id: int, user_id: int,
                   role: UserRole = UserRole.MEMBER) -> ProjectMember:
        """添加项目成员"""
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role
        )
        self.session.add(member)
        self.session.flush()
        return member


class SessionRepository:
    """
    会话数据访问层
    """

    def __init__(self, session: Session):
        self.session = session

    def create(self, session_id: str, project_id: int,
               meta_data: Dict[str, Any] = None) -> DBSession:
        """创建会话"""
        db_session = DBSession(
            id=session_id,
            project_id=project_id,
            status=SessionStatus.ACTIVE,
            meta_data=meta_data or {}
        )
        self.session.add(db_session)
        self.session.flush()
        return db_session

    def get_by_id(self, session_id: str) -> Optional[DBSession]:
        """根据ID获取会话"""
        return self.session.query(DBSession).filter(DBSession.id == session_id).first()

    def get_project_sessions(self, project_id: int) -> List[DBSession]:
        """获取项目的所有会话"""
        return self.session.query(DBSession).filter(
            DBSession.project_id == project_id
        ).order_by(DBSession.created_at.desc()).all()

    def update_status(self, session_id: str, status: SessionStatus):
        """更新会话状态"""
        db_session = self.get_by_id(session_id)
        if db_session:
            db_session.status = status
            self.session.flush()


class TaskRepository:
    """
    任务数据访问层
    """

    def __init__(self, session: Session):
        self.session = session

    def create(self, task_id: str, session_id: str, title: str,
               description: str = None) -> Task:
        """创建任务"""
        task = Task(
            id=task_id,
            session_id=session_id,
            title=title,
            description=description,
            status=TaskStatus.CREATED
        )
        self.session.add(task)
        self.session.flush()
        return task

    def get_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务"""
        return self.session.query(Task).filter(Task.id == task_id).first()

    def get_session_tasks(self, session_id: str) -> List[Task]:
        """获取会话的所有任务"""
        return self.session.query(Task).filter(
            Task.session_id == session_id
        ).order_by(Task.created_at.desc()).all()

    def update_status(self, task_id: str, status: TaskStatus,
                     current_agent: str = None):
        """更新任务状态"""
        task = self.get_by_id(task_id)
        if task:
            task.status = status
            if current_agent:
                task.current_agent = current_agent
            self.session.flush()

    def add_event(self, task_id: str, agent_name: str, agent_type: str,
                  event_type: str, content: Dict[str, Any] = None,
                  created_by_user: int = None) -> TaskEvent:
        """添加任务事件"""
        event = TaskEvent(
            task_id=task_id,
            agent_name=agent_name,
            agent_type=agent_type,
            event_type=event_type,
            content=content or {},
            created_by_user=created_by_user
        )
        self.session.add(event)
        self.session.flush()
        return event

    def add_artifact(self, task_id: str, artifact_type: str, name: str,
                    content: str = None, meta_data: Dict[str, Any] = None,
                    created_by: int = None) -> Artifact:
        """添加任务产物"""
        artifact = Artifact(
            task_id=task_id,
            artifact_type=artifact_type,
            name=name,
            content=content,
            meta_data=meta_data or {},
            created_by=created_by
        )
        self.session.add(artifact)
        self.session.flush()
        return artifact

    def get_task_events(self, task_id: str) -> List[TaskEvent]:
        """获取任务的所有事件"""
        return self.session.query(TaskEvent).filter(
            TaskEvent.task_id == task_id
        ).order_by(TaskEvent.created_at).all()

    def get_task_artifacts(self, task_id: str) -> List[Artifact]:
        """获取任务的所有产物"""
        return self.session.query(Artifact).filter(
            Artifact.task_id == task_id
        ).order_by(Artifact.created_at).all()


class DecisionRepository:
    """
    决策数据访问层
    """

    def __init__(self, session: Session):
        self.session = session

    def create(self, task_id: str, agent_name: str, decision_type: str,
               context: Dict[str, Any] = None, assigned_to: int = None) -> PendingDecision:
        """创建待办决策"""
        decision = PendingDecision(
            task_id=task_id,
            agent_name=agent_name,
            decision_type=decision_type,
            context=context or {},
            assigned_to=assigned_to,
            status=DecisionStatus.PENDING
        )
        self.session.add(decision)
        self.session.flush()
        return decision

    def get_by_id(self, decision_id: int) -> Optional[PendingDecision]:
        """根据ID获取决策"""
        return self.session.query(PendingDecision).filter(
            PendingDecision.id == decision_id
        ).first()

    def get_pending_decisions(self, task_id: str = None,
                             assigned_to: int = None) -> List[PendingDecision]:
        """获取待办决策"""
        query = self.session.query(PendingDecision).filter(
            PendingDecision.status == DecisionStatus.PENDING
        )

        if task_id:
            query = query.filter(PendingDecision.task_id == task_id)

        if assigned_to:
            query = query.filter(PendingDecision.assigned_to == assigned_to)

        return query.order_by(PendingDecision.created_at).all()

    def resolve(self, decision_id: int, response: Dict[str, Any],
                resolved_by: int):
        """解决决策"""
        decision = self.get_by_id(decision_id)
        if decision:
            decision.status = DecisionStatus.RESOLVED
            decision.response = response
            decision.resolved_by = resolved_by
            from datetime import datetime
            decision.resolved_at = datetime.utcnow()
            self.session.flush()


# 便捷函数：创建数据库实例
def create_database(database_url: str = None, echo: bool = False) -> Database:
    """
    创建数据库实例的便捷函数

    Args:
        database_url: 数据库连接URL，默认使用环境变量DATABASE_URL
        echo: 是否打印SQL语句

    Returns:
        Database实例
    """
    if database_url is None:
        database_url = os.getenv("DATABASE_URL", "sqlite:///multi_agent_dev.db")

    return Database(database_url, echo=echo)
