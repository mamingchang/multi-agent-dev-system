"""
工作流执行API路由

端点：
- POST /sessions - 创建会话
- GET /sessions/{session_id} - 获取会话详情
- POST /tasks - 创建任务
- GET /tasks/{task_id} - 获取任务详情
- POST /tasks/{task_id}/execute - 执行工作流
- GET /tasks/{task_id}/events - 获取任务事件
- GET /tasks/{task_id}/artifacts - 获取任务产物
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List
import uuid

from ..database.database import Database, SessionRepository, TaskRepository
from ..database.models import User
from .schemas import (
    SessionCreate, SessionResponse,
    TaskCreate, TaskResponse,
    TaskEventResponse, ArtifactResponse,
    WorkflowExecuteRequest, WorkflowExecuteResponse,
    HumanMessageRequest
)
from .auth import get_current_active_user, check_project_permission
from .dependencies import get_db

router = APIRouter(prefix="/workflow", tags=["工作流"])

# 全局orchestrator管理器：task_id -> orchestrator
active_orchestrators = {}


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    创建会话

    在指定项目下创建新的工作流会话。
    """
    # 检查项目权限
    check_project_permission(current_user, session_data.project_id, db)

    with db.get_session() as session:
        session_repo = SessionRepository(session)

        # 生成会话ID
        session_id = f"session-{uuid.uuid4().hex[:12]}"

        # 创建会话
        db_session = session_repo.create(
            session_id=session_id,
            project_id=session_data.project_id,
            meta_data=session_data.meta_data
        )

        return SessionResponse(
            id=db_session.id,
            project_id=db_session.project_id,
            status=db_session.status,
            meta_data=db_session.meta_data,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at
        )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取会话详情
    """
    with db.get_session() as session:
        session_repo = SessionRepository(session)
        db_session = session_repo.get_by_id(session_id)

        if not db_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )

        # 检查项目权限
        check_project_permission(current_user, db_session.project_id, db)

        return SessionResponse(
            id=db_session.id,
            project_id=db_session.project_id,
            status=db_session.status,
            meta_data=db_session.meta_data,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at
        )


@router.get("/tasks", response_model=List[TaskResponse])
def list_tasks(
    project_id: int = None,
    session_id: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取任务列表

    可以按项目ID或会话ID过滤。
    """
    with db.get_session() as session:
        task_repo = TaskRepository(session)

        if session_id:
            # 按会话ID查询
            session_repo = SessionRepository(session)
            db_session = session_repo.get_by_id(session_id)
            if not db_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="会话不存在"
                )
            check_project_permission(current_user, db_session.project_id, db)
            tasks = task_repo.get_session_tasks(session_id)
        elif project_id:
            # 按项目ID查询
            check_project_permission(current_user, project_id, db)
            # 先获取项目的所有会话
            session_repo = SessionRepository(session)
            sessions = session_repo.get_project_sessions(project_id)
            # 获取所有会话的任务
            tasks = []
            for db_session in sessions:
                session_tasks = task_repo.get_session_tasks(db_session.id)
                tasks.extend(session_tasks)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必须提供project_id或session_id"
            )

        return [
            TaskResponse(
                id=task.id,
                session_id=task.session_id,
                title=task.title,
                description=task.description,
                status=task.status,
                current_agent=task.current_agent,
                created_at=task.created_at,
                updated_at=task.updated_at
            )
            for task in tasks
        ]


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    创建任务

    在指定会话下创建新任务。
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


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取任务详情
    """
    with db.get_session() as session:
        task_repo = TaskRepository(session)
        task = task_repo.get_by_id(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )

        # 通过session检查项目权限
        session_repo = SessionRepository(session)
        db_session = session_repo.get_by_id(task.session_id)
        check_project_permission(current_user, db_session.project_id, db)

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
async def execute_workflow(
    task_id: str,
    execute_request: WorkflowExecuteRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    执行工作流

    启动Agent工作流处理任务。
    这是一个异步操作，会在后台执行。
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

        session_repo = SessionRepository(session)
        db_session = session_repo.get_by_id(task.session_id)
        check_project_permission(current_user, db_session.project_id, db)

    # 检查是否已经有运行中的orchestrator
    if task_id in active_orchestrators:
        return WorkflowExecuteResponse(
            success=True,
            message="工作流已在运行中",
            final_status="running",
            iteration_count={},
            artifacts_count=0
        )

    # 捕获execute_request的值
    agents_list = execute_request.agents
    max_iter = execute_request.max_iterations
    llm_cfg = execute_request.llm_config or {}

    # 在后台启动orchestrator
    async def start_orchestrator():
        """在后台启动orchestrator"""
        print(f"[Workflow] 开始执行工作流: {task_id}")
        from ..workflow.persistent_task import PersistentTask
        from ..workflow.task import Task as MemoryTask
        from ..llm.llm_client import create_llm_client
        from ..agents.base_agent import BaseAgent
        from typing import Dict, Any
        from .websocket import manager

        try:
            print(f"[Workflow] 查询任务信息...")
            # 重新查询task
            with db.get_session() as session:
                task_repo = TaskRepository(session)
                fresh_task = task_repo.get_by_id(task_id)

                if not fresh_task:
                    print(f"[Workflow] 任务不存在: {task_id}")
                    return

                task_title = fresh_task.title
                task_description = fresh_task.description
                task_session_id = fresh_task.session_id
                print(f"[Workflow] 任务信息: {task_title}")

            # 通知工作流开始
            print(f"[Workflow] 发送工作流启动通知...")
            await manager.broadcast_to_task(
                {
                    "type": "workflow_started",
                    "message": "工作流已启动，Agent开始协作..."
                },
                task_id
            )

            # 创建内存Task
            memory_task = MemoryTask(task_id, task_title, task_description)

            # 包装为持久化Task
            persistent_task = PersistentTask(memory_task, db, task_session_id)

            # 创建LLM客户端
            llm_type = llm_cfg.get("type", "mock")
            print(f"[Workflow] 创建LLM客户端: {llm_type}")
            llm_client = create_llm_client(llm_type, **llm_cfg)

            # 创建Agents
            class DynamicAgent(BaseAgent):
                def __init__(self, name, role, llm_client, task_id, db_instance):
                    super().__init__(name, role, llm_client=llm_client)
                    self.task_id = task_id
                    self.db_instance = db_instance

                def _get_responsibilities(self) -> str:
                    """
                    获取Agent的职责描述

                    为什么：需要给Agent完整的角色定义，让它既能完成专业工作，又能进行日常交流
                    """
                    responsibilities = {
                        'RequirementAnalyst': """你是需求分析师，负责：
