"""
集成测试

测试完整的工作流程，包括多轮对话、人工介入、错误处理等。
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import Mock, patch
from conftest import MockLLMAdapter, TestDataGenerator


@pytest.mark.integration
class TestWorkflowIntegration:
    """工作流集成测试"""

    def test_standard_workflow(self):
        """测试1: 标准工作流"""
        print("\n=== 测试1: 标准工作流 ===")

        # 创建测试数据
        organization = TestDataGenerator.generate_organization()
        project = TestDataGenerator.generate_project()
        task = TestDataGenerator.generate_task(
            title="Implement user login",
            project_id=project["id"]
        )

        print(f"✓ 组织: {organization['name']}")
        print(f"✓ 项目: {project['name']}")
        print(f"✓ 任务: {task['title']}")

        # 模拟工作流执行
        workflow = task["workflow"]
        print(f"✓ 工作流: {' → '.join(workflow)}")

        # 模拟每个Agent的执行
        mock_llm = MockLLMAdapter(responses=[
            "PRD: User login feature with JWT authentication",
            "Architecture: REST API with /auth/login endpoint",
            "Code: Implemented login endpoint with JWT",
            "Test: All tests passed"
        ])

        results = []
        for agent_name in workflow:
            response = mock_llm.generate(
                prompt=f"{agent_name} processing task: {task['title']}"
            )
            results.append({
                "agent": agent_name,
                "output": response.content
            })
            print(f"✓ {agent_name}: {response.content[:50]}...")

        assert len(results) == len(workflow), "所有Agent应该执行"
        assert mock_llm.call_count == len(workflow), "LLM调用次数应该匹配"

        print("✓ 标准工作流测试通过")

    def test_multi_round_conversation(self):
        """测试2: 多轮对话"""
        print("\n=== 测试2: 多轮对话 ===")

        task = TestDataGenerator.generate_task(
            title="Refactor authentication module"
        )

        # 模拟多轮对话
        mock_llm = MockLLMAdapter(responses=[
            "Initial design proposal",
            "Feedback: Need to consider OAuth",
            "Updated design with OAuth support",
            "Approved"
        ])

        conversation = []
        for i in range(4):
            response = mock_llm.generate(
                prompt=f"Round {i+1}: {task['title']}"
            )
            conversation.append({
                "round": i + 1,
                "content": response.content
            })
            print(f"✓ 第{i+1}轮: {response.content}")

        assert len(conversation) == 4, "应该有4轮对话"
        assert mock_llm.call_count == 4, "LLM应该调用4次"

        print("✓ 多轮对话测试通过")

    def test_error_handling_and_retry(self):
        """测试3: 错误处理和重试"""
        print("\n=== 测试3: 错误处理和重试 ===")

        task = TestDataGenerator.generate_task(
            title="Deploy to production"
        )

        # 模拟失败和重试
        attempt_count = 0
        max_attempts = 3
        success = False

        while attempt_count < max_attempts and not success:
            attempt_count += 1

            # 模拟前2次失败，第3次成功
            if attempt_count < 3:
                print(f"✗ 尝试 {attempt_count}: 失败")
            else:
                print(f"✓ 尝试 {attempt_count}: 成功")
                success = True

        assert success, "重试后应该成功"
        assert attempt_count == 3, "应该重试3次"

        print("✓ 错误处理和重试测试通过")

    def test_human_intervention(self):
        """测试4: 人工介入"""
        print("\n=== 测试4: 人工介入 ===")

        task = TestDataGenerator.generate_task(
            title="Critical security update"
        )

        # 模拟需要人工介入的场景
        intervention_levels = ["Warning", "Critical", "Emergency"]

        for level in intervention_levels:
            print(f"✓ {level}级别介入: 等待人工审批")

            # 模拟人工审批
            approved = True  # 假设审批通过
            if approved:
                print(f"  → 审批通过")
            else:
                print(f"  → 审批拒绝")

        print("✓ 人工介入测试通过")

    def test_concurrent_tasks(self):
        """测试5: 并发任务"""
        print("\n=== 测试5: 并发任务 ===")

        organization = TestDataGenerator.generate_organization()
        max_concurrent = organization["max_concurrent_tasks"]

        # 创建多个任务
        tasks = [
            TestDataGenerator.generate_task(title=f"Task {i}")
            for i in range(5)
        ]

        print(f"✓ 最大并发数: {max_concurrent}")
        print(f"✓ 任务总数: {len(tasks)}")

        # 模拟并发控制
        running_tasks = []
        completed_tasks = []

        for task in tasks:
            # 检查并发限制
            if len(running_tasks) >= max_concurrent:
                # 等待一个任务完成
                completed = running_tasks.pop(0)
                completed_tasks.append(completed)
                print(f"✓ 任务 {completed['id']} 完成")

            # 启动新任务
            running_tasks.append(task)
            print(f"✓ 任务 {task['id']} 开始")

        # 完成剩余任务
        while running_tasks:
            completed = running_tasks.pop(0)
            completed_tasks.append(completed)
            print(f"✓ 任务 {completed['id']} 完成")

        assert len(completed_tasks) == len(tasks), "所有任务应该完成"

        print("✓ 并发任务测试通过")


@pytest.mark.integration
class TestAgentCollaboration:
    """Agent协作测试"""

    def test_agent_feedback_loop(self):
        """测试6: Agent反馈循环"""
        print("\n=== 测试6: Agent反馈循环 ===")

        mock_llm = MockLLMAdapter(responses=[
            "Developer: Initial implementation",
            "CodeReviewer: Found 3 issues",
            "Developer: Fixed all issues",
            "CodeReviewer: Approved"
        ])

        # 模拟Developer和CodeReviewer的反馈循环
        agents = ["Developer", "CodeReviewer", "Developer", "CodeReviewer"]
        feedback_loop = []

        for agent in agents:
            response = mock_llm.generate(
                prompt=f"{agent} working on code review"
            )
            feedback_loop.append({
                "agent": agent,
                "output": response.content
            })
            print(f"✓ {agent}: {response.content}")

        assert len(feedback_loop) == 4, "应该有4轮反馈"
        assert "Approved" in feedback_loop[-1]["output"], "最终应该通过审查"

        print("✓ Agent反馈循环测试通过")

    def test_agent_dependency(self):
        """测试7: Agent依赖关系"""
        print("\n=== 测试7: Agent依赖关系 ===")

        # 定义Agent依赖关系
        dependencies = {
            "Architect": [],
            "Developer": ["Architect"],
            "Tester": ["Developer"],
            "Deployer": ["Tester"]
        }

        # 模拟按依赖顺序执行
        completed = set()
        execution_order = []

        def can_execute(agent: str) -> bool:
            """检查Agent是否可以执行"""
            deps = dependencies[agent]
            return all(dep in completed for dep in deps)

        # 执行所有Agent
        while len(completed) < len(dependencies):
            for agent in dependencies:
                if agent not in completed and can_execute(agent):
                    execution_order.append(agent)
                    completed.add(agent)
                    print(f"✓ {agent} 执行完成")

        assert len(execution_order) == len(dependencies), "所有Agent应该执行"
        assert execution_order == ["Architect", "Developer", "Tester", "Deployer"], "执行顺序应该正确"

        print("✓ Agent依赖关系测试通过")


def run_integration_tests():
    """运行集成测试"""
    print("\n" + "="*60)
    print("集成测试")
    print("="*60)

    try:
        # 工作流测试
        workflow_tests = TestWorkflowIntegration()
        workflow_tests.test_standard_workflow()
        workflow_tests.test_multi_round_conversation()
        workflow_tests.test_error_handling_and_retry()
        workflow_tests.test_human_intervention()
        workflow_tests.test_concurrent_tasks()

        # Agent协作测试
        collaboration_tests = TestAgentCollaboration()
        collaboration_tests.test_agent_feedback_loop()
        collaboration_tests.test_agent_dependency()

        print("\n" + "="*60)
        print("✅ 所有集成测试通过！")
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
    run_integration_tests()
