"""
工作流与数据库集成层

将内存中的Task对象与数据库同步，实现：
1. Task创建时自动保存到数据库
2. Agent处理时自动记录事件
3. 产物生成时自动保存
4. 状态变更时自动更新

设计原则：
- 透明集成：对现有代码影响最小
- 可选持久化：可以选择是否启用数据库
- 自动同步：关键操作自动触发数据库写入

为什么这样设计：
- 装饰器模式：在不修改原有Task类的情况下增加持久化功能
- 观察者模式：Task状态变化时自动通知数据库层
- 适配器模式：将内存对象转换为数据库对象
"""

from typing import Optional, Dict, Any
from datetime import datetime

from ..workflow.task import Task as MemoryTask, TaskStatus as MemoryTaskStatus
from ..database.database import Database, TaskRepository, SessionRepository
from ..database.models import TaskStatus as DBTaskStatus


class PersistentTask:
    """
    持久化Task包装器

    包装内存Task对象，自动同步到数据库。
    使用装饰器模式，对外接口与Task一致。
    """

    def __init__(self, task: MemoryTask, db: Database, session_id: str):
        """
        初始化持久化Task

        Args:
            task: 内存Task对象
            db: 数据库实例
            session_id: 所属会话ID
        """
        self._task = task
        self._db = db
        self._session_id = session_id

        # 初始化时保存到数据库
        self._save_to_db()

    def _save_to_db(self):
        """保存Task到数据库"""
        with self._db.get_session() as session:
            task_repo = TaskRepository(session)

            # 检查是否已存在
            existing = task_repo.get_by_id(self._task.task_id)
            if not existing:
                # 创建新任务
                task_repo.create(
                    task_id=self._task.task_id,
                    session_id=self._session_id,
                    title=self._task.title,
                    description=self._task.description
                )

    def _update_status_in_db(self, status: MemoryTaskStatus, current_agent: str = None):
        """更新数据库中的任务状态"""
        with self._db.get_session() as session:
            task_repo = TaskRepository(session)

            # 转换状态枚举
            db_status = self._convert_status(status)

            task_repo.update_status(
                task_id=self._task.task_id,
                status=db_status,
                current_agent=current_agent
            )

    def _convert_status(self, memory_status: MemoryTaskStatus) -> DBTaskStatus:
        """转换内存状态到数据库状态"""
        status_map = {
            MemoryTaskStatus.CREATED: DBTaskStatus.CREATED,
            MemoryTaskStatus.IN_REQUIREMENT: DBTaskStatus.IN_REQUIREMENT,
            MemoryTaskStatus.IN_DESIGN: DBTaskStatus.IN_DESIGN,
            MemoryTaskStatus.IN_DEVELOPMENT: DBTaskStatus.IN_DEVELOPMENT,
            MemoryTaskStatus.IN_REVIEW: DBTaskStatus.IN_REVIEW,
            MemoryTaskStatus.IN_TESTING: DBTaskStatus.IN_TESTING,
            MemoryTaskStatus.IN_DEPLOYMENT: DBTaskStatus.IN_DEPLOYMENT,
            MemoryTaskStatus.COMPLETED: DBTaskStatus.COMPLETED,
            MemoryTaskStatus.REJECTED: DBTaskStatus.REJECTED,
        }
        return status_map.get(memory_status, DBTaskStatus.CREATED)

    def add_artifact(self, artifact_type: str, content: Any, agent: str):
        """
        添加产物（同时保存到内存和数据库）

        Args:
            artifact_type: 产物类型
            content: 产物内容
            agent: Agent名称
        """
        # 保存到内存（Task会自动计算version）
        self._task.add_artifact(artifact_type, content, agent)

        # 获取刚添加的产物（最后一个）
        latest_artifact = self._task.artifacts[-1]
        version = latest_artifact['version']

        # 保存到数据库
        with self._db.get_session() as session:
            task_repo = TaskRepository(session)

            task_repo.add_artifact(
                task_id=self._task.task_id,
                artifact_type=artifact_type,
                name=f"{agent}_{artifact_type}_v{version}",
                content=str(content),
                meta_data={
                    "agent": agent,
                    "version": version,
                    "created_at": datetime.now().isoformat()
                }
            )

    def record_event(self, agent_name: str, event_type: str, content: Dict[str, Any] = None):
        """
        记录事件到数据库

        Args:
            agent_name: Agent名称
            event_type: 事件类型（start, complete, artifact, feedback等）
            content: 事件内容
        """
        with self._db.get_session() as session:
            task_repo = TaskRepository(session)

            task_repo.add_event(
                task_id=self._task.task_id,
                agent_name=agent_name,
                agent_type="ai",  # 目前都是AI Agent
                event_type=event_type,
                content=content or {}
            )

    # 代理所有Task的属性和方法
    def __getattr__(self, name):
        """代理访问内存Task的属性"""
        return getattr(self._task, name)

    def __setattr__(self, name, value):
        """拦截属性设置"""
        # 内部属性直接设置
        if name.startswith('_'):
            super().__setattr__(name, value)
            return

        # status属性特殊处理
        if name == 'status':
            # 更新内存
            self._task.status = value
            # 同步到数据库
            self._update_status_in_db(value)
        else:
            # 其他属性直接设置到内存Task
            setattr(self._task, name, value)


class WorkflowSession:
    """
    工作流会话管理器

    管理一个会话中的所有任务，自动处理数据库持久化。
    """

    def __init__(self, session_id: str, project_id: int, db: Database):
        """
        初始化会话

        Args:
            session_id: 会话ID
            project_id: 项目ID
            db: 数据库实例
        """
        self.session_id = session_id
        self.project_id = project_id
        self.db = db

        # 创建会话记录
        with db.get_session() as session:
            session_repo = SessionRepository(session)
            session_repo.create(
                session_id=session_id,
                project_id=project_id,
                meta_data={"created_at": datetime.now().isoformat()}
            )

    def create_task(self, task_id: str, title: str, description: str) -> PersistentTask:
        """
        创建持久化Task

        Args:
            task_id: 任务ID
            title: 任务标题
            description: 任务描述

        Returns:
            PersistentTask: 持久化Task对象
        """
        # 创建内存Task
        memory_task = MemoryTask(task_id, title, description)

        # 包装为持久化Task
        persistent_task = PersistentTask(memory_task, self.db, self.session_id)

        return persistent_task

    def complete(self):
        """完成会话"""
        from ..database.models import SessionStatus

        with self.db.get_session() as session:
            session_repo = SessionRepository(session)
            session_repo.update_status(self.session_id, SessionStatus.COMPLETED)


# 便捷函数
def create_workflow_session(session_id: str, project_id: int,
                            database_url: str = None) -> WorkflowSession:
    """
    创建工作流会话的便捷函数

    Args:
        session_id: 会话ID
        project_id: 项目ID
        database_url: 数据库URL（可选）

    Returns:
        WorkflowSession: 会话管理器
    """
    from ..database.database import create_database

    db = create_database(database_url)
    db.init_db()

    return WorkflowSession(session_id, project_id, db)