1. 理解和分析用户需求
2. 编写详细的需求文档
3. 与用户沟通澄清需求细节
4. 评估需求的可行性

你可以：
- 回答关于需求的问题
- 与用户进行日常交流
- 解释你的分析思路
- 提出建议和疑问""",

                        'Architect': """你是架构师，负责：
1. 设计系统架构
2. 选择技术栈
3. 制定技术方案
4. 评审代码架构

你可以：
- 回答关于架构的问题
- 与团队进行技术讨论
- 解释设计决策
- 提供技术建议""",

                        'Developer': """你是开发工程师，负责：
1. 编写代码实现功能
2. 遵循架构设计
3. 编写单元测试
4. 修复bug

你可以：
- 回答关于代码的问题
- 与团队讨论实现细节
- 解释代码逻辑
- 寻求帮助和建议""",

                        'CodeReviewer': """你是代码审查员，负责：
1. 审查代码质量
2. 检查代码规范
3. 发现潜在问题
4. 提出改进建议

你可以：
- 回答关于代码质量的问题
- 与开发者讨论代码
- 解释审查意见
- 提供最佳实践建议""",

                        'Tester': """你是测试工程师，负责：
1. 设计测试用例
2. 执行测试
3. 报告bug
4. 验证修复

你可以：
- 回答关于测试的问题
- 与团队讨论测试策略
- 解释测试结果
- 提供质量保证建议"""
                    }

                    return responsibilities.get(self.role, f"{self.role}的职责")

                def _notify_message_sync(self, content: str, event_type: str = "thinking"):
                    """保存事件到数据库"""
                    print(f"[Agent {self.name}] {event_type}: {content[:50]}...")

                    try:
                        with self.db_instance.get_session() as session:
                            from ..database.models import TaskEvent
                            event = TaskEvent(
                                task_id=self.task_id,
                                agent_name=self.name,
                                agent_type=self.role,
                                event_type=event_type,
                                content={"message": content}
                            )
                            session.add(event)
                            session.commit()
                    except Exception as e:
                        print(f"[Agent {self.name}] 保存事件失败: {e}")

                def process(self, task) -> Dict[str, Any]:
                    print(f"[Agent {self.name}] 开始处理任务...")

                    # 调用LLM
                    response = self._call_llm(
                        self._build_system_prompt(),
                        self._build_user_prompt(task)
                    )

                    # 不在这里保存事件，由Orchestrator统一保存
                    # 避免重复保存导致消息发送两遍

                    print(f"[Agent {self.name}] 处理完成")
                    return {'success': True, 'output': response}

            print(f"[Workflow] 创建Agents: {agents_list}")
            agents = [
                DynamicAgent(agent_name, agent_name, llm_client, task_id, db)
                for agent_name in agents_list
            ]

            # 执行工作流
            print(f"[Workflow] 开始执行orchestrator...")
            from ..workflow.message_driven_orchestrator import MessageDrivenOrchestrator

            # 创建WebSocket回调
            async def ws_callback(message):
                await manager.broadcast_to_task(message, task_id)

            orchestrator = MessageDrivenOrchestrator(
                agents=agents,
                task=persistent_task,
                websocket_callback=ws_callback,
                db_instance=db
            )

            # 注册到全局管理器
            active_orchestrators[task_id] = orchestrator

            # 启动orchestrator（持续运行，等待消息）
            await orchestrator.start()

            print(f"[Workflow] Orchestrator已停止")

            # 从全局管理器移除
            if task_id in active_orchestrators:
                del active_orchestrators[task_id]

            print(f"[Workflow] 工作流会话结束")
        except Exception as e:
            print(f"[Workflow] 执行出错: {e}")
            import traceback
            traceback.print_exc()

    # 使用asyncio.create_task在当前事件循环中启动
    import asyncio
    asyncio.create_task(start_orchestrator())

    return WorkflowExecuteResponse(
        success=True,
        message="工作流已启动，正在后台执行",
        final_status="running",
        iteration_count={},
        artifacts_count=0
    )


@router.get("/tasks/{task_id}/events", response_model=List[TaskEventResponse])
def get_task_events(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取任务事件列表
    """
    with db.get_session() as session:
        # 验证任务和权限
        task_repo = TaskRepository(session)
        task = task_repo.get_by_id(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )

        session_repo = SessionRepository(session)
        db_session = session_repo.get_by_id(task.session_id)
        check_project_permission(current_user, db_session.project_id, db)

        # 获取事件
        events = task_repo.get_task_events(task_id)

        return [
            TaskEventResponse(
                id=e.id,
                task_id=e.task_id,
                agent_name=e.agent_name,
                agent_type=e.agent_type,
                event_type=e.event_type,
                content=e.content,
                created_at=e.created_at
            )
            for e in events
        ]


