"""
测试数据库操作层

验证内容：
1. 数据库初始化
2. 用户CRUD操作
3. 项目和成员管理
4. 会话和任务管理
5. 事件和产物存储
6. 决策管理

使用SQLite内存数据库进行测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.database import (
    create_database,
    UserRepository, ProjectRepository, SessionRepository,
    TaskRepository, DecisionRepository
)
from src.database.models import UserRole, SessionStatus, TaskStatus, DecisionStatus


def test_database_init():
    """测试1：数据库初始化"""
    print("\n" + "="*60)
    print("测试1：数据库初始化")
    print("="*60)

    # 创建内存数据库
    db = create_database(echo=False)
    print("✅ 数据库实例创建成功")

    # 初始化表结构
    db.init_db()
    print("✅ 数据库表创建成功")

    return db


def test_user_operations(db):
    """测试2：用户操作"""
    print("\n" + "="*60)
    print("测试2：用户CRUD操作")
    print("="*60)

    with db.get_session() as session:
        user_repo = UserRepository(session)

        # 创建用户
        user1 = user_repo.create(
            username="alice",
            email="alice@example.com",
            password_hash="hashed_password_123",
            full_name="Alice Wang"
        )
        print(f"✅ 创建用户: {user1.username} (ID: {user1.id})")

        user2 = user_repo.create(
            username="bob",
            email="bob@example.com",
            password_hash="hashed_password_456",
            full_name="Bob Li"
        )
        print(f"✅ 创建用户: {user2.username} (ID: {user2.id})")

        # 查询用户
        found_user = user_repo.get_by_username("alice")
        print(f"✅ 根据用户名查询: {found_user.username} - {found_user.email}")

        found_user = user_repo.get_by_email("bob@example.com")
        print(f"✅ 根据邮箱查询: {found_user.username} - {found_user.full_name}")

        return user1.id, user2.id


def test_project_operations(db, user1_id, user2_id):
    """测试3：项目操作"""
    print("\n" + "="*60)
    print("测试3：项目和成员管理")
    print("="*60)

    with db.get_session() as session:
        project_repo = ProjectRepository(session)

        # 创建项目
        project = project_repo.create(
            name="AI Agent System",
            description="多Agent协作系统",
            created_by=user1_id
        )
        print(f"✅ 创建项目: {project.name} (ID: {project.id})")

        # 添加项目成员
        member1 = project_repo.add_member(
            project_id=project.id,
            user_id=user1_id,
            role=UserRole.OWNER
        )
        print(f"✅ 添加成员: User {user1_id} as {member1.role.value}")

        member2 = project_repo.add_member(
            project_id=project.id,
            user_id=user2_id,
            role=UserRole.MEMBER
        )
        print(f"✅ 添加成员: User {user2_id} as {member2.role.value}")

        # 查询用户的项目
        user_projects = project_repo.get_user_projects(user1_id)
        print(f"✅ 用户 {user1_id} 的项目数: {len(user_projects)}")

        return project.id


def test_session_operations(db, project_id):
    """测试4：会话操作"""
    print("\n" + "="*60)
    print("测试4：会话管理")
    print("="*60)

    with db.get_session() as session:
        session_repo = SessionRepository(session)

        # 创建会话
        db_session = session_repo.create(
            session_id="session-001",
            project_id=project_id,
            meta_data={"description": "第一个测试会话"}
        )
        print(f"✅ 创建会话: {db_session.id} (状态: {db_session.status.value})")

        # 查询会话
        found_session = session_repo.get_by_id("session-001")
        print(f"✅ 查询会话: {found_session.id} - {found_session.meta_data}")

        # 更新会话状态
        session_repo.update_status("session-001", SessionStatus.COMPLETED)
        found_session = session_repo.get_by_id("session-001")
        print(f"✅ 更新状态: {found_session.status.value}")

        return db_session.id


def test_task_operations(db, session_id, user_id):
    """测试5：任务操作"""
    print("\n" + "="*60)
    print("测试5：任务、事件和产物管理")
    print("="*60)

    with db.get_session() as session:
        task_repo = TaskRepository(session)

        # 创建任务
        task = task_repo.create(
            task_id="task-001",
            session_id=session_id,
            title="实现用户登录功能",
            description="实现基于JWT的用户登录"
        )
        print(f"✅ 创建任务: {task.title} (ID: {task.id})")

        # 更新任务状态
        task_repo.update_status(
            task_id="task-001",
            status=TaskStatus.IN_DEVELOPMENT,
            current_agent="Developer"
        )
        print(f"✅ 更新任务状态: {TaskStatus.IN_DEVELOPMENT.value}")

        # 添加事件
        event1 = task_repo.add_event(
            task_id="task-001",
            agent_name="Requester",
            agent_type="ai",
            event_type="start",
            content={"message": "开始分析需求"}
        )
        print(f"✅ 添加事件: {event1.agent_name} - {event1.event_type}")

        event2 = task_repo.add_event(
            task_id="task-001",
            agent_name="Developer",
            agent_type="ai",
            event_type="artifact",
            content={"artifact_type": "code", "version": 1}
        )
        print(f"✅ 添加事件: {event2.agent_name} - {event2.event_type}")

        # 添加产物
        artifact1 = task_repo.add_artifact(
            task_id="task-001",
            artifact_type="code",
            name="login.py",
            content="def login(username, password):\n    pass",
            meta_data={"language": "python", "version": 1}
        )
        print(f"✅ 添加产物: {artifact1.name} ({artifact1.artifact_type})")

        artifact2 = task_repo.add_artifact(
            task_id="task-001",
            artifact_type="document",
            name="需求文档.md",
            content="# 用户登录需求\n\n...",
            meta_data={"version": 1}
        )
        print(f"✅ 添加产物: {artifact2.name} ({artifact2.artifact_type})")

        # 查询事件和产物
        events = task_repo.get_task_events("task-001")
        print(f"✅ 任务事件数: {len(events)}")

        artifacts = task_repo.get_task_artifacts("task-001")
        print(f"✅ 任务产物数: {len(artifacts)}")

        return task.id


def test_decision_operations(db, task_id, user_id):
    """测试6：决策操作"""
    print("\n" + "="*60)
    print("测试6：决策管理")
    print("="*60)

    with db.get_session() as session:
        decision_repo = DecisionRepository(session)

        # 创建待办决策
        decision = decision_repo.create(
            task_id=task_id,
            agent_name="CodeReviewer",
            decision_type="approval",
            context={"message": "代码审查发现问题，需要人工决策"},
            assigned_to=user_id
        )
        print(f"✅ 创建决策: {decision.decision_type} (ID: {decision.id})")

        # 查询待办决策
        pending = decision_repo.get_pending_decisions(task_id=task_id)
        print(f"✅ 待办决策数: {len(pending)}")

        pending_for_user = decision_repo.get_pending_decisions(assigned_to=user_id)
        print(f"✅ 用户 {user_id} 的待办决策数: {len(pending_for_user)}")

        # 解决决策
        decision_repo.resolve(
            decision_id=decision.id,
            response={"action": "approve", "comment": "同意通过"},
            resolved_by=user_id
        )
        print(f"✅ 解决决策: {decision.id}")

        # 验证状态
        resolved_decision = decision_repo.get_by_id(decision.id)
        print(f"✅ 决策状态: {resolved_decision.status.value}")
        print(f"✅ 决策结果: {resolved_decision.response}")


def test_complete_workflow(db):
    """测试7：完整工作流"""
    print("\n" + "="*60)
    print("测试7：完整工作流（模拟真实场景）")
    print("="*60)

    with db.get_session() as session:
        user_repo = UserRepository(session)
        project_repo = ProjectRepository(session)
        session_repo = SessionRepository(session)
        task_repo = TaskRepository(session)

        # 1. 创建用户
        user = user_repo.create(
            username="charlie",
            email="charlie@example.com",
            password_hash="hash123"
        )
        print(f"1. 创建用户: {user.username}")

        # 2. 创建项目
        project = project_repo.create(
            name="电商系统",
            description="在线购物平台",
            created_by=user.id
        )
        project_repo.add_member(project.id, user.id, UserRole.OWNER)
        print(f"2. 创建项目: {project.name}")

        # 3. 创建会话
        db_session = session_repo.create(
            session_id="session-workflow-001",
            project_id=project.id,
            meta_data={"sprint": "Sprint 1"}
        )
        print(f"3. 创建会话: {db_session.id}")

        # 4. 创建任务
        task = task_repo.create(
            task_id="task-workflow-001",
            session_id=db_session.id,
            title="实现购物车功能",
            description="用户可以添加商品到购物车"
        )
        print(f"4. 创建任务: {task.title}")

        # 5. 模拟Agent工作流
        agents = ["Requester", "Developer", "CodeReviewer", "Tester", "DevOps"]

        for i, agent_name in enumerate(agents, 1):
            # 更新任务状态
            task_repo.update_status(
                task_id=task.id,
                status=TaskStatus.IN_DEVELOPMENT,
                current_agent=agent_name
            )

            # 添加事件
            task_repo.add_event(
                task_id=task.id,
                agent_name=agent_name,
                agent_type="ai",
                event_type="start",
                content={"step": i, "message": f"{agent_name}开始工作"}
            )

            # 添加产物
            task_repo.add_artifact(
                task_id=task.id,
                artifact_type="document" if i == 1 else "code",
                name=f"{agent_name}_output.txt",
                content=f"{agent_name}的输出内容",
                meta_data={"agent": agent_name, "step": i}
            )

            print(f"   {i}. {agent_name} 完成工作")

        # 6. 完成任务
        task_repo.update_status(task.id, TaskStatus.COMPLETED)
        session_repo.update_status(db_session.id, SessionStatus.COMPLETED)
        print(f"5. 任务完成")

        # 7. 统计
        events = task_repo.get_task_events(task.id)
        artifacts = task_repo.get_task_artifacts(task.id)
        print(f"\n统计:")
        print(f"  - 事件数: {len(events)}")
        print(f"  - 产物数: {len(artifacts)}")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("数据库操作层测试")
    print("="*60)

    try:
        # 测试1：初始化
        db = test_database_init()

        # 测试2：用户操作
        user1_id, user2_id = test_user_operations(db)

        # 测试3：项目操作
        project_id = test_project_operations(db, user1_id, user2_id)

        # 测试4：会话操作
        session_id = test_session_operations(db, project_id)

        # 测试5：任务操作
        task_id = test_task_operations(db, session_id, user1_id)

        # 测试6：决策操作
        test_decision_operations(db, task_id, user1_id)

        # 测试7：完整工作流
        test_complete_workflow(db)

        # 总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        print("✅ 所有测试通过")

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
