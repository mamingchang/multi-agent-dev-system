"""
Session Management Demo
演示如何使用Session管理系统
"""
from src.orchestrator import Orchestrator
from src.workflow.task import Task
from src.session_manager import SessionManager


def demo_basic_session():
    """基础Session使用"""
    print("=" * 80)
    print("示例1: 基础Session管理")
    print("=" * 80)

    # 创建Session管理器
    session_mgr = SessionManager(storage_path="./sessions")

    # 创建会话
    session = session_mgr.create_session(user_id="user_001")

    # 创建协调器
    orchestrator = Orchestrator(
        config={'max_iterations': 15},
        session_manager=session_mgr
    )

    # 创建任务
    task = Task(
        task_id="TASK-001",
        title="开发用户管理系统",
        description="需要一个用户管理系统，支持用户注册、登录、权限管理等功能"
    )

    # 执行工作流（自动保存）
    result = orchestrator.execute_workflow(task, session=session, auto_save=True)

    print(f"\n会话ID: {result.get('session_id')}")
    print(f"任务状态: {result['task']['status']}")


def demo_resume_session():
    """恢复会话"""
    print("\n" + "=" * 80)
    print("示例2: 恢复已保存的会话")
    print("=" * 80)

    session_mgr = SessionManager(storage_path="./sessions")

    # 列出所有会话
    sessions = session_mgr.list_sessions()
    print(f"\n找到 {len(sessions)} 个会话:")
    for s in sessions:
        print(f"  - {s['session_id'][:8]}... | 用户: {s['user_id']} | 状态: {s['status']} | 任务数: {s['task_count']}")

    if sessions:
        # 恢复第一个会话
        session_id = sessions[0]['session_id']
        session = session_mgr.resume_session(session_id)

        if session:
            print(f"\n会话详情:")
            print(f"  会话ID: {session.session_id}")
            print(f"  用户ID: {session.user_id}")
            print(f"  状态: {session.status}")
            print(f"  任务列表: {session.list_tasks()}")

            # 查看任务详情
            for task_id in session.list_tasks():
                task = session.get_task(task_id)
                print(f"\n  任务 {task_id}:")
                print(f"    标题: {task.title}")
                print(f"    状态: {task.status.value}")
                print(f"    产物数: {len(task.artifacts)}")
                print(f"    反馈数: {len(task.feedback)}")


def demo_multi_user():
    """多用户会话管理"""
    print("\n" + "=" * 80)
    print("示例3: 多用户会话管理")
    print("=" * 80)

    session_mgr = SessionManager(storage_path="./sessions")

    # 为不同用户创建会话
    users = ["alice", "bob", "charlie"]

    for user in users:
        session = session_mgr.create_session(user_id=user)
        task = Task(
            task_id=f"TASK-{user}",
            title=f"{user}的任务",
            description=f"这是{user}的开发任务"
        )
        session.add_task(task)
        session_mgr.save_session(session)

    # 查看每个用户的会话
    for user in users:
        user_sessions = session_mgr.list_sessions(user_id=user)
        print(f"\n{user} 的会话: {len(user_sessions)}个")
        for s in user_sessions:
            print(f"  - {s['session_id'][:8]}... | 任务数: {s['task_count']}")


def demo_pause_resume():
    """暂停和恢复会话"""
    print("\n" + "=" * 80)
    print("示例4: 暂停和恢复会话")
    print("=" * 80)

    session_mgr = SessionManager(storage_path="./sessions")

    # 创建会话
    session = session_mgr.create_session(user_id="test_user")
    task = Task(
        task_id="TASK-PAUSE",
        title="可暂停的任务",
        description="测试暂停和恢复功能"
    )
    session.add_task(task)
    session_mgr.save_session(session)

    print(f"会话状态: {session.status}")

    # 暂停会话
    session_mgr.pause_session(session.session_id)
    print(f"暂停后状态: {session.status}")

    # 恢复会话
    resumed_session = session_mgr.resume_session(session.session_id)
    print(f"恢复后状态: {resumed_session.status}")


def demo_cleanup():
    """清理旧会话"""
    print("\n" + "=" * 80)
    print("示例5: 清理旧会话")
    print("=" * 80)

    session_mgr = SessionManager(storage_path="./sessions")

    # 清理30天前的会话
    deleted = session_mgr.cleanup_old_sessions(days=30)
    print(f"清理了 {deleted} 个旧会话")


if __name__ == "__main__":
    # 运行所有示例
    demo_basic_session()
    demo_resume_session()
    demo_multi_user()
    demo_pause_resume()
    demo_cleanup()