@router.get("/tasks/{task_id}/artifacts", response_model=List[ArtifactResponse])
def get_task_artifacts(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    获取任务产物列表
    """
    with db.get_session() as session:
        # 验证任务和权限
        task_repo = TaskRepository(session)
        task = task_repo.get_by_id(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )

        session_repo = SessionRepository(session)
        db_session = session_repo.get_by_id(task.session_id)
        check_project_permission(current_user, db_session.project_id, db)

        # 获取产物
        artifacts = task_repo.get_task_artifacts(task_id)

        return [
            ArtifactResponse(
                id=a.id,
                task_id=a.task_id,
                artifact_type=a.artifact_type,
                name=a.name,
                content=a.content,
                meta_data=a.meta_data,
                created_at=a.created_at
            )
            for a in artifacts
        ]


@router.post("/tasks/{task_id}/human_message")
async def send_human_message(
    task_id: str,
    message_request: HumanMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Database = Depends(get_db)
):
    """
    发送人工消息到工作流

    用于人工介入时发送反馈，或通过@Agent唤醒工作流
    """
    # 验证任务和权限
    with db.get_session() as session:
        task_repo = TaskRepository(session)
        task = task_repo.get_by_id(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )

        session_repo = SessionRepository(session)
        db_session = session_repo.get_by_id(task.session_id)
        check_project_permission(current_user, db_session.project_id, db)

    # 查找对应的orchestrator
    orchestrator = active_orchestrators.get(task_id)

    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="工作流未运行或已结束"
        )

    # 发送消息到orchestrator
    await orchestrator.handle_human_message({
        'content': message_request.content,
        'mentioned_agents': message_request.mentioned_agents,
        'action': message_request.action,
        'user_id': current_user.id
    })

    return {
        'success': True,
        'message': '消息已发送'
    }

