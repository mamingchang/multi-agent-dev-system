"""
支持WebSocket通知的工作流编排器

在SimpleOrchestrator基础上添加实时通知功能。

设计：
- 继承SimpleOrchestrator
- 在关键节点发送WebSocket通知
- 不侵入原有逻辑
- 可选启用/禁用通知

为什么这样设计：
- 保持原有编排器的简洁性
- 通知功能可以独立开关
- 便于测试（测试时可以不启用通知）
"""

from typing import List, Dict, Any, Optional
import asyncio

from .simple_orchestrator import SimpleOrchestrator
from ..workflow.task import Task, TaskStatus
from ..agents.base_agent import BaseAgent


class NotifyingOrchestrator(SimpleOrchestrator):
    """
    支持WebSocket通知的编排器

    在执行过程中发送实时通知。
    """

    def __init__(
        self,
        agents: List[BaseAgent],
        max_iterations: int = 5,
        enable_notifications: bool = True
    ):
        """
        初始化

        Args:
            agents: Agent列表
            max_iterations: 最大迭代次数
            enable_notifications: 是否启用通知
        """
        super().__init__(agents, max_iterations)
        self.enable_notifications = enable_notifications

    def execute(self, task: Task) -> Dict[str, Any]:
        """
        执行工作流（带通知）

        Args:
            task: 任务对象

        Returns:
            Dict: 执行结果
        """
        # 发送任务开始通知
        self._notify_task_started(task)

        print(f"\n{'='*60}")
        print(f"开始执行任务: {task.title}")
        print(f"{'='*60}\n")

        current_agent_index = 0

        while current_agent_index < len(self.agents):
            agent = self.agents[current_agent_index]

            print(f"\n--- {agent.name} 开始处理 ---")

            # 发送Agent开始通知
            self._notify_agent_started(task, agent)

            # 检查迭代次数
            iteration_count = task.get_iteration_count(agent.name)
            if iteration_count >= self.max_iterations:
                print(f"⚠️  {agent.name} 迭代次数超限({iteration_count}次)，升级到人工介入")

                # 发送警告通知
                self._notify_warning(
                    task,
                    f"{agent.name} 迭代次数超限",
                    agent.name
                )

                result = self._escalate_to_human(task, agent.name, "迭代次数超限")

                # 发送任务失败通知
                self._notify_task_completed(task, False, result['message'])

                return result

            # 发送迭代更新通知
            self._notify_iteration_update(task, agent.name, iteration_count + 1)

            # 更新任务状态
            task.update_status(self._get_task_status(agent.name), agent.name)

            # 执行Agent
            try:
                result = agent.process(task)

                if result['success']:
                    print(f"✅ {agent.name} 处理成功")

                    # 保存产物
                    if 'output' in result and result['output']:
                        artifact_type = self._get_artifact_type(agent.name)
                        task.add_artifact(
                            artifact_type=artifact_type,
                            content=result['output'],
                            agent=agent.name
                        )

                        # 发送产物创建通知
                        self._notify_artifact_created(
                            task,
                            artifact_type,
                            agent.name,
                            len([a for a in task.artifacts if a['agent'] == agent.name])
                        )

                    # 发送Agent完成通知
                    self._notify_agent_completed(
                        task,
                        agent.name,
                        True,
                        result.get('output')
                    )

                    # 进入下一个Agent
                    current_agent_index += 1

                else:
                    print(f"❌ {agent.name} 处理失败: {result.get('message', '未知错误')}")

                    # 发送Agent失败通知
                    self._notify_agent_completed(
                        task,
                        agent.name,
                        False,
                        result.get('message')
                    )

                    # 检查是否需要回退
                    if 'action' in result and result['action'] == 'revise':
                        # 回退到指定Agent
                        next_agent = result.get('next_agent')
                        if next_agent and next_agent in self.agent_map:
                            current_agent_index = self.agents.index(self.agent_map[next_agent])
                            print(f"🔄 回退到 {next_agent}")

                            # 发送消息通知
                            self._notify_message_sent(
                                task,
                                agent.name,
                                next_agent,
                                "revise",
                                result.get('message', '')
                            )
                        else:
                            # 默认回退到上一个Agent
                            if current_agent_index > 0:
                                current_agent_index -= 1
                                print(f"🔄 回退到上一个Agent")
                    else:
                        # 失败，终止流程
                        error_result = {
                            'success': False,
                            'message': f"{agent.name} 处理失败",
                            'final_status': task.status.value
                        }

                        # 发送任务失败通知
                        self._notify_task_completed(task, False, error_result['message'])

                        return error_result

            except Exception as e:
                print(f"💥 {agent.name} 执行异常: {str(e)}")

                # 发送错误通知
                self._notify_error(task, str(e), agent.name)

                error_result = {
                    'success': False,
                    'message': f"{agent.name} 执行异常: {str(e)}",
                    'final_status': task.status.value
                }

                # 发送任务失败通知
                self._notify_task_completed(task, False, error_result['message'])

                return error_result

        # 所有Agent执行完成
        task.update_status(TaskStatus.COMPLETED, "Orchestrator")

        print(f"\n{'='*60}")
        print(f"✅ 任务完成: {task.title}")
        print(f"{'='*60}\n")

        success_result = {
            'success': True,
            'message': '任务执行完成',
            'final_status': task.status.value
        }

        # 发送任务完成通知
        self._notify_task_completed(task, True, success_result['message'])

        return success_result

    # ==================== 通知方法 ====================

    def _notify_task_started(self, task: Task):
        """通知任务开始"""
        if not self.enable_notifications:
            return

        try:
            from ..api.websocket import notify_task_started
            asyncio.create_task(notify_task_started(task.task_id, task.title))
        except Exception as e:
            print(f"[通知失败] 任务开始: {e}")

    def _notify_task_completed(self, task: Task, success: bool, message: str):
        """通知任务完成"""
        if not self.enable_notifications:
            return

        try:
            from ..api.websocket import notify_task_completed
            asyncio.create_task(notify_task_completed(task.task_id, success, message))
        except Exception as e:
            print(f"[通知失败] 任务完成: {e}")

    def _notify_agent_started(self, task: Task, agent: BaseAgent):
        """通知Agent开始"""
        if not self.enable_notifications:
            return

        try:
            from ..api.websocket import notify_agent_started
            asyncio.create_task(
                notify_agent_started(task.task_id, agent.name, agent.role)
            )
        except Exception as e:
            print(f"[通知失败] Agent开始: {e}")

    def _notify_agent_completed(
        self,
        task: Task,
        agent_name: str,
        success: bool,
        output: Optional[str] = None
    ):
        """通知Agent完成"""
        if not self.enable_notifications:
            return

        try:
            from ..api.websocket import notify_agent_completed
            asyncio.create_task(
                notify_agent_completed(task.task_id, agent_name, success, output)
            )
        except Exception as e:
            print(f"[通知失败] Agent完成: {e}")

    def _notify_message_sent(
        self,
        task: Task,
        from_agent: str,
        to_agent: str,
        message_type: str,
        content: Any
    ):
        """通知消息发送"""
        if not self.enable_notifications:
            return

        try:
            from ..api.websocket import notify_message_sent
            asyncio.create_task(
                notify_message_sent(
                    task.task_id,
                    from_agent,
                    to_agent,
                    message_type,
                    content
                )
            )
        except Exception as e:
            print(f"[通知失败] 消息发送: {e}")

    def _notify_artifact_created(
        self,
        task: Task,
        artifact_type: str,
        agent_name: str,
        version: int
    ):
        """通知产物创建"""
        if not self.enable_notifications:
            return

        try:
            from ..api.websocket import notify_artifact_created
            asyncio.create_task(
                notify_artifact_created(
                    task.task_id,
                    artifact_type,
                    agent_name,
                    version
                )
            )
        except Exception as e:
            print(f"[通知失败] 产物创建: {e}")

    def _notify_iteration_update(
        self,
        task: Task,
        agent_name: str,
        iteration: int
    ):
        """通知迭代更新"""
        if not self.enable_notifications:
            return

        try:
            from ..api.websocket import notify_iteration_update
            asyncio.create_task(
                notify_iteration_update(
                    task.task_id,
                    agent_name,
                    iteration,
                    self.max_iterations
                )
            )
        except Exception as e:
            print(f"[通知失败] 迭代更新: {e}")

    def _notify_error(self, task: Task, error_message: str, agent_name: Optional[str] = None):
        """通知错误"""
        if not self.enable_notifications:
            return

        try:
            from ..api.websocket import notify_error
            asyncio.create_task(
                notify_error(task.task_id, error_message, agent_name)
            )
        except Exception as e:
            print(f"[通知失败] 错误: {e}")

    def _notify_warning(
        self,
        task: Task,
        warning_message: str,
        agent_name: Optional[str] = None
    ):
        """通知警告"""
        if not self.enable_notifications:
            return

        try:
            from ..api.websocket import notify_warning
            asyncio.create_task(
                notify_warning(task.task_id, warning_message, agent_name)
            )
        except Exception as e:
            print(f"[通知失败] 警告: {e}")
