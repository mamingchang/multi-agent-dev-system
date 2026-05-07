"""
Code Reviewer Agent
代码审查员：审查代码质量
"""
from typing import Dict, Any
import random
from .base_agent import BaseAgent
from ..workflow.task import Task, TaskStatus


class CodeReviewerAgent(BaseAgent):
    """代码审查员"""

    def __init__(self, name: str = "CodeReviewer", config: Dict[str, Any] = None):
        super().__init__(name, "代码审查员", config)

    def process(self, task: Task) -> Dict[str, Any]:
        """
        审查代码质量

        Args:
            task: 任务对象

        Returns:
            处理结果
        """
        print(f"\n[{self.name}] 开始代码审查...")

        code = task.artifacts.get('code', {}).get('content', {})

        # 模拟代码审查
        issues = []
        suggestions = []

        # 随机生成一些审查意见
        if random.random() > 0.7:
            issues.append({
                'file': 'src/main.py',
                'line': 15,
                'severity': 'medium',
                'message': '建议添加错误处理'
            })

        if random.random() > 0.6:
            suggestions.append({
                'file': 'src/models.py',
                'message': '可以使用Pydantic模型提高类型安全'
            })

        review_result = {
            'overall_quality': random.choice(['excellent', 'good', 'needs_improvement']),
            'code_style': 'PEP8 compliant',
            'security_issues': len([i for i in issues if i.get('severity') == 'high']),
            'issues': issues,
            'suggestions': suggestions,
            'approved': len(issues) == 0 or all(i.get('severity') != 'high' for i in issues)
        }

        task.add_artifact(
            artifact_type="code_review",
            content=review_result,
            agent=self.name
        )

        task.update_status(TaskStatus.IN_REVIEW, self.name)

        print(f"[{self.name}] 代码审查完成")
        print(f"  - 整体质量: {review_result['overall_quality']}")
        print(f"  - 发现问题: {len(issues)}个")
        print(f"  - 建议: {len(suggestions)}个")
        print(f"  - 审查结果: {'通过' if review_result['approved'] else '需要修改'}")

        if not review_result['approved']:
            task.add_feedback(
                from_agent=self.name,
                to_agent='Developer',
                content=f"发现{len(issues)}个问题，请修复后重新提交",
                feedback_type='rejection'
            )
            result = {
                'success': False,
                'message': '代码审查未通过',
                'next_agent': 'Developer',
                'review': review_result
            }
        else:
            task.add_feedback(
                from_agent=self.name,
                to_agent='Developer',
                content='代码质量良好，审查通过',
                feedback_type='approval'
            )
            result = {
                'success': True,
                'message': '代码审查通过',
                'next_agent': 'Tester',
                'review': review_result
            }

        return result
