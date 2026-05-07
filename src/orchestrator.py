"""
Orchestrator
协调器：管理整个工作流，协调各个Agent
"""
from typing import Dict, Any, List, Optional
from .agents.base_agent import BaseAgent
from .agents.requester import RequesterAgent
from .agents.product_manager import ProductManagerAgent
from .agents.architect import ArchitectAgent
from .agents.developer import DeveloperAgent
from .agents.code_reviewer import CodeReviewerAgent
from .agents.tester import TesterAgent
from .agents.devops import DevOpsAgent
from .workflow.task import Task, TaskStatus
from .session_manager import SessionManager, Session


class Orchestrator:
    """协调器"""

    def __init__(self, config: Dict[str, Any] = None, session_manager: SessionManager = None):
        self.config = config or {}
        self.agents: Dict[str, BaseAgent] = {}
        self.max_iterations = self.config.get('max_iterations', 10)
        self.session_manager = session_manager
        self.current_session: Optional[Session] = None
        self._initialize_agents()

    def _initialize_agents(self) -> None:
        """初始化所有Agent"""
        self.agents = {
            'Requester': RequesterAgent(),
            'ProductManager': ProductManagerAgent(),
            'Architect': ArchitectAgent(),
            'Developer': DeveloperAgent(),
            'CodeReviewer': CodeReviewerAgent(),
            'Tester': TesterAgent(),
            'DevOps': DevOpsAgent(config={'environment': 'production'})
        }

    def execute_workflow(self, task: Task, session: Session = None, auto_save: bool = True) -> Dict[str, Any]:
        """
        执行完整工作流

        Args:
            task: 任务对象
            session: 会话对象（可选）
            auto_save: 是否自动保存会话

        Returns:
            执行结果
        """
        # 如果提供了session，将任务添加到session
        if session:
            self.current_session = session
            session.add_task(task)

        print("=" * 80)
        print(f"开始执行工作流: {task.title}")
        if session:
            print(f"会话ID: {session.session_id}")
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
            agent = self.agents[agent_name]

            print(f"\n{'='*80}")
            print(f"第{iteration}轮 - 当前Agent: {agent_name} ({agent.role})")
            print(f"{'='*80}")

            try:
                result = agent.process(task)

                # 自动保存会话
                if auto_save and session and self.session_manager:
                    self.session_manager.save_session(session)

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
                break

        # 检查是否完成
        if task.status == TaskStatus.COMPLETED:
            if session:
                session.status = "completed"
                if self.session_manager:
                    self.session_manager.save_session(session)

            print("\n" + "=" * 80)
            print("🎉 工作流执行成功!")
            print("=" * 80)
            self._print_summary(task)
            return {
                'success': True,
                'message': '工作流执行成功',
                'task': task.to_dict(),
                'session_id': session.session_id if session else None
            }
        else:
            if session:
                session.status = "failed"
                if self.session_manager:
                    self.session_manager.save_session(session)

            print("\n" + "=" * 80)
            print("⚠️  工作流未完成")
            print("=" * 80)
            return {
                'success': False,
                'message': f'工作流在{iteration}轮后未完成',
                'task': task.to_dict(),
                'session_id': session.session_id if session else None
            }

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
