"""
Agent协作模式测试

测试场景：
1. DAG并行执行
2. 任务分解
3. Agent投票
4. 冲突解决
"""

import pytest
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.workflow.dag_executor import DAGExecutor, TaskStatus
from src.workflow.task_decomposer import TaskDecomposer, TaskComplexity
from src.workflow.voting_system import VotingSystem, VoteOption, ConflictResolver


class TestDAGExecutor:
    """DAG执行器测试"""

    @pytest.mark.asyncio
    async def test_simple_dag(self):
        """测试简单DAG执行"""
        executor = DAGExecutor()

        # 定义执行函数
        async def task_a(deps):
            return "Result A"

        async def task_b(deps):
            return f"Result B (depends on {deps.get('A')})"

        async def task_c(deps):
            return f"Result C (depends on {deps.get('B')})"

        # 添加节点
        executor.add_node("A", dependencies=[], executor=task_a)
        executor.add_node("B", dependencies=["A"], executor=task_b)
        executor.add_node("C", dependencies=["B"], executor=task_c)

        # 执行
        results = await executor.execute()

        # 验证
        assert results["A"]["status"] == "completed"
        assert results["B"]["status"] == "completed"
        assert results["C"]["status"] == "completed"
        assert "Result A" in results["A"]["result"]

        print("✅ 简单DAG执行测试通过")

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """测试并行执行"""
        executor = DAGExecutor()

        execution_order = []

        async def task_a(deps):
            execution_order.append("A")
            await asyncio.sleep(0.1)
            return "A"

        async def task_b(deps):
            execution_order.append("B")
            await asyncio.sleep(0.1)
            return "B"

        async def task_c(deps):
            execution_order.append("C")
            return "C"

        # A和B无依赖，应该并行执行
        # C依赖A和B
        executor.add_node("A", dependencies=[], executor=task_a)
        executor.add_node("B", dependencies=[], executor=task_b)
        executor.add_node("C", dependencies=["A", "B"], executor=task_c)

        results = await executor.execute()

        # 验证A和B并行执行（都在C之前）
        assert execution_order.index("C") > execution_order.index("A")
        assert execution_order.index("C") > execution_order.index("B")

        print("✅ 并行执行测试通过")

    def test_topological_sort(self):
        """测试拓扑排序"""
        executor = DAGExecutor()

        executor.add_node("Requester", dependencies=[])
        executor.add_node("Architect", dependencies=["Requester"])
        executor.add_node("ProductManager", dependencies=["Requester"])
        executor.add_node("Developer", dependencies=["Architect"])
        executor.add_node("Tester", dependencies=["Developer"])

        execution_plan = executor.topological_sort()

        # 验证执行顺序
        assert execution_plan[0] == ["Requester"]
        assert set(execution_plan[1]) == {"Architect", "ProductManager"}
        assert execution_plan[2] == ["Developer"]
        assert execution_plan[3] == ["Tester"]

        print("✅ 拓扑排序测试通过")

    def test_circular_dependency_detection(self):
        """测试循环依赖检测"""
        executor = DAGExecutor()

        executor.add_node("A", dependencies=["B"])
        executor.add_node("B", dependencies=["C"])
        executor.add_node("C", dependencies=["A"])  # 循环依赖

        # 应该抛出异常
        with pytest.raises(ValueError, match="Circular dependency"):
            executor.topological_sort()

        print("✅ 循环依赖检测测试通过")

    def test_visualization(self):
        """测试DAG可视化"""
        executor = DAGExecutor()

        executor.add_node("A", dependencies=[])
        executor.add_node("B", dependencies=["A"])
        executor.add_node("C", dependencies=["A"])
        executor.add_node("D", dependencies=["B", "C"])

        visualization = executor.visualize()

        assert "Layer 0: A" in visualization
        assert "Layer 1:" in visualization
        assert "Layer 2: D" in visualization

        print("✅ DAG可视化测试通过")


class TestTaskDecomposer:
    """任务分解器测试"""

    @pytest.mark.asyncio
    async def test_simple_task_analysis(self):
        """测试简单任务分析"""
        decomposer = TaskDecomposer()

        suggestion = await decomposer.analyze("修复登录按钮的样式问题")

        assert suggestion.complexity == TaskComplexity.SIMPLE
        assert suggestion.should_decompose is False

        print("✅ 简单任务分析测试通过")

    @pytest.mark.asyncio
    async def test_complex_task_analysis(self):
        """测试复杂任务分析"""
        decomposer = TaskDecomposer()

        suggestion = await decomposer.analyze(
            "开发一个完整的用户管理系统，包括用户注册、登录、权限管理、角色管理、审计日志等功能"
        )

        assert suggestion.complexity == TaskComplexity.COMPLEX
        assert suggestion.should_decompose is True
        assert len(suggestion.subtasks) > 0

        print("✅ 复杂任务分析测试通过")

    @pytest.mark.asyncio
    async def test_subtask_creation(self):
        """测试子任务创建"""
        decomposer = TaskDecomposer()

        suggestion = await decomposer.analyze("开发用户管理系统")
        subtasks = await decomposer.create_subtasks(suggestion, "task-123")

        assert len(subtasks) > 0
        assert all("task-123" in st["id"] for st in subtasks)
        assert all("parent_id" in st for st in subtasks)

        print("✅ 子任务创建测试通过")

    def test_execution_order(self):
        """测试子任务执行顺序"""
        from src.workflow.task_decomposer import SubTask

        decomposer = TaskDecomposer()

        subtasks = [
            SubTask("1", "需求分析", "", "Requester", [], 30),
            SubTask("2", "架构设计", "", "Architect", ["1"], 60),
            SubTask("3", "开发", "", "Developer", ["2"], 120),
            SubTask("4", "测试", "", "Tester", ["3"], 60),
        ]

        execution_order = decomposer.get_execution_order(subtasks)

        assert execution_order[0] == ["1"]
        assert execution_order[1] == ["2"]
        assert execution_order[2] == ["3"]
        assert execution_order[3] == ["4"]

        print("✅ 子任务执行顺序测试通过")


