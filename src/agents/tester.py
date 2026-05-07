"""
Tester Agent
测试员：执行功能测试
"""
from typing import Dict, Any
import random
from .base_agent import BaseAgent
from ..workflow.task import Task, TaskStatus


class TesterAgent(BaseAgent):
    """测试员"""

    def __init__(self, name: str = "Tester", config: Dict[str, Any] = None):
        super().__init__(name, "测试员", config)

    def process(self, task: Task) -> Dict[str, Any]:
        """
        执行测试

        Args:
            task: 任务对象

        Returns:
            处理结果
        """
        print(f"\n[{self.name}] 开始功能测试...")

        prd = task.artifacts.get('prd', {}).get('content', {})
        code = task.artifacts.get('code', {}).get('content', {})

        # 模拟测试执行
        test_cases = [
            {'name': '用户注册测试', 'status': 'passed'},
            {'name': '用户登录测试', 'status': 'passed'},
            {'name': '数据查询测试', 'status': random.choice(['passed', 'failed'])},
            {'name': '权限验证测试', 'status': 'passed'},
            {'name': '性能测试', 'status': random.choice(['passed', 'failed'])}
        ]

        failed_tests = [tc for tc in test_cases if tc['status'] == 'failed']
        passed_tests = [tc for tc in test_cases if tc['status'] == 'passed']

        test_result = {
            'total_tests': len(test_cases),
            'passed': len(passed_tests),
            'failed': len(failed_tests),
            'test_cases': test_cases,
            'coverage': code.get('test_coverage', 80),
            'bugs_found': len(failed_tests),
            'all_passed': len(failed_tests) == 0
        }

        task.add_artifact(
            artifact_type="test_result",
            content=test_result,
            agent=self.name
        )

        task.update_status(TaskStatus.IN_TESTING, self.name)

        print(f"[{self.name}] 测试完成")
        print(f"  - 总测试数: {test_result['total_tests']}")
        print(f"  - 通过: {test_result['passed']}")
        print(f"  - 失败: {test_result['failed']}")
        print(f"  - 测试覆盖率: {test_result['coverage']}%")

        if not test_result['all_passed']:
            task.add_feedback(
                from_agent=self.name,
                to_agent='Developer',
                content=f"发现{len(failed_tests)}个测试失败: {[t['name'] for t in failed_tests]}",
                feedback_type='rejection'
            )
            result = {
                'success': False,
                'message': '测试未通过',
                'next_agent': 'Developer',
                'test_result': test_result
            }
        else:
            task.add_feedback(
                from_agent=self.name,
                to_agent='Developer',
                content='所有测试通过',
                feedback_type='approval'
            )
            result = {
                'success': True,
                'message': '测试通过',
                'next_agent': 'DevOps',
                'test_result': test_result
            }

        return result
