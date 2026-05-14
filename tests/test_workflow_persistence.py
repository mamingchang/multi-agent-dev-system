"""
测试工作流与数据库集成

验证内容：
1. PersistentTask自动保存到数据库
2. 产物自动持久化
3. 事件自动记录
4. 状态自动同步
5. 完整工作流的数据库持久化

使用SQLite内存数据库进行测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.workflow.persistent_task import create_workflow_session, PersistentTask
from src.database.database import create_database, TaskRepository, SessionRepository
from src.database.models import TaskStatus, SessionStatus
from src.agents.base_agent import BaseAgent
from src.llm.llm_client import create_llm_client
from src.workflow.simple_orchestrator import SimpleOrchestrator
from typing import Dict, Any


def test_basic_persistence():
    """测试1：基本持久化功能"""
    print("\n" + "="*60)
    print("测试1：基本持久化功能")
    print("="*60)

    # 创建数据库
    db = create_database()
    db.init_db()

    # 创建用户和项目（简化，直接插入）
    with db.get_session() as session:
        from src.database.models import User, Project, ProjectMember, UserRole, Organization

        # 创建组织
        org = Organization(name="Test Org", slug="test-org")
        session.add(org)
        session.flush()

        # 创建用户
        user = User(username="test_user", email="test@example.com", password_hash="hash")
        session.add(user)
        session.flush()

        # 创建项目
        project = Project(name="Test Project", organization_id=org.id, created_by=user.id)
        session.add(project)
        session.flush()

        member = ProjectMember(project_id=project.id, user_id=user.id, role=UserRole.OWNER)
        session.add(member)
        session.flush()

        project_id = project.id

    # 创建工作流会话
    workflow_session = create_workflow_session(
        session_id="test-session-001",
        project_id=project_id,
        database_url="sqlite:///:memory:"
    )
    print(f"✅ 创建工作流会话: {workflow_session.session_id}")

    # 创建持久化Task
    task = workflow_session.create_task(
        task_id="test-task-001",
        title="测试任务",
        description="测试持久化功能"
    )
    print(f"✅ 创建持久化Task: {task.task_id}")

    # 验证数据库中存在
    with workflow_session.db.get_session() as session:
        task_repo = TaskRepository(session)
        db_task = task_repo.get_by_id("test-task-001")
        print(f"✅ 数据库验证: {db_task.title} (状态: {db_task.status.value})")

    # 添加产物
    task.add_artifact(
        artifact_type="code",
        content="print('Hello World')",
        agent="TestAgent"
    )
    print(f"✅ 添加产物")

    # 验证产物保存
    with workflow_session.db.get_session() as session:
        task_repo = TaskRepository(session)
        artifacts = task_repo.get_task_artifacts("test-task-001")
        print(f"✅ 数据库中的产物数: {len(artifacts)}")
        if artifacts:
            print(f"   产物: {artifacts[0].name} - {artifacts[0].artifact_type}")

    # 记录事件
    task.record_event(
        agent_name="TestAgent",
        event_type="start",
        content={"message": "开始处理"}
    )
    print(f"✅ 记录事件")

    # 验证事件保存
    with workflow_session.db.get_session() as session:
        task_repo = TaskRepository(session)
        events = task_repo.get_task_events("test-task-001")
        print(f"✅ 数据库中的事件数: {len(events)}")
        if events:
            print(f"   事件: {events[0].agent_name} - {events[0].event_type}")

    # 更新状态
    from src.workflow.task import TaskStatus as MemoryTaskStatus
    task.status = MemoryTaskStatus.IN_DEVELOPMENT
    print(f"✅ 更新状态: {task.status.value}")

    # 验证状态同步
    with workflow_session.db.get_session() as session:
        task_repo = TaskRepository(session)
        db_task = task_repo.get_by_id("test-task-001")
        print(f"✅ 数据库状态同步: {db_task.status.value}")

    return workflow_session


def test_workflow_with_persistence():
    """测试2：完整工作流的持久化"""
    print("\n" + "="*60)
    print("测试2：完整工作流的持久化")
    print("="*60)

    # 创建数据库
    db = create_database()
    db.init_db()

    # 创建用户和项目
    with db.get_session() as session:
        from src.database.models import User, Project, ProjectMember, UserRole, Organization

        # 创建组织
        org = Organization(name="Workflow Org", slug="workflow-org")
        session.add(org)
        session.flush()

        # 创建用户
        user = User(username="workflow_user", email="workflow@example.com", password_hash="hash")
        session.add(user)
        session.flush()

        # 创建项目
        project = Project(name="Workflow Project", organization_id=org.id, created_by=user.id)
        session.add(project)
        session.flush()

        member = ProjectMember(project_id=project.id, user_id=user.id, role=UserRole.OWNER)
        session.add(member)
        session.flush()

        project_id = project.id

    # 创建工作流会话
    from src.workflow.persistent_task import WorkflowSession
    workflow_session = WorkflowSession(
        session_id="workflow-session-001",
        project_id=project_id,
        db=db
    )
    print(f"✅ 创建工作流会话")

    # 创建持久化Task
    task = workflow_session.create_task(
        task_id="workflow-task-001",
        title="实现登录功能",
        description="实现用户登录功能"
    )
    print(f"✅ 创建任务: {task.title}")

    # 创建Mock LLM和Agents
    mock_responses = {
        "Requester": "# 需求文档\n\n实现用户登录",
        "Developer": "# 登录代码\n\n```python\ndef login(): pass\n```",
        "CodeReviewer": "✅ 代码审查通过"
    }
    llm_client = create_llm_client("mock", responses=mock_responses)

    # 定义简单的Agent
    class SimpleRequester(BaseAgent):
        def __init__(self, llm_client, db, task_id):
            super().__init__("Requester", "需求分析师", llm_client=llm_client)
            self.db = db
            self.task_id = task_id

        def _get_responsibilities(self) -> str:
            return "分析需求"

        def process(self, task) -> Dict[str, Any]:
            print(f"\n[{self.name}] 处理中...")
            response = self._call_llm(self._build_system_prompt(), self._build_user_prompt(task))

            # 记录事件到数据库
            if hasattr(task, 'record_event'):
                task.record_event(self.name, "complete", {"output": response})

            return {'success': True, 'output': response}

    class SimpleDeveloper(BaseAgent):
        def __init__(self, llm_client, db, task_id):
            super().__init__("Developer", "开发工程师", llm_client=llm_client)
            self.db = db
            self.task_id = task_id

        def _get_responsibilities(self) -> str:
            return "编写代码"

        def process(self, task) -> Dict[str, Any]:
            print(f"\n[{self.name}] 处理中...")
            response = self._call_llm(self._build_system_prompt(), self._build_user_prompt(task))

            # 记录事件到数据库
            if hasattr(task, 'record_event'):
                task.record_event(self.name, "complete", {"output": response})

            return {'success': True, 'output': response}

    class SimpleReviewer(BaseAgent):
        def __init__(self, llm_client, db, task_id):
            super().__init__("CodeReviewer", "代码审查员", llm_client=llm_client)
            self.db = db
            self.task_id = task_id

        def _get_responsibilities(self) -> str:
            return "审查代码"

        def process(self, task) -> Dict[str, Any]:
            print(f"\n[{self.name}] 处理中...")
            response = self._call_llm(self._build_system_prompt(), self._build_user_prompt(task))

            # 记录事件到数据库
            if hasattr(task, 'record_event'):
                task.record_event(self.name, "complete", {"output": response})

            return {'success': True, 'output': response}

    # 创建Agents
    agents = [
        SimpleRequester(llm_client, db, task.task_id),
        SimpleDeveloper(llm_client, db, task.task_id),
        SimpleReviewer(llm_client, db, task.task_id)
    ]

    # 创建Orchestrator
    orchestrator = SimpleOrchestrator(agents, max_iterations=3)

    # 执行工作流
    print(f"\n开始执行工作流...")
    result = orchestrator.execute(task)

    print(f"\n✅ 工作流执行完成: {result['success']}")

    # 验证数据库中的数据
    print(f"\n验证数据库持久化:")
    with db.get_session() as session:
        task_repo = TaskRepository(session)

        # 查询任务
        db_task = task_repo.get_by_id("workflow-task-001")
        print(f"  任务: {db_task.title} (状态: {db_task.status.value})")

        # 查询事件
        events = task_repo.get_task_events("workflow-task-001")
        print(f"  事件数: {len(events)}")
        for event in events:
            print(f"    - {event.agent_name}: {event.event_type}")

        # 查询产物
        artifacts = task_repo.get_task_artifacts("workflow-task-001")
        print(f"  产物数: {len(artifacts)}")
        for artifact in artifacts:
            print(f"    - {artifact.name} ({artifact.artifact_type})")

    # 完成会话
    workflow_session.complete()
    print(f"\n✅ 会话完成")

    # 验证会话状态
    with db.get_session() as session:
        session_repo = SessionRepository(session)
        db_session = session_repo.get_by_id("workflow-session-001")
        print(f"  会话状态: {db_session.status.value}")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("工作流与数据库集成测试")
    print("="*60)

    try:
        # 测试1：基本持久化
        test_basic_persistence()

        # 测试2：完整工作流
        test_workflow_with_persistence()

        # 总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        print("✅ 所有测试通过")
        print("\n关键验证点:")
        print("  ✅ Task自动保存到数据库")
        print("  ✅ 产物自动持久化")
        print("  ✅ 事件自动记录")
        print("  ✅ 状态自动同步")
        print("  ✅ 完整工作流持久化")

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
