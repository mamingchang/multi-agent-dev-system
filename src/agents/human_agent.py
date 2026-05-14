"""
Human Agent
人工Agent - 允许人类参与工作流
"""
from typing import Dict, Any, Optional
from datetime import datetime
import time

from .base_agent import BaseAgent
from src.decision_queue import DecisionQueue


# Task类型提示（避免循环导入）
Task = Dict[str, Any]


class HumanAgent(BaseAgent):
    """人工Agent"""

    def __init__(
        self,
        name: str,
        user_id: int,
        decision_queue: DecisionQueue,
        mode: str = 'async',
        config: Dict[str, Any] = None
    ):
        """
        初始化人工Agent

        Args:
            name: Agent名称
            user_id: 用户ID
            decision_queue: 决策队列
            mode: 交互模式 ('sync' 同步阻塞 或 'async' 异步队列)
            config: 配置
        """
        super().__init__(name, "人工Agent", config)
        self.user_id = user_id
        self.decision_queue = decision_queue
        self.mode = mode
        self.agent_type = 'human'

    def process(self, task: Task) -> Dict[str, Any]:
        """
        处理任务

        Args:
            task: 任务对象

        Returns:
            处理结果
        """
        print(f"\n[{self.name}] 人工Agent介入 (模式: {self.mode})")

        if self.mode == 'sync':
            return self._process_sync(task)
        else:
            return self._process_async(task)

    def _process_sync(self, task: Task) -> Dict[str, Any]:
        """
        同步模式：阻塞等待人工输入

        Args:
            task: 任务对象

        Returns:
            处理结果
        """
        print(f"[{self.name}] 同步模式：等待人工决策...")

        # 创建决策记录
        decision = self.decision_queue.create_decision(
            task_id=task.task_id,
            agent_name=self.name,
            decision_type='sync_input',
            context={
                'task_title': task.title,
                'task_description': task.description,
                'current_status': task.status.value,
                'artifacts': list(task.artifacts.keys()),
                'mode': 'sync'
            },
            assigned_to=self.user_id
        )

        # 通知需要决策
        self.decision_queue.notify_decision_needed(decision.id)

        # 阻塞等待决策（轮询）
        print(f"[{self.name}] 等待决策 {decision.id}...")
        print(f"  提示：在Web界面或CLI中处理决策 {decision.id}")

        timeout = self.config.get('sync_timeout', 300)  # 默认5分钟超时
        start_time = time.time()
        poll_interval = 2  # 每2秒检查一次

        while time.time() - start_time < timeout:
            # 刷新决策状态
            self.decision_queue.db.refresh(decision)

            if decision.status.value == 'resolved':
                print(f"[{self.name}] 决策已解决")
                response = decision.response

                # 添加反馈到任务
                task.add_feedback(
                    from_agent=self.name,
                    to_agent='System',
                    content=f"人工决策: {response.get('action', 'unknown')}",
                    feedback_type='approval' if response.get('approved', False) else 'rejection'
                )

                return {
                    'success': response.get('approved', True),
                    'message': response.get('message', '人工决策完成'),
                    'next_agent': response.get('next_agent'),
                    'decision_id': decision.id,
                    'response': response
                }

            time.sleep(poll_interval)

        # 超时
        self.decision_queue.check_timeout(decision.id, timeout_minutes=timeout // 60)
        return {
            'success': False,
            'message': f'决策超时（{timeout}秒）',
            'next_agent': None,
            'decision_id': decision.id
        }

    def _process_async(self, task: Task) -> Dict[str, Any]:
        """
        异步模式：创建待办决策，工作流暂停

        Args:
            task: 任务对象

        Returns:
            处理结果（pending状态）
        """
        print(f"[{self.name}] 异步模式：创建待办决策...")

        # 创建决策记录
        decision = self.decision_queue.create_decision(
            task_id=task.task_id,
            agent_name=self.name,
            decision_type='async_input',
            context={
                'task_title': task.title,
                'task_description': task.description,
                'current_status': task.status.value,
                'artifacts': list(task.artifacts.keys()),
                'feedback': task.feedback[-3:] if len(task.feedback) > 0 else [],  # 最近3条反馈
                'mode': 'async'
            },
            assigned_to=self.user_id
        )

        # 通知需要决策
        self.decision_queue.notify_decision_needed(decision.id)

        print(f"[{self.name}] 决策已创建: {decision.id}")
        print(f"  分配给用户: {self.user_id}")
        print(f"  工作流已暂停，等待人工处理")

        # 返回pending状态，工作流暂停
        return {
            'success': False,  # 标记为未完成
            'status': 'pending',  # 特殊状态：等待人工
            'message': f'等待人工决策 (决策ID: {decision.id})',
            'decision_id': decision.id,
            'next_agent': None  # 暂停工作流
        }

    def resume_from_decision(self, decision_id: int) -> Dict[str, Any]:
        """
        从决策恢复工作流

        Args:
            decision_id: 决策ID

        Returns:
            处理结果
        """
        decision = self.decision_queue.get_decision(decision_id)
        if not decision:
            return {
                'success': False,
                'message': f'决策 {decision_id} 不存在'
            }

        if decision.status.value != 'resolved':
            return {
                'success': False,
                'message': f'决策 {decision_id} 尚未解决'
            }

        response = decision.response

        return {
            'success': response.get('approved', True),
            'message': response.get('message', '人工决策完成'),
            'next_agent': response.get('next_agent'),
            'decision_id': decision_id,
            'response': response
        }


class HumanAgentFactory:
    """人工Agent工厂"""

    @staticmethod
    def create_agent(
        agent_name: str,
        user_id: int,
        decision_queue: DecisionQueue,
        mode: str = 'async',
        config: Dict[str, Any] = None
    ) -> HumanAgent:
        """
        创建人工Agent

        Args:
            agent_name: Agent名称
            user_id: 用户ID
            decision_queue: 决策队列
            mode: 交互模式
            config: 配置

        Returns:
            人工Agent实例
        """
        return HumanAgent(
            name=agent_name,
            user_id=user_id,
            decision_queue=decision_queue,
            mode=mode,
            config=config or {}
        )