class TestVotingSystem:
    """投票系统测试"""

    def test_simple_voting(self):
        """测试简单投票"""
        voting = VotingSystem(threshold=0.6)

        voting.add_vote("Architect", VoteOption.APPROVE, "技术方案可行")
        voting.add_vote("Developer", VoteOption.APPROVE, "可以实现")
        voting.add_vote("Tester", VoteOption.APPROVE, "测试覆盖充分")

        result = voting.calculate_result()

        assert result.passed is True
        assert result.consensus_level > 0.9

        print("✅ 简单投票测试通过")

    def test_weighted_voting(self):
        """测试加权投票"""
        voting = VotingSystem(threshold=0.6)

        # Architect权重高
        voting.set_agent_weight("Architect", 3.0)
        voting.set_agent_weight("Developer", 2.0)
        voting.set_agent_weight("Tester", 1.0)

        # Architect反对，其他同意
        voting.add_vote("Architect", VoteOption.REJECT, "架构有问题")
        voting.add_vote("Developer", VoteOption.APPROVE, "可以实现")
        voting.add_vote("Tester", VoteOption.APPROVE, "测试OK")

        result = voting.calculate_result()

        # 由于Architect权重高且反对，应该不通过
        assert result.passed is False

        print("✅ 加权投票测试通过")

    def test_conditional_voting(self):
        """测试有条件投票"""
        voting = VotingSystem(threshold=0.6)

        voting.add_vote("Architect", VoteOption.APPROVE, "可行")
        voting.add_vote("Developer", VoteOption.CONDITIONAL, "需要优化", ["添加缓存", "优化查询"])
        voting.add_vote("Tester", VoteOption.APPROVE, "OK")

        result = voting.calculate_result()

        # 有条件同意算0.5权重，应该能通过
        assert result.passed is True
        assert len(result.conflicts) > 0  # 有条件被记录为冲突

        print("✅ 有条件投票测试通过")

    def test_conflict_identification(self):
        """测试冲突识别"""
        voting = VotingSystem(threshold=0.6)

        voting.set_agent_weight("Architect", 3.0)

        voting.add_vote("Architect", VoteOption.REJECT, "架构不合理")
        voting.add_vote("Developer", VoteOption.APPROVE, "可以实现")

        result = voting.calculate_result()

        assert len(result.conflicts) > 0
        assert "Architect" in result.conflicts[0]

        print("✅ 冲突识别测试通过")

    def test_voting_summary(self):
        """测试投票摘要"""
        voting = VotingSystem()

        voting.add_vote("Architect", VoteOption.APPROVE, "可行")
        voting.add_vote("Developer", VoteOption.REJECT, "实现困难")

        summary = voting.get_summary()

        assert "投票结果摘要" in summary
        assert "Architect" in summary
        assert "Developer" in summary

        print("✅ 投票摘要测试通过")


class TestConflictResolver:
    """冲突解决器测试"""

    @pytest.mark.asyncio
    async def test_conflict_analysis(self):
        """测试冲突分析"""
        voting = VotingSystem()

        voting.add_vote("Architect", VoteOption.REJECT, "架构问题")
        voting.add_vote("Developer", VoteOption.APPROVE, "可以实现")

        result = voting.calculate_result()

        resolver = ConflictResolver()
        analysis = await resolver.analyze_conflict(result)

        assert analysis["has_conflict"] is True
        assert len(analysis["suggestions"]) > 0

        print("✅ 冲突分析测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Agent协作模式测试")
    print("="*60 + "\n")

    # DAG执行器测试
    print("【DAG执行器测试】")
    dag_tests = TestDAGExecutor()
    asyncio.run(dag_tests.test_simple_dag())
    asyncio.run(dag_tests.test_parallel_execution())
    dag_tests.test_topological_sort()
    dag_tests.test_circular_dependency_detection()
    dag_tests.test_visualization()

    # 任务分解器测试
    print("\n【任务分解器测试】")
    decomposer_tests = TestTaskDecomposer()
    asyncio.run(decomposer_tests.test_simple_task_analysis())
    asyncio.run(decomposer_tests.test_complex_task_analysis())
    asyncio.run(decomposer_tests.test_subtask_creation())
    decomposer_tests.test_execution_order()

    # 投票系统测试
    print("\n【投票系统测试】")
    voting_tests = TestVotingSystem()
    voting_tests.test_simple_voting()
    voting_tests.test_weighted_voting()
    voting_tests.test_conditional_voting()
    voting_tests.test_conflict_identification()
    voting_tests.test_voting_summary()

    # 冲突解决器测试
    print("\n【冲突解决器测试】")
    resolver_tests = TestConflictResolver()
    asyncio.run(resolver_tests.test_conflict_analysis())

    print("\n" + "="*60)
    print("✅ 所有Agent协作模式测试通过！")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()
