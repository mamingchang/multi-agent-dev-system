"""
并发控制测试

测试场景：
1. Token预估
2. Token预留和释放
3. 任务调度器基本功能
4. 并发限制
5. 优先级调度
6. 公平调度
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
from src.concurrency.token_reservation import TokenEstimator, TokenReservationManager
from src.concurrency.task_scheduler import TaskScheduler, FairScheduler


def test_token_estimation():
    """测试1: Token预估"""
    print("\n=== 测试1: Token预估 ===")

    # 简单任务
    simple_estimate = TokenEstimator.estimate_tokens(
        task_description="修复登录页面的按钮样式",
        agent_sequence=["Developer"],
        complexity="simple"
    )
    print(f"简单任务预估: {simple_estimate} tokens")
    assert simple_estimate > 0

    # 复杂任务
    complex_estimate = TokenEstimator.estimate_tokens(
        task_description="实现完整的用户认证系统，包括注册、登录、密码重置、邮箱验证等功能",
        agent_sequence=["ProductManager", "Architect", "Developer", "Tester", "CodeReviewer"],
        complexity="complex"
    )
    print(f"复杂任务预估: {complex_estimate} tokens")
    assert complex_estimate > simple_estimate

    print("✓ Token预估测试通过")


def test_token_reservation():
    """测试2: Token预留管理"""
    print("\n=== 测试2: Token预留管理 ===")

    manager = TokenReservationManager()

    # 注意：这个测试不涉及数据库，只测试管理器逻辑
    # 实际使用需要数据库会话

    # 模拟预留记录
    from src.concurrency.token_reservation import TokenReservation

    reservation = TokenReservation(
        task_id="task-1",
        organization_id=1,
        reserved_tokens=5000,
        estimated_tokens=5000
    )

    manager.reservations["task-1"] = reservation

    # 获取预留记录
    retrieved = manager.get_reservation("task-1")
    assert retrieved is not None
    assert retrieved.task_id == "task-1"
    assert retrieved.reserved_tokens == 5000

    # 获取组织总预留
    total_reserved = manager.get_organization_reserved(1)
    assert total_reserved == 5000

    print(f"✓ 预留记录创建成功: {total_reserved} tokens")
    print("✓ Token预留管理测试通过")


def test_task_scheduler_basic():
    """测试3: 任务调度器基本功能"""
    print("\n=== 测试3: 任务调度器基本功能 ===")

    scheduler = TaskScheduler()

    # 添加任务
    scheduler.add_task("task-1", organization_id=1, priority=50)
    scheduler.add_task("task-2", organization_id=1, priority=60)
    scheduler.add_task("task-3", organization_id=1, priority=40)

    assert scheduler.get_queue_size() == 3
    print(f"✓ 队列大小: {scheduler.get_queue_size()}")

    # 获取下一个任务（应该是优先级最高的task-2）
    next_task = scheduler.get_next_task()
    assert next_task == "task-2"
    print(f"✓ 调度任务: {next_task} (优先级60)")

    # 完成任务
    scheduler.complete_task("task-2", organization_id=1)

    print("✓ 任务调度器基本功能测试通过")


def test_concurrent_limit():
    """测试4: 并发限制"""
    print("\n=== 测试4: 并发限制 ===")

    scheduler = TaskScheduler()

    # 设置组织1的并发限制为2
    scheduler.set_organization_limit(1, 2)

    # 添加3个任务
    scheduler.add_task("task-1", organization_id=1, priority=50)
    scheduler.add_task("task-2", organization_id=1, priority=50)
    scheduler.add_task("task-3", organization_id=1, priority=50)

    # 调度前2个任务
    task1 = scheduler.get_next_task()
    task2 = scheduler.get_next_task()

    assert task1 is not None
    assert task2 is not None
    print(f"✓ 调度了2个任务: {task1}, {task2}")

    # 第3个任务应该被阻塞
    task3 = scheduler.get_next_task()
    assert task3 is None
    print("✓ 第3个任务被并发限制阻塞")

    # 完成一个任务后，第3个任务应该可以调度
    scheduler.complete_task(task1, organization_id=1)
    task3 = scheduler.get_next_task()
    assert task3 == "task-3"
    print(f"✓ 完成任务后，第3个任务可以调度: {task3}")

    print("✓ 并发限制测试通过")


def test_priority_scheduling():
    """测试5: 优先级调度"""
    print("\n=== 测试5: 优先级调度 ===")

    scheduler = TaskScheduler()

    # 添加不同优先级的任务
    scheduler.add_task("low", organization_id=1, priority=30)
    scheduler.add_task("high", organization_id=1, priority=80)
    scheduler.add_task("medium", organization_id=1, priority=50)

    # 应该按优先级顺序调度
    task1 = scheduler.get_next_task()
    assert task1 == "high"
    print(f"✓ 第1个调度: {task1} (优先级80)")

    task2 = scheduler.get_next_task()
    assert task2 == "medium"
    print(f"✓ 第2个调度: {task2} (优先级50)")

    task3 = scheduler.get_next_task()
    assert task3 == "low"
    print(f"✓ 第3个调度: {task3} (优先级30)")

    print("✓ 优先级调度测试通过")


def test_fair_scheduling():
    """测试6: 公平调度"""
    print("\n=== 测试6: 公平调度 ===")

    scheduler = FairScheduler()

    # 设置两个组织的并发限制
    scheduler.set_organization_limit(1, 2)
    scheduler.set_organization_limit(2, 2)

    # 添加两个组织的任务（相同优先级）
    scheduler.add_task("org1-task1", organization_id=1, priority=50)
    scheduler.add_task("org1-task2", organization_id=1, priority=50)
    scheduler.add_task("org2-task1", organization_id=2, priority=50)
    scheduler.add_task("org2-task2", organization_id=2, priority=50)

    # 应该轮询调度
    scheduled = []
    for _ in range(4):
        task = scheduler.get_next_task()
        if task:
            scheduled.append(task)
            # 提取组织ID
            org_id = 1 if "org1" in task else 2
            scheduler.complete_task(task, org_id)

    print(f"✓ 调度顺序: {scheduled}")

    # 验证两个组织的任务都被调度了
    org1_tasks = [t for t in scheduled if "org1" in t]
    org2_tasks = [t for t in scheduled if "org2" in t]

    assert len(org1_tasks) == 2
    assert len(org2_tasks) == 2
    print(f"✓ 组织1任务: {len(org1_tasks)}, 组织2任务: {len(org2_tasks)}")

    print("✓ 公平调度测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("并发控制测试")
    print("="*60)

    try:
        test_token_estimation()
        test_token_reservation()
        test_task_scheduler_basic()
        test_concurrent_limit()
        test_priority_scheduling()
        test_fair_scheduling()

        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60)

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
