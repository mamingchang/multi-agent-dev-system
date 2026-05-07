"""
Task Definition
任务对象，在agents间流转
"""
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime


class TaskStatus(Enum):
    """任务状态"""
    CREATED = "created"
    IN_REQUIREMENT = "in_requirement"
    IN_DESIGN = "in_design"
    IN_DEVELOPMENT = "in_development"
    IN_REVIEW = "in_review"
    IN_TESTING = "in_testing"
    IN_DEPLOYMENT = "in_deployment"
    COMPLETED = "completed"
    REJECTED = "rejected"


class Task:
    """任务对象"""

    def __init__(self, task_id: str, title: str, description: str):
        self.task_id = task_id
        self.title = title
        self.description = description
        self.status = TaskStatus.CREATED
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.artifacts: Dict[str, Any] = {}  # 存储各阶段产物
        self.feedback: List[Dict] = []  # 存储反馈意见
        self.current_agent: Optional[str] = None

    def update_status(self, status: TaskStatus, agent: str) -> None:
        """更新任务状态"""
        self.status = status
        self.current_agent = agent
        self.updated_at = datetime.now()

    def add_artifact(self, artifact_type: str, content: Any, agent: str) -> None:
        """添加产物"""
        self.artifacts[artifact_type] = {
            'content': content,
            'created_by': agent,
            'created_at': datetime.now().isoformat()
        }
        self.updated_at = datetime.now()

    def add_feedback(self, from_agent: str, to_agent: str, content: str, feedback_type: str = "question") -> None:
        """添加反馈"""
        self.feedback.append({
            'from': from_agent,
            'to': to_agent,
            'content': content,
            'type': feedback_type,  # question, approval, rejection
            'timestamp': datetime.now().isoformat()
        })
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'current_agent': self.current_agent,
            'artifacts': self.artifacts,
            'feedback': self.feedback
        }

    def __repr__(self):
        return f"<Task(id='{self.task_id}', status='{self.status.value}')>"
