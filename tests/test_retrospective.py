"""
测试经验回溯系统

验证内容：
1. 任务复盘和经验提取
2. 经验知识库管理
3. 经验搜索和过滤
4. 最佳实践和反模式识别
5. 经验应用和反馈
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.memory.retrospective import (
    Experience, ExperienceType, TaskRetrospective,
    ExperienceKnowledgeBase, RetrospectiveSystem,
    get_retrospective_system
)


def test_task_retrospective():
    """测试1：任务复盘"""
    print("\n" + "="*60)
    print("测试1：任务复盘和经验提取")
    print("="*60)

    # 创建复盘对象
    retro = TaskRetrospective("task-001", "实现用户登录功能")

    # 添加事件
    retro.add_event({'agent': 'Requester', 'type': 'complete'})
    retro.add_event({'agent': 'Developer', 'type': 'complete'})
    retro.add_event({'agent': 'CodeReviewer', 'type': 'reject'})
    retro.add_event({'agent': 'Developer', 'type': 'complete'})
    retro.add_event({'agent': 'CodeReviewer', 'type': 'approve'})

    # 设置迭代次数
    retro.iteration_count = {
        'Requester': 1,
        'Developer': 2,
        'CodeReviewer': 2
    }

    retro.success = True
    retro.duration = 300.0

    # 分析提取经验
    experiences = retro.analyze()

    print(f"✅ 从任务中提取了 {len(experiences)} 条经验")

    for i, exp in enumerate(experiences, 1):
        print(f"\n经验 {i}:")
        print(f"  类型: {exp.experience_type.value}")
        print(f"  标题: {exp.title}")
        print(f"  描述: {exp.description}")
        print(f"  置信度: {exp.confidence}")

    assert len(experiences) > 0
    print("\n✅ 任务复盘测试通过")


def test_experience_knowledge_base():
    """测试2：经验知识库"""
    print("\n" + "="*60)
    print("测试2：经验知识库管理")
    print("="*60)

    kb = ExperienceKnowledgeBase()

    # 添加多条经验
    import uuid

    exp1 = Experience(
        experience_id=f"exp-{uuid.uuid4().hex[:12]}",
        experience_type=ExperienceType.SUCCESS,
        title="成功实现登录功能",
        description="使用JWT认证成功实现了登录功能",
        context={'task': 'login', 'tech': 'jwt'},
        agents_involved=['Developer'],
        tags=['success', 'login', 'jwt'],
        confidence=0.9
    )
    kb.add_experience(exp1)

    exp2 = Experience(
        experience_id=f"exp-{uuid.uuid4().hex[:12]}",
        experience_type=ExperienceType.BEST_PRACTICE,
        title="使用bcrypt哈希密码",
        description="密码应该使用bcrypt进行哈希存储",
        context={'security': 'password'},
        agents_involved=['Developer'],
        tags=['best_practice', 'security'],
        confidence=1.0
    )
    kb.add_experience(exp2)

    exp3 = Experience(
        experience_id=f"exp-{uuid.uuid4().hex[:12]}",
        experience_type=ExperienceType.ANTI_PATTERN,
        title="避免明文存储密码",
        description="绝不应该明文存储用户密码",
        context={'security': 'password'},
        agents_involved=['Developer'],
        tags=['anti_pattern', 'security'],
        confidence=1.0
    )
    kb.add_experience(exp3)

    print(f"✅ 添加了 {len(kb.experiences)} 条经验")

    # 搜索经验
    results = kb.search_experiences(query="登录")
    print(f"\n搜索'登录': {len(results)} 条")

    # 获取最佳实践
    best_practices = kb.get_best_practices()
    print(f"最佳实践: {len(best_practices)} 条")
    for bp in best_practices:
        print(f"  - {bp.title}")

    # 获取反模式
    anti_patterns = kb.get_anti_patterns()
    print(f"反模式: {len(anti_patterns)} 条")
    for ap in anti_patterns:
        print(f"  - {ap.title}")

    # 统计
    stats = kb.get_statistics()
    print(f"\n统计信息:")
    print(f"  总数: {stats['total']}")
    print(f"  按类型: {stats['by_type']}")

    print("\n✅ 经验知识库测试通过")


def test_experience_application():
    """测试3：经验应用和反馈"""
    print("\n" + "="*60)
    print("测试3：经验应用和反馈")
    print("="*60)

    import uuid

    exp = Experience(
        experience_id=f"exp-{uuid.uuid4().hex[:12]}",
        experience_type=ExperienceType.BEST_PRACTICE,
        title="使用参数化查询防止SQL注入",
        description="数据库查询应该使用参数化查询",
        context={'security': 'sql'},
        agents_involved=['Developer'],
        tags=['best_practice', 'security', 'sql'],
        confidence=0.9
    )

    print(f"初始状态:")
    print(f"  应用次数: {exp.applied_count}")
    print(f"  成功率: {exp.success_rate:.2f}")

    # 模拟应用经验
    exp.apply(success=True)
    exp.apply(success=True)
    exp.apply(success=False)
    exp.apply(success=True)

    print(f"\n应用4次后:")
    print(f"  应用次数: {exp.applied_count}")
    print(f"  成功率: {exp.success_rate:.2f}")

    assert exp.applied_count == 4
    assert exp.success_rate == 0.75

    print("\n✅ 经验应用测试通过")


def test_retrospective_system():
    """测试4：完整回溯系统"""
    print("\n" + "="*60)
    print("测试4：完整回溯系统")
    print("="*60)

    system = RetrospectiveSystem()

    # 模拟任务1：成功的任务
    experiences1 = system.retrospect_task(
        task_id="task-001",
        task_title="实现用户注册",
        events=[
            {'agent': 'Requester', 'type': 'complete'},
            {'agent': 'Developer', 'type': 'complete'},
            {'agent': 'CodeReviewer', 'type': 'approve'}
        ],
        artifacts=[
            {'type': 'requirement', 'agent': 'Requester'},
            {'type': 'code', 'agent': 'Developer'}
        ],
        iteration_count={'Requester': 1, 'Developer': 1, 'CodeReviewer': 1},
        success=True,
        duration=200.0
    )

    print(f"✅ 任务1复盘，提取 {len(experiences1)} 条经验")

    # 模拟任务2：迭代较多的任务
    experiences2 = system.retrospect_task(
        task_id="task-002",
        task_title="实现支付功能",
        events=[],
        artifacts=[],
        iteration_count={'Developer': 5, 'CodeReviewer': 5},
        success=True,
        duration=600.0
    )

    print(f"✅ 任务2复盘，提取 {len(experiences2)} 条经验")

    # 模拟任务3：失败的任务
    experiences3 = system.retrospect_task(
        task_id="task-003",
        task_title="实现复杂算法",
        events=[],
        artifacts=[],
        iteration_count={'Developer': 3, 'CodeReviewer': 3},
        success=False,
        duration=500.0
    )

    print(f"✅ 任务3复盘，提取 {len(experiences3)} 条经验")

    # 获取统计
    stats = system.get_statistics()
    print(f"\n系统统计:")
    print(f"  总经验数: {stats['total']}")
    print(f"  按类型: {stats['by_type']}")

    # 获取相关经验
    relevant = system.get_relevant_experiences(
        task_description="实现用户登录功能",
        agent_name="Developer",
        limit=3
    )

    print(f"\n相关经验: {len(relevant)} 条")
    for exp in relevant:
        print(f"  - {exp.title} (置信度: {exp.confidence})")

    print("\n✅ 完整回溯系统测试通过")


def test_global_system():
    """测试5：全局回溯系统"""
    print("\n" + "="*60)
    print("测试5：全局回溯系统")
    print("="*60)

    system = get_retrospective_system()

    # 添加一些经验
    system.retrospect_task(
        task_id="global-task-001",
        task_title="全局测试任务",
        events=[],
        artifacts=[],
        iteration_count={'Agent1': 1},
        success=True
    )

    stats = system.get_statistics()
    print(f"全局系统经验数: {stats['total']}")

    print("✅ 全局回溯系统测试通过")


def test_experience_persistence():
    """测试6：经验持久化"""
    print("\n" + "="*60)
    print("测试6：经验持久化")
    print("="*60)

    kb = ExperienceKnowledgeBase()

    # 添加经验
    import uuid
    for i in range(3):
        exp = Experience(
            experience_id=f"exp-{uuid.uuid4().hex[:12]}",
            experience_type=ExperienceType.SUCCESS,
            title=f"测试经验 {i+1}",
            description=f"这是第{i+1}条测试经验",
            context={'test': True},
            agents_involved=['TestAgent'],
            tags=['test']
        )
        kb.add_experience(exp)

    # 保存到文件
    filepath = "/tmp/test_experiences.json"
    kb.save_to_file(filepath)
    print(f"✅ 保存 {len(kb.experiences)} 条经验到文件")

    # 从文件加载
    loaded_kb = ExperienceKnowledgeBase.load_from_file(filepath)
    print(f"✅ 从文件加载 {len(loaded_kb.experiences)} 条经验")

    assert len(loaded_kb.experiences) == len(kb.experiences)

    # 清理
    os.remove(filepath)

    print("✅ 经验持久化测试通过")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("经验回溯系统测试")
    print("="*60)

    try:
        # 测试1：任务复盘
        test_task_retrospective()

        # 测试2：经验知识库
        test_experience_knowledge_base()

        # 测试3：经验应用
        test_experience_application()

        # 测试4：完整系统
        test_retrospective_system()

        # 测试5：全局系统
        test_global_system()

        # 测试6：持久化
        test_experience_persistence()

        # 总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        print("✅ 所有测试通过")
        print("\n关键验证点:")
        print("  ✅ 任务复盘和经验提取")
        print("  ✅ 经验知识库管理")
        print("  ✅ 经验搜索和过滤")
        print("  ✅ 最佳实践和反模式识别")
        print("  ✅ 经验应用和反馈")
        print("  ✅ 经验持久化")

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
