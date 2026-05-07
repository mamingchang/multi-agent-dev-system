"""
Product Manager Agent
产品经理：将原始需求细化为PRD
"""
from typing import Dict, Any
from .base_agent import BaseAgent
from ..workflow.task import Task, TaskStatus


class ProductManagerAgent(BaseAgent):
    """产品经理"""

    def __init__(self, name: str = "ProductManager", config: Dict[str, Any] = None):
        super().__init__(name, "产品经理", config)

    def process(self, task: Task) -> Dict[str, Any]:
        """
        细化需求，编写PRD

        Args:
            task: 任务对象

        Returns:
            处理结果
        """
        print(f"\n[{self.name}] 分析需求并编写PRD...")

        raw_req = task.artifacts.get('raw_requirement', {}).get('content', {})

        # 模拟PRD编写
        prd = {
            'title': raw_req.get('title', task.title),
            'background': f"基于需求: {raw_req.get('description', task.description)}",
            'user_stories': [
                "作为用户，我希望能够...",
                "作为管理员，我需要..."
            ],
            'functional_requirements': [
                "系统应该支持...",
                "界面需要展示..."
            ],
            'non_functional_requirements': {
                'performance': '响应时间<200ms',
                'security': '需要身份验证',
                'scalability': '支持1000并发用户'
            },
            'acceptance_criteria': [
                "功能正常运行",
                "通过所有测试用例"
            ]
        }

        task.add_artifact(
            artifact_type="prd",
            content=prd,
            agent=self.name
        )

        print(f"[{self.name}] PRD已完成")
        print(f"  - 用户故事: {len(prd['user_stories'])}个")
        print(f"  - 功能需求: {len(prd['functional_requirements'])}个")

        result = {
            'success': True,
            'message': 'PRD已完成',
            'next_agent': 'Architect',
            'prd': prd
        }

        return result
