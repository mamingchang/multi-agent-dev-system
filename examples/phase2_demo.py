"""
Phase 2 Demo: Human Agent and Decision System
演示人工Agent和决策系统
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.migrations import Database
from src.project_manager import ProjectManager
from src.decision_queue import DecisionQueue
from src.event_logger import EventLogger
from src.enhanced_orchestrator import EnhancedOrchestrator
from src.workflow.task import Task
from src.database.models import User, Project, UserRole


def main():
    """主函数"""
    print("=" * 80)
    print("Phase 2 演示：人工Agent和决策系统")
    print("=" * 80)

    # 1. 初始化数据库
    print("\n1. 初始化数据库...")
    db = Database("demo_phase2.db")
    db.init_db()
    db.create_demo_data()

    db_session = db.get_session()

    # 2. 获取演示用户和项目
    print("\n2. 获取演示数据...")
    alice = db_session.query(User).filter_by(username="alice").first()
    project = db_session.query(Project).filter_by(name="Demo Project").first()

    print(f"  用户: {alice.username} (ID: {alice.id})")
    print(f"  项目: {project.name} (ID: {project.id})")

    # 3. 初始化管理器
    print("\n3. 初始化管理器...")
    project_manager = ProjectManager(db_session)
    decision_queue = DecisionQueue(db_session)
    event_logger = EventLogger(db_session)

    # 4. 创建增强的协调器
    print("\n4. 创建协调器...")
    orchestrator = EnhancedOrchestrator(
        project_manager=project_manager,
        decision_queue=decision_queue,
        event_logger=event_logger,
        config={'max_iterations': 15}
    )

    # 5. 配置Developer为人工Agent（异步模式）
    print("\n5. 配置人工Agent...")
    orchestrator.configure_human_agent('Developer', mode='async')

    # 6. 创建任务
    print("\n6. 创建任务...")
    task = Task(
        task_id="DEMO-001",
        title="演示人工Agent介入",
        description="这个任务会在Developer阶段暂停，等待人工决策"
    )

    # 7. 执行工作流
    print("\n7. 执行工作流...")
    try:
        result = orchestrator.execute_workflow(
            task=task,
            project_id=project.id,
            user_id=alice.id,
            session_id="demo-session-001"
        )

        print("\n" + "=" * 80)
        print("执行结果:")
        print("=" * 80)
        print(f"状态: {result['status']}")
        print(f"消息: {result['message']}")

        if result['status'] == 'waiting_for_human':
            decision_id = result['decision_id']
            print(f"\n⏸  工作流已暂停")
            print(f"决策ID: {decision_id}")
            print(f"\n要恢复工作流，请：")
            print(f"1. 在Web界面处理决策 {decision_id}")
            print(f"2. 或使用CLI命令解决决策")
            print(f"\n演示：自动解决决策...")

            # 模拟人工决策
            decision_queue.resolve_decision(
                decision_id=decision_id,
                user_id=alice.id,
                response={
                    'approved': True,
                    'message': '代码审查通过',
                    'next_agent': 'CodeReviewer',
                    'comments': '这是模拟的人工决策'
                }
            )

            print(f"✓ 决策 {decision_id} 已解决")

            # 恢复工作流
            print(f"\n8. 恢复工作流...")
            result = orchestrator.resume_workflow(
                task=task,
                project_id=project.id,
                user_id=alice.id,
                session_id="demo-session-001",
                decision_id=decision_id
            )

            print(f"\n最终状态: {result['status']}")

    except Exception as e:
        print(f"\n✗ 执行出错: {e}")
        import traceback
        traceback.print_exc()

    # 8. 查看事件日志
    print("\n" + "=" * 80)
    print("9. 任务时间线:")
    print("=" * 80)
    timeline = event_logger.get_task_timeline(task.task_id)
    for event in timeline:
        print(f"  [{event['created_at']}] {event['agent_name']} ({event['agent_type']}) - {event['event_type']}")

    # 9. 查看决策统计
    print("\n" + "=" * 80)
    print("10. 决策统计:")
    print("=" * 80)
    stats = decision_queue.get_statistics(project_id=project.id)
    print(f"  总决策数: {stats['total']}")
    print(f"  待处理: {stats['pending']}")
    print(f"  已解决: {stats['resolved']}")
    print(f"  解决率: {stats['resolution_rate']:.1%}")

    # 10. 查看事件统计
    print("\n" + "=" * 80)
    print("11. 事件统计:")
    print("=" * 80)
    event_stats = event_logger.get_statistics(task_id=task.task_id)
    print(f"  总事件数: {event_stats['total_events']}")
    print(f"  AI事件: {event_stats['ai_events']}")
    print(f"  人工事件: {event_stats['human_events']}")
    print(f"  事件类型分布:")
    for event_type, count in event_stats['event_types'].items():
        if count > 0:
            print(f"    - {event_type}: {count}")

    print("\n" + "=" * 80)
    print("✓ Phase 2 演示完成！")
    print("=" * 80)

    db_session.close()


if __name__ == "__main__":
    main()
