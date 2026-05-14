"""
Agent扩展测试

测试场景：
1. Agent注册和注销
2. Agent搜索
3. 工作流选择
4. 工作流验证
5. 依赖图生成
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.registry import agent_registry, AgentRegistry
from src.agents.capability import AgentCapability, AgentScope
from src.agents.workflow_selector import WorkflowSelector


def test_agent_registration():
    """测试1: Agent注册和注销"""
    print("\n=== 测试1: Agent注册和注销 ===")

    registry = AgentRegistry()

    # 创建自定义Agent
    custom_agent = AgentCapability(
        name="CustomAgent",
        display_name="自定义Agent",
        description="测试用的自定义Agent",
        version="1.0.0",
        author="Test",
        task_types=["custom"],
        tech_stacks=["Python"],
        domains=["testing"],
        required_inputs=[],
        output_artifacts=["custom_output"],
        depends_on=[]
    )

    # 注册Agent
    success = registry.register(custom_agent)
    assert success, "注册应该成功"
    print(f"✓ 注册成功: {custom_agent.name}")

    # 获取Agent
    agent = registry.get("CustomAgent")
    assert agent is not None, "应该能获取到Agent"
    assert agent.name == "CustomAgent", "Agent名称应该匹配"
    print(f"✓ 获取成功: {agent.display_name}")

    # 重复注册（应该失败）
    success = registry.register(custom_agent)
    assert not success, "重复注册应该失败"
    print("✓ 重复注册被拒绝")

    # 注销Agent
    success = registry.unregister("CustomAgent")
    assert success, "注销应该成功"
    print("✓ 注销成功")

    # 再次获取（应该为None）
    agent = registry.get("CustomAgent")
    assert agent is None, "注销后应该获取不到"
    print("✓ 注销后无法获取")

    print("✓ Agent注册和注销测试通过")


def test_agent_search():
    """测试2: Agent搜索"""
    print("\n=== 测试2: Agent搜索 ===")

    # 按任务类型搜索
    agents = agent_registry.search(task_type="feature")
    print(f"✓ 任务类型'feature': 找到 {len(agents)} 个Agent")
    assert len(agents) > 0, "应该找到Agent"

    # 按技术栈搜索
    agents = agent_registry.search(tech_stack="Python")
    print(f"✓ 技术栈'Python': 找到 {len(agents)} 个Agent")
    assert len(agents) > 0, "应该找到Agent"

    # 按领域搜索
    agents = agent_registry.search(domain="coding")
    print(f"✓ 领域'coding': 找到 {len(agents)} 个Agent")
    assert len(agents) > 0, "应该找到Agent"

    # 按标签搜索
    agents = agent_registry.search(tags=["builtin"])
    print(f"✓ 标签'builtin': 找到 {len(agents)} 个Agent")
    assert len(agents) > 0, "应该找到Agent"

    print("✓ Agent搜索测试通过")


def test_workflow_selection():
    """测试3: 工作流选择"""
    print("\n=== 测试3: 工作流选择 ===")

    selector = WorkflowSelector()

    # 测试不同任务类型的工作流选择
    test_cases = [
        ("feature", ["Python", "FastAPI"], ["ProductManager", "Architect", "Developer", "CodeReviewer", "Tester"]),
        ("bugfix", ["Python"], ["Developer", "CodeReviewer", "Tester"]),
        ("deployment", ["Docker"], ["Deployer"]),
    ]

    for task_type, tech_stack, expected_agents in test_cases:
        result = selector.select_workflow(
            task_description=f"Test {task_type} task",
            task_type=task_type,
            project_tech_stack=tech_stack,
            organization_id=1
        )

        print(f"✓ {task_type}: {' → '.join(result['workflow'])}")
        assert len(result["workflow"]) > 0, "工作流不应该为空"

        # 检查是否包含期望的Agent
        for agent in expected_agents:
            if agent in [a for a in agent_registry.list_all() if a.name == agent]:
                assert agent in result["workflow"], f"应该包含{agent}"

    print("✓ 工作流选择测试通过")


def test_workflow_validation():
    """测试4: 工作流验证"""
    print("\n=== 测试4: 工作流验证 ===")

    # 有效的工作流
    valid_workflow = ["ProductManager", "Architect", "Developer", "Tester"]
    result = agent_registry.validate_workflow(valid_workflow)
    assert result["valid"], "有效的工作流应该通过验证"
    print(f"✓ 有效工作流: {' → '.join(valid_workflow)}")

    # 包含不存在的Agent
    invalid_workflow = ["ProductManager", "NonExistentAgent", "Developer"]
    result = agent_registry.validate_workflow(invalid_workflow)
    assert not result["valid"], "包含不存在Agent的工作流应该验证失败"
    print(f"✓ 无效工作流被拒绝: {result['errors'][0]}")

    # 依赖关系警告
    workflow_with_warnings = ["Developer", "ProductManager"]  # 顺序不对
    result = agent_registry.validate_workflow(workflow_with_warnings)
    print(f"✓ 依赖警告: {len(result['warnings'])} 个警告")

    print("✓ 工作流验证测试通过")


def test_dependency_graph():
    """测试5: 依赖图生成"""
    print("\n=== 测试5: 依赖图生成 ===")

    # 获取依赖图
    graph = agent_registry.get_dependency_graph()
    print(f"✓ 依赖图包含 {len(graph)} 个Agent")

    # 检查依赖关系
    assert "ProductManager" in graph, "应该包含ProductManager"
    assert "Developer" in graph, "应该包含Developer"

    # ProductManager没有依赖
    assert len(graph["ProductManager"]) == 0, "ProductManager不应该有依赖"
    print("✓ ProductManager: 无依赖")

    # Developer依赖Architect
    assert "Architect" in graph["Developer"], "Developer应该依赖Architect"
    print(f"✓ Developer: 依赖 {', '.join(graph['Developer'])}")

    print("✓ 依赖图生成测试通过")


def test_topological_sort():
    """测试6: 拓扑排序"""
    print("\n=== 测试6: 拓扑排序 ===")

    # 测试拓扑排序
    agents = ["Tester", "Developer", "Architect", "ProductManager"]
    sorted_agents = agent_registry.topological_sort(agents)

    print(f"✓ 原始顺序: {' → '.join(agents)}")
    print(f"✓ 排序后: {' → '.join(sorted_agents)}")

    # 验证顺序
    pm_index = sorted_agents.index("ProductManager")
    arch_index = sorted_agents.index("Architect")
    dev_index = sorted_agents.index("Developer")
    test_index = sorted_agents.index("Tester")

    assert pm_index < arch_index, "ProductManager应该在Architect之前"
    assert arch_index < dev_index, "Architect应该在Developer之前"
    assert dev_index < test_index, "Developer应该在Tester之前"

    print("✓ 拓扑排序测试通过")


def test_workflow_adjustment():
    """测试7: 工作流调整"""
    print("\n=== 测试7: 工作流调整 ===")

    selector = WorkflowSelector()

    original_workflow = ["ProductManager", "Developer", "Tester"]
    print(f"✓ 原始工作流: {' → '.join(original_workflow)}")

    # 添加Agent
    result = selector.adjust_workflow(
        current_workflow=original_workflow,
        current_step=1,
        adjustment_type="add",
        agent_name="CodeReviewer",
        reason="需要代码审查"
    )

    print(f"✓ 添加CodeReviewer后: {' → '.join(result['new_workflow'])}")
    assert "CodeReviewer" in result["new_workflow"], "应该包含CodeReviewer"

    # 跳过Agent
    result = selector.adjust_workflow(
        current_workflow=original_workflow,
        current_step=1,
        adjustment_type="skip",
        reason="跳过Developer"
    )

    print(f"✓ 跳过Developer后: {' → '.join(result['new_workflow'])}")
    assert len(result["new_workflow"]) == 2, "应该减少一个Agent"

    print("✓ 工作流调整测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Agent扩展测试")
    print("="*60)

    try:
        test_agent_registration()
        test_agent_search()
        test_workflow_selection()
        test_workflow_validation()
        test_dependency_graph()
        test_topological_sort()
        test_workflow_adjustment()

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
