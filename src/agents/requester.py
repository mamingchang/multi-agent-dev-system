"""
Requester Agent
需求提出者：提出原始需求
"""
from typing import Dict, Any
from .base_agent import BaseAgent
from ..workflow.task import Task, TaskStatus


class RequesterAgent(BaseAgent):
    """需求提出者"""

    def __init__(self, name: str = "Requester", config: Dict[str, Any] = None):
        super().__init__(name, "需求提出者", config)

    def process(self, task: Task) -> Dict[str, Any]:
        """
        提出需求

        Args:
            task: 任务对象

        Returns:
            处理结果
        """
        print(f"\n[{self.name}] 提出需求: {task.title}")
        print(f"描述: {task.description}")

        # 更新任务状态
        task.update_status(TaskStatus.IN_REQUIREMENT, self.name)

        # 添加原始需求作为产物
        task.add_artifact(
            artifact_type="raw_requirement",
            content={
                'title': task.title,
                'description': task.description,
                'priority': self.config.get('default_priority', 'medium')
            },
            agent=self.name
        )

        result = {
            'success': True,
            'message': f'需求已提出: {task.title}',
            'next_agent': 'ProductManager'
        }

        return result
