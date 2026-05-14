"""
简化的Orchestrator - MVP版本

工作流编排器，负责：
1. 按顺序调度Agent执行
2. 处理Agent之间的反馈循环
3. 检查迭代次数，防止无限循环
4. 升级到人工介入

为什么需要Orchestrator：
- 统一的流程控制
- 避免Agent之间直接耦合
- 方便添加监控、日志、错误处理
"""

from typing import List, Dict, Any, Optional
from ..workflow.task import Task, TaskStatus
from ..agents.base_agent import BaseAgent
from ..conversation import MessageType


class SimpleOrchestrator:
    """
    简化的工作流编排器

    MVP版本：
    - 固定的Agent序列
    - 简单的反馈循环
    - 基本的迭代控制
    """

    def __init__(self, agents: List[BaseAgent], max_iterations: int = 5):
        """
        初始化Orchestrator

        Args:
            agents: Agent列表（按执行顺序）
            max_iterations: 每个Agent最多执行次数
        """
        self.agents = agents
        self.max_iterations = max_iterations

        # 创建Agent名称到Agent对象的映射
        self.agent_map = {agent.name: agent for agent in agents}

    def execute(self, task: Task) -> Dict[str, Any]:
        """
        执行工作流

        Args:
            task: 任务对象

        Returns:
            Dict: 执行结果
            {
                'success': bool,
                'message': str,
                'final_status': str
            }
        """
        print(f"\n{'='*60}")
        print(f"开始执行任务: {task.title}")
        print(f"{'='*60}\n")

        current_agent_index = 0

        while current_agent_index < len(self.agents):
            agent = self.agents[current_agent_index]

            print(f"\n--- {agent.name} 开始处理 ---")

            # 检查迭代次数
            iteration_count = task.get_iteration_count(agent.name)
            if iteration_count >= self.max_iterations:
                print(f"⚠️  {agent.name} 迭代次数超限({iteration_count}次)，升级到人工介入")
                return self._escalate_to_human(task, agent.name, "迭代次数超限")

            # 更新任务状态
            task.update_status(self._get_task_status(agent.name), agent.name)

            # 执行Agent
            try:
                result = agent.process(task)

                if result['success']:
                    print(f"✅ {agent.name} 处理成功")

                    # 保存产物
                    if 'output' in result and result['output']:
                        task.add_artifact(
                            artifact_type=self._get_artifact_type(agent.name),
                            content=result['output'],
                            agent=agent.name
                        )

                    # 进入下一个Agent
                    current_agent_index += 1

                else:
                    print(f"❌ {agent.name} 处理失败: {result.get('message', '未知错误')}")

                    # 检查是否需要回退
                    if 'action' in result and result['action'] == 'revise':
                        # 回退到指定Agent
                        next_agent = result.get('next_agent')
                        if next_agent and next_agent in self.agent_map:
                            current_agent_index = self.agents.index(self.agent_map[next_agent])
                            print(f"🔄 回退到 {next_agent}")
                        else:
                            # 默认回退到上一个Agent
                            if current_agent_index > 0:
                                current_agent_index -= 1
                                print(f"🔄 回退到上一个Agent")
                    else:
                        # 失败，终止流程
                        return {
                            'success': False,
                            'message': f"{agent.name} 处理失败",
                            'final_status': task.status.value
                        }

            except Exception as e:
                print(f"💥 {agent.name} 执行异常: {str(e)}")
                return {
                    'success': False,
                    'message': f"{agent.name} 执行异常: {str(e)}",
                    'final_status': task.status.value
                }

        # 所有Agent执行完成
        task.update_status(TaskStatus.COMPLETED, "Orchestrator")

        print(f"\n{'='*60}")
        print(f"✅ 任务完成: {task.title}")
        print(f"{'='*60}\n")

        return {
            'success': True,
            'message': '任务执行完成',
            'final_status': task.status.value
        }

    def _get_task_status(self, agent_name: str) -> TaskStatus:
        """
        根据Agent名称获取对应的任务状态

        Args:
            agent_name: Agent名称

        Returns:
            TaskStatus: 任务状态
        """
        status_map = {
            'Requester': TaskStatus.IN_REQUIREMENT,
            'ProductManager': TaskStatus.IN_DESIGN,
            'Architect': TaskStatus.IN_DESIGN,
            'Developer': TaskStatus.IN_DEVELOPMENT,
            'CodeReviewer': TaskStatus.IN_REVIEW,
            'Tester': TaskStatus.IN_TESTING,
            'DevOps': TaskStatus.IN_DEPLOYMENT
        }

        return status_map.get(agent_name, TaskStatus.IN_DEVELOPMENT)

    def _get_artifact_type(self, agent_name: str) -> str:
        """
        根据Agent名称获取产物类型

        Args:
            agent_name: Agent名称

        Returns:
            str: 产物类型
        """
        artifact_map = {
            'Requester': 'requirement',
            'ProductManager': 'prd',
            'Architect': 'architecture',
            'Developer': 'code',
            'CodeReviewer': 'review',
            'Tester': 'test_report',
            'DevOps': 'deployment'
        }

        return artifact_map.get(agent_name, 'output')

    def _escalate_to_human(self, task: Task, agent_name: str, reason: str) -> Dict[str, Any]:
        """
        升级到人工介入

        Args:
            task: 任务对象
            agent_name: 触发升级的Agent名称
            reason: 升级原因

        Returns:
            Dict: 执行结果
        """
        print(f"\n🚨 升级到人工介入")
        print(f"原因: {reason}")
        print(f"当前Agent: {agent_name}")

        # 发送系统消息
        if task.conversation:
            task.conversation.add_message(
                from_agent="System",
                to_agent="Human",
                content={
                    'reason': reason,
                    'agent': agent_name,
                    'task_id': task.task_id
                },
                message_type=MessageType.INFO
            )

        return {
            'success': False,
            'message': f'需要人工介入: {reason}',
            'final_status': task.status.value,
            'escalation': {
                'reason': reason,
                'agent': agent_name
            }
        }
