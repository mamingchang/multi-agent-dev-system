"""
Enhanced Orchestrator
增强的协调器：支持人工Agent、权限检查、事件日志
"""
from typing import Dict, Any, List, Optional
import time
from datetime import datetime

from .agents.base_agent import BaseAgent
from .agents.requester import RequesterAgent
from .agents.product_manager import ProductManagerAgent
from .agents.architect import ArchitectAgent
from .agents.developer import DeveloperAgent
from .agents.code_reviewer import CodeReviewerAgent
from .agents.tester import TesterAgent
from .agents.devops import DevOpsAgent
from .agents.human_agent import HumanAgent, HumanAgentFactory
from .workflow.task import Task, TaskStatus
from .project_manager import ProjectManager, PermissionError
from .decision_queue import DecisionQueue
from .event_logger import EventLogger


class EnhancedOrchestrator:
    """增强的协调器"""

    def __init__(
        self,
        project_manager: ProjectManager,
        decision_queue: DecisionQueue,
        event_logger: EventLogger,
        config: Dict[str, Any] = None
    ):
        """
        初始化协调器

        Args:
            project_manager: 项目管理器
            decision_queue: 决策队列
            event_logger: 事件日志记录器
            config: 配置
        """
        self.config = config or {}
        self.project_manager = project_manager
        self.decision_queue = decision_queue
        self.event_logger = event_logger
        self.agents: Dict[str, BaseAgent] = {}
        self.max_iterations = self.config.get('max_iterations', 10)
        self.human_agent_config = self.config.get('human_agents', {})  # 配置哪些Agent使用人工模式
        self._initialize_agents()

    def _initialize_agents(self) -> None:
        """初始化所有AI Agent"""
        self.agents = {
            'Requester': RequesterAgent(),
            'ProductManager': ProductManagerAgent(),
            'Architect': ArchitectAgent(),
            'Developer': DeveloperAgent(),
            'CodeReviewer': CodeReviewerAgent(),
            'Tester': TesterAgent(),
            'DevOps': DevOpsAgent(config={'environment': 'production'})
        }

    def execute_workflow(
        self,
        task: Task,
        project_id: int,
        user_id: int,
        session_id: str,
        mode: str = 'auto'
    ) -> Dict[str, Any]:
        """
        执行完整工作流

        Args:
            task: 任务对象
            project_id: 项目ID
            user_id: 执行用户ID
            session_id: 会话ID
            mode: 执行模式 ('auto' 自动 或 'manual' 手动)

        Returns:
            执行结果

        Raises:
            PermissionError: 无权限执行
        """
        # 1. 权限检查
        if not self.project_manager.check_permission(project_id, user_id, 'execute_task'):
            raise PermissionError(f"用户 {user_id} 无权在项目 {project_id} 中执行任务")

        print("=" * 80)
        print(f"开始执行工作流: {task.title}")
        print(f"项目ID: {project_id} | 用户ID: {user_id} | 会话ID: {session_id}")
        print("=" * 80)

        # 工作流顺序
        workflow_sequence = [
            'Requester',
            'ProductManager',
            'Architect',
            'Developer',
            'CodeReviewer',
            'Tester',
            'DevOps'
        ]

        current_step = 0
        iteration = 0

        while current_step < len(workflow_sequence) and iteration < self.max_iterations:
            iteration += 1
            agent_name = workflow_sequence[current_step]

            print(f"\n{'='*80}")
            print(f"第{iteration}轮 - 当前Agent: {agent_name}")
            print(f"{'='*80}")

            # 获取Agent（可能是AI或人工）
            agent = self._get_agent(agent_name, task, user_id)

            # 记录开始事件
            start_time = time.time()
            self.event_logger.log_agent_start(
                task_id=task.task_id,
                agent_name=agent_name,
                agent_type=agent.agent_type if hasattr(agent, 'agent_type') else 'ai',
                user_id=user_id if isinstance(agent, HumanAgent) else None
            )

            try:
                result = agent.process(task)
                duration = time.time() - start_time

                # 处理pending状态（异步人工决策）
                if result.get('status') == 'pending':
                    print(f"\n⏸  工作流暂停：等待人工决策")
                    return {
                        'status': 'waiting_for_human',
                        'message': result.get('message'),
                        'decision_id': result.get('decision_id'),
                        'task': task.to_dict(),
                        'current_step': current_step,
                        'iteration': iteration
                    }

                # 记录完成事件
                self.event_logger.log_agent_complete(
                    task_id=task.task_id,
                    agent_name=agent_name,
                    result=result,
                    duration=duration,
                    user_id=user_id if isinstance(agent, HumanAgent) else None
                )

                if result['success']:
                    print(f"\n✓ {agent_name} 处理成功: {result['message']}")
                    current_step += 1
                else:
                    print(f"\n✗ {agent_name} 处理失败: {result['message']}")
                    # 如果失败，回退到相应的Agent
                    next_agent = result.get('next_agent')
                    if next_agent and next_agent in workflow_sequence:
                        current_step = workflow_sequence.index(next_agent)
                        print(f"  回退到: {next_agent}")

            except Exception as e:
                print(f"\n✗ {agent_name} 执行出错: {str(e)}")
                self.event_logger.log_error(
                    task_id=task.task_id,
                    agent_name=agent_name,
                    error=str(e),
                    user_id=user_id if isinstance(agent, HumanAgent) else None
                )
                break

        # 检查是否完成
        if task.status == TaskStatus.COMPLETED:
            print("\n" + "=" * 80)
            print("🎉 工作流执行成功!")
            print("=" * 80)
            self._print_summary(task)
            return {
                'status': 'completed',
                'success': True,
                'message': '工作流执行成功',
                'task': task.to_dict(),
                'session_id': session_id
            }
        else:
            print("\n" + "=" * 80)
            print("⚠️  工作流未完成")
            print("=" * 80)
            return {
                'status': 'incomplete',
                'success': False,
                'message': f'工作流在{iteration}轮后未完成',
                'task': task.to_dict(),
                'session_id': session_id
            }

    def resume_workflow(
        self,
        task: Task,
        project_id: int,
        user_id: int,
        session_id: str,
        decision_id: int
    ) -> Dict[str, Any]:
        """
        从人工决策恢复工作流

        Args:
            task: 任务对象
            project_id: 项目ID
            user_id: 用户ID
            session_id: 会话ID
            decision_id: 决策ID

        Returns:
            执行结果
        """
        print(f"\n恢复工作流: 决策 {decision_id}")

        # 获取决策
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

        # 记录决策事件
        self.event_logger.log_decision(
            task_id=task.task_id,
            decision_id=decision_id,
            user_id=user_id,
            response=decision.response
        )

        # 继续执行工作流
        return self.execute_workflow(task, project_id, user_id, session_id)

    def _get_agent(self, agent_name: str, task: Task, user_id: int) -> BaseAgent:
        """
        获取Agent（AI或人工）

        Args:
            agent_name: Agent名称
            task: 任务对象
            user_id: 用户ID

        Returns:
            Agent实例
        """
        # 检查是否配置为人工Agent
        if agent_name in self.human_agent_config:
            config = self.human_agent_config[agent_name]
            mode = config.get('mode', 'async')

            print(f"  使用人工Agent (模式: {mode})")

            return HumanAgentFactory.create_agent(
                agent_name=agent_name,
                user_id=user_id,
                decision_queue=self.decision_queue,
                mode=mode,
                config=config
            )

        # 返回AI Agent
        return self.agents[agent_name]

    def _print_summary(self, task: Task) -> None:
        """打印执行摘要"""
        print("\n执行摘要:")
        print(f"  任务ID: {task.task_id}")
        print(f"  标题: {task.title}")
        print(f"  状态: {task.status.value}")
        print(f"  创建时间: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  完成时间: {task.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n产物:")
        for artifact_type, artifact in task.artifacts.items():
            print(f"    - {artifact_type}: 由 {artifact['created_by']} 创建")
        print(f"\n反馈记录: {len(task.feedback)}条")

    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """获取指定Agent"""
        return self.agents.get(agent_name)

    def list_agents(self) -> List[str]:
        """列出所有Agent"""
        return list(self.agents.keys())

    def configure_human_agent(self, agent_name: str, mode: str = 'async', **kwargs) -> None:
        """
        配置Agent为人工模式

        Args:
            agent_name: Agent名称
            mode: 交互模式 ('sync' 或 'async')
            **kwargs: 其他配置
        """
        self.human_agent_config[agent_name] = {
            'mode': mode,
            **kwargs
        }
        print(f"✓ 已配置 {agent_name} 为人工Agent (模式: {mode})")

    def remove_human_agent(self, agent_name: str) -> None:
        """移除人工Agent配置"""
        if agent_name in self.human_agent_config:
            del self.human_agent_config[agent_name]
            print(f"✓ 已移除 {agent_name} 的人工Agent配置")
