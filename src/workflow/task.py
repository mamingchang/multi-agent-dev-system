"""
Task Definition
任务对象，在agents间流转

改进：
- 集成对话系统（Conversation）
- 支持多轮迭代
- 记录需求锚点
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
    FAILED = "failed"


class Task:
    """
    任务对象

    改进：
    - 集成Conversation对话系统
    - 记录需求锚点（原始需求，不可变）
    - 支持多轮迭代
    """

    def __init__(self, task_id: str, title: str, description: str):
        self.task_id = task_id
        self.title = title
        self.description = description
        self.status = TaskStatus.CREATED
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

        # 产物存储（改为列表，支持多版本）
        self.artifacts: List[Dict[str, Any]] = []

        # 旧的feedback保留兼容性
        self.feedback: List[Dict] = []

        # 当前处理的Agent
        self.current_agent: Optional[str] = None

        # 需求锚点（3层结构，原始需求，不可变）
        self.requirement_anchor = {
            'core': title,  # 核心需求：绝对不可变
            'detailed': description,  # 详细需求：可澄清，不可扩展
            'constraints': [],  # 约束条件：技术/时间/资源限制
            'created_at': datetime.now().isoformat()
        }

        # 对话系统（延迟导入避免循环依赖）
        self.conversation = None
        self._init_conversation()

        # 迭代计数器（记录每个Agent执行次数）
        self.iteration_count: Dict[str, int] = {}

    def _init_conversation(self):
        """初始化对话系统"""
        try:
            from ..conversation import Conversation
            self.conversation = Conversation()
        except ImportError:
            # 如果导入失败，使用None（兼容旧代码）
            self.conversation = None

    def update_status(self, status: TaskStatus, agent: str) -> None:
        """更新任务状态"""
        self.status = status
        self.current_agent = agent
        self.updated_at = datetime.now()

        # 增加迭代计数
        self.iteration_count[agent] = self.iteration_count.get(agent, 0) + 1

    def add_artifact(self, artifact_type: str, content: Any, agent: str) -> None:
        """
        添加产物

        改进：使用列表存储，支持多版本
        """
        artifact = {
            'type': artifact_type,
            'content': content,
            'agent': agent,
            'version': self.iteration_count.get(agent, 1),
            'timestamp': datetime.now().isoformat()
        }

        self.artifacts.append(artifact)
        self.updated_at = datetime.now()

    def get_latest_artifact(self, artifact_type: str) -> Optional[Dict[str, Any]]:
        """
        获取指定类型的最新产物

        Args:
            artifact_type: 产物类型

        Returns:
            Dict: 产物对象，如果不存在返回None
        """
        # 反向查找最新的
        for artifact in reversed(self.artifacts):
            if artifact['type'] == artifact_type:
                return artifact
        return None

    def add_feedback(self, from_agent: str, to_agent: str, content: str, feedback_type: str = "question") -> None:
        """
        添加反馈（旧方法，保留兼容性）

        建议使用conversation.add_message()代替
        """
        self.feedback.append({
            'from': from_agent,
            'to': to_agent,
            'content': content,
            'type': feedback_type,
            'timestamp': datetime.now().isoformat()
        })
        self.updated_at = datetime.now()

    def get_requirement_anchor(self) -> Dict[str, Any]:
        """
        获取需求锚点

        需求锚点是原始需求，在整个任务过程中不可变。
        用于确保讨论不偏离原始需求。

        Returns:
            Dict: 需求锚点（3层结构）
            {
                'core': 核心需求（绝对不可变）,
                'detailed': 详细需求（可澄清，不可扩展）,
                'constraints': 约束条件列表,
                'created_at': 创建时间
            }
        """
        return self.requirement_anchor

    def add_constraint(self, constraint: str) -> None:
        """
        添加约束条件

        约束条件可以在任务执行过程中添加，但不能修改核心需求。

        Args:
            constraint: 约束条件描述
        """
        self.requirement_anchor['constraints'].append({
            'content': constraint,
            'added_at': datetime.now().isoformat()
        })

    def check_requirement_deviation(self, proposed_solution: str) -> Dict[str, Any]:
        """
        检查方案是否偏离需求锚点

        这是一个简化版本，实际应该使用LLM进行语义分析。

        Args:
            proposed_solution: 提议的解决方案

        Returns:
            Dict: 检查结果
            {
                'is_deviated': bool,  # 是否偏离
                'reason': str,  # 偏离原因
                'severity': str  # 严重程度: low/medium/high
            }
        """
        # 简化版本：只检查是否完全为空或过短
        if not proposed_solution or len(proposed_solution.strip()) < 10:
            return {
                'is_deviated': True,
                'reason': '方案内容过短或为空',
                'severity': 'high'
            }

        # 默认不偏离（避免误判）
        # 实际应该使用LLM进行语义分析
        return {
            'is_deviated': False,
            'reason': '方案符合需求',
            'severity': 'low'
        }

    def get_iteration_count(self, agent_name: str) -> int:
        """
        获取指定Agent的迭代次数

        Args:
            agent_name: Agent名称

        Returns:
            int: 迭代次数
        """
        return self.iteration_count.get(agent_name, 0)

    def is_first_iteration(self, agent_name: str) -> bool:
        """
        判断是否是首次执行

        Args:
            agent_name: Agent名称

        Returns:
            bool: 是否首次执行
        """
        return self.get_iteration_count(agent_name) == 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'current_agent': self.current_agent,
            'artifacts': self.artifacts,
            'feedback': self.feedback,
            'requirement_anchor': self.requirement_anchor,
            'iteration_count': self.iteration_count
        }

        # 如果有对话系统，添加对话历史
        if self.conversation:
            result['conversation'] = self.conversation.to_dict()

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """
        从字典创建Task对象

        Args:
            data: 任务数据字典

        Returns:
            Task: 任务对象
        """
        # 创建基础Task对象
        task = cls(
            task_id=data['task_id'],
            title=data['title'],
            description=data['description']
        )

        # 恢复状态
        task.status = TaskStatus(data['status'])
        task.current_agent = data.get('current_agent')

        # 恢复时间戳
        if 'created_at' in data:
            task.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            task.updated_at = datetime.fromisoformat(data['updated_at'])

        # 恢复产物和反馈
        task.artifacts = data.get('artifacts', [])
        task.feedback = data.get('feedback', [])

        # 恢复需求锚点
        if 'requirement_anchor' in data:
            task.requirement_anchor = data['requirement_anchor']

        # 恢复迭代计数
        task.iteration_count = data.get('iteration_count', {})

        # 恢复对话系统（如果有）
        if 'conversation' in data and task.conversation:
            # 这里需要Conversation类支持from_dict，暂时跳过
            pass

        return task

    def __repr__(self):
        return f"<Task(id='{self.task_id}', status='{self.status.value}')>"
