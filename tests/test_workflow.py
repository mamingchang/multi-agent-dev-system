"""
Test Workflow
工作流测试用例
"""
import unittest
from src.orchestrator import Orchestrator
from src.workflow.task import Task, TaskStatus


class TestWorkflow(unittest.TestCase):
    """工作流测试"""

    def setUp(self):
        """测试前准备"""
        self.orchestrator = Orchestrator()

    def test_create_task(self):
        """测试创建任务"""
        task = Task(
            task_id="TEST-001",
            title="测试任务",
            description="这是一个测试任务"
        )
        self.assertEqual(task.task_id, "TEST-001")
        self.assertEqual(task.status, TaskStatus.CREATED)

    def test_orchestrator_initialization(self):
        """测试协调器初始化"""
        self.assertIsNotNone(self.orchestrator)
        agents = self.orchestrator.list_agents()
        self.assertEqual(len(agents), 7)
        self.assertIn('Developer', agents)
        self.assertIn('Tester', agents)

    def test_workflow_execution(self):
        """测试工作流执行"""
        task = Task(
            task_id="TEST-002",
            title="测试工作流",
            description="测试完整工作流执行"
        )
        result = self.orchestrator.execute_workflow(task)
        self.assertIsNotNone(result)
        self.assertIn('success', result)
        self.assertIn('task', result)


if __name__ == '__main__':
    unittest.main()
