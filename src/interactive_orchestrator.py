"""
交互式Orchestrator
支持实时查看Agent工作过程并允许用户介入

特性：
1. 实时显示Agent思考和工作过程
2. 每个Agent完成后暂停，等待用户确认
3. 用户可以提供反馈或修改方向
4. 用户可以跳过某些Agent
5. 用户可以随时终止工作流
"""
from typing import Dict, Any, List, Optional, Callable
from .orchestrator import Orchestrator
from .workflow.task import Task, TaskStatus
from .session_manager import Session
import time


class InteractiveOrchestrator(Orchestrator):
    """交互式协调器"""

    def __init__(self, config: Dict[str, Any] = None, session_manager=None, use_registration: bool = True):
        super().__init__(config, session_manager, use_registration)
        self.pause_after_each_agent = True
        self.show_thinking_process = True
        self.user_feedback_callback: Optional[Callable] = None

    def execute_workflow_interactive(
        self,
        task: Task,
        session: Session = None,
        auto_save: bool = True,
        feedback_callback: Callable = None
    ) -> Dict[str, Any]:
        """
        执行交互式工作流

        Args:
            task: 任务对象
            session: 会话对象
            auto_save: 是否自动保存
            feedback_callback: 用户反馈回调函数，签名为 (agent_name, result) -> Dict
                返回: {'action': 'continue'|'skip'|'retry'|'stop', 'feedback': str}

        Returns:
            执行结果
        """
        self.user_feedback_callback = feedback_callback

        if session:
            self.current_session = session
            session.add_task(task)

        print("\n" + "=" * 80)
        print(f"🚀 开始交互式工作流: {task.title}")
        if session:
            print(f"📋 会话ID: {session.session_id}")
        print("=" * 80)
        print("\n💡 提示: 每个Agent完成后会暂停，等待你的确认")
        print("   你可以: [c]继续 / [s]跳过 / [r]重试 / [f]反馈 / [q]退出\n")

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
        skipped_agents = []

        while current_step < len(workflow_sequence) and iteration < self.max_iterations:
            iteration += 1
            agent_name = workflow_sequence[current_step]
            agent = self.agents[agent_name]

            print(f"\n{'='*80}")
            print(f"🔄 第{iteration}轮 - 当前Agent: {agent_name} ({agent.role})")
            print(f"{'='*80}")

            # 显示Agent即将执行的任务
            print(f"\n📝 {agent_name} 将要:")
            print(f"   {self._get_agent_description(agent_name)}")
            print()

            try:
                # 实时显示Agent工作过程
                print(f"⏳ {agent_name} 正在工作...")
                start_time = time.time()

                # 执行Agent任务
                result = agent.process(task)

                elapsed_time = time.time() - start_time

                # 显示执行结果
                print(f"\n⏱️  耗时: {elapsed_time:.2f}秒")

                if result['success']:
                    print(f"✅ {agent_name} 处理成功")
                    print(f"📄 消息: {result['message']}")

                    # 显示产物
                    if 'artifacts' in result and result['artifacts']:
                        print(f"\n📦 产物:")
                        for artifact_key, artifact_value in result['artifacts'].items():
                            if isinstance(artifact_value, dict):
                                print(f"   - {artifact_key}: {artifact_value.get('description', 'N/A')}")
                            else:
                                print(f"   - {artifact_key}")
                else:
                    print(f"❌ {agent_name} 处理失败")
                    print(f"📄 消息: {result['message']}")

                # 自动保存会话
                if auto_save and session and self.session_manager:
                    self.session_manager.save_session(session)

                # 暂停并等待用户反馈
                if self.pause_after_each_agent:
                    user_action = self._wait_for_user_feedback(agent_name, result)

                    if user_action['action'] == 'stop':
                        print("\n🛑 用户终止工作流")
                        break
                    elif user_action['action'] == 'skip':
                        print(f"\n⏭️  跳过后续步骤，继续下一个Agent")
                        skipped_agents.append(agent_name)
                        current_step += 1
                    elif user_action['action'] == 'retry':
                        print(f"\n🔄 重试 {agent_name}")
                        # 不增加current_step，重新执行当前Agent
                    elif user_action['action'] == 'continue':
                        if result['success']:
                            current_step += 1
                        else:
                            # 处理失败，可能需要回退
                            next_agent = result.get('next_agent')
                            if next_agent and next_agent in workflow_sequence:
                                current_step = workflow_sequence.index(next_agent)
                                print(f"  ↩️  回退到: {next_agent}")
                            else:
                                # 如果没有指定回退，询问用户
                                print("\n⚠️  Agent处理失败，是否继续？")
                                continue_anyway = input("继续下一个Agent? [y/N]: ").strip().lower()
                                if continue_anyway == 'y':
                                    current_step += 1
                                else:
                                    break

                    # 如果用户提供了反馈，添加到任务中
                    if user_action.get('feedback'):
                        task.add_feedback(
                            agent_name=agent_name,
                            feedback=user_action['feedback'],
                            feedback_type='user_intervention'
                        )
                else:
                    # 不暂停，自动继续
                    if result['success']:
                        current_step += 1

            except KeyboardInterrupt:
                print("\n\n⚠️  检测到 Ctrl+C，暂停工作流")
                print("是否要终止工作流？")
                terminate = input("[y]终止 / [n]继续: ").strip().lower()
                if terminate == 'y':
                    break
                else:
                    continue

            except Exception as e:
                print(f"\n❌ {agent_name} 执行出错: {str(e)}")
                print("\n是否继续执行下一个Agent？")
                continue_on_error = input("[y]继续 / [n]终止: ").strip().lower()
                if continue_on_error != 'y':
                    break
                current_step += 1

        # 工作流完成总结
        print("\n" + "=" * 80)
        if task.status == TaskStatus.COMPLETED:
            print("🎉 工作流执行成功!")
        else:
            print("⚠️  工作流未完全完成")
        print("=" * 80)

        self._print_interactive_summary(task, skipped_agents, iteration)

        if session:
            session.status = "completed" if task.status == TaskStatus.COMPLETED else "partial"
            if self.session_manager:
                self.session_manager.save_session(session)

        return {
            'success': task.status == TaskStatus.COMPLETED,
            'message': '工作流执行完成' if task.status == TaskStatus.COMPLETED else '工作流部分完成',
            'task': task.to_dict(),
            'session_id': session.session_id if session else None,
            'skipped_agents': skipped_agents,
            'iterations': iteration
        }

    def _wait_for_user_feedback(self, agent_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        等待用户反馈

        Returns:
            {'action': 'continue'|'skip'|'retry'|'stop', 'feedback': str}
        """
        # 如果提供了回调函数，使用回调
        if self.user_feedback_callback:
            return self.user_feedback_callback(agent_name, result)

        # 否则使用命令行交互
        print("\n" + "-" * 80)
        print("⏸️  工作流已暂停，等待你的指令...")
        print("-" * 80)

        while True:
            user_input = input("\n👉 [c]继续 / [s]跳过 / [r]重试 / [f]反馈 / [q]退出: ").strip().lower()

            if user_input == 'c' or user_input == '':
                return {'action': 'continue', 'feedback': None}
            elif user_input == 's':
                return {'action': 'skip', 'feedback': None}
            elif user_input == 'r':
                return {'action': 'retry', 'feedback': None}
            elif user_input == 'q':
                return {'action': 'stop', 'feedback': None}
            elif user_input == 'f':
                feedback = input("📝 请输入你的反馈: ").strip()
                action = input("反馈后的操作 [c]继续 / [r]重试: ").strip().lower()
                return {
                    'action': 'continue' if action == 'c' else 'retry',
                    'feedback': feedback
                }
            else:
                print("❌ 无效的输入，请重新选择")

    def _get_agent_description(self, agent_name: str) -> str:
        """获取Agent的工作描述"""
        descriptions = {
            'Requester': '收集和分析需求，明确项目目标',
            'ProductManager': '制定产品规划，定义功能和优先级',
            'Architect': '设计系统架构，制定技术方案',
            'Developer': '编写代码，实现功能',
            'CodeReviewer': '审查代码质量，提出改进建议',
            'Tester': '编写和执行测试，确保质量',
            'DevOps': '配置部署环境，发布应用'
        }
        return descriptions.get(agent_name, '执行任务')

    def _print_interactive_summary(self, task: Task, skipped_agents: List[str], iterations: int) -> None:
        """打印交互式工作流摘要"""
        print("\n📊 执行摘要:")
        print(f"  任务ID: {task.task_id}")
        print(f"  标题: {task.title}")
        print(f"  状态: {task.status.value}")
        print(f"  总轮次: {iterations}")

        if skipped_agents:
            print(f"\n⏭️  跳过的Agent: {', '.join(skipped_agents)}")

        print(f"\n📦 产物:")
        if isinstance(task.artifacts, dict):
            for artifact_type, artifact in task.artifacts.items():
                print(f"    - {artifact_type}: 由 {artifact.get('created_by', 'unknown')} 创建")
        elif isinstance(task.artifacts, list):
            for artifact in task.artifacts:
                print(f"    - {artifact.get('type', 'unknown')}: 由 {artifact.get('created_by', 'unknown')} 创建")

        print(f"\n💬 反馈记录: {len(task.feedback)}条")
        if task.feedback:
            for i, feedback in enumerate(task.feedback[-3:], 1):  # 显示最后3条
                print(f"    {i}. [{feedback.get('agent_name', 'unknown')}] {feedback.get('feedback', '')[:50]}...")

    def set_pause_mode(self, enabled: bool):
        """设置是否在每个Agent后暂停"""
        self.pause_after_each_agent = enabled

    def set_thinking_display(self, enabled: bool):
        """设置是否显示思考过程"""
        self.show_thinking_process = enabled
