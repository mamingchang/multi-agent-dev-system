"""
动态路由Orchestrator - Agent自主决定下一步

核心特性：
1. Agent输出中指定next_agent
2. Agent可以查询可用的Agent列表
3. Agent可以标记任务完成
4. 支持动态工作流路由
5. 防止无限循环
"""
from typing import Dict, Any, List, Optional, Callable
from .workflow.task import Task, TaskStatus
from .agents.base_agent import BaseAgent
import time


class DynamicOrchestrator:
    """
    动态路由工作流编排器

    Agent自主决定工作流路由，而不是固定顺序
    """

    def __init__(
        self,
        agents: Dict[str, BaseAgent],  # agent_name -> agent_instance
        max_total_iterations: int = 50,
        max_iterations_per_agent: int = 10,
        human_input_callback: Optional[Callable] = None
    ):
        """
        初始化动态路由Orchestrator

        Args:
            agents: Agent字典 {name: instance}
            max_total_iterations: 总迭代次数限制
            max_iterations_per_agent: 单个Agent迭代次数限制
            human_input_callback: 人工介入回调
        """
        self.agents = agents
        self.max_total_iterations = max_total_iterations
        self.max_iterations_per_agent = max_iterations_per_agent
        self.human_input_callback = human_input_callback

        # 统计信息
        self.agent_iteration_count = {name: 0 for name in agents.keys()}
        self.total_iterations = 0
        self.execution_path = []  # 记录执行路径

    def execute(self, task: Task, start_agent: str = None) -> Dict[str, Any]:
        """
        执行动态路由工作流

        Args:
            task: 任务对象
            start_agent: 起始Agent（默认为第一个）

        Returns:
            Dict: 执行结果
        """
        print("\n" + "=" * 80)
        print("🚀 动态路由工作流")
        print("=" * 80)
        print(f"任务: {task.title}")
        print(f"可用Agent: {', '.join(self.agents.keys())}")
        print("=" * 80)
        print()

        # 设置Agent上下文（让Agent知道有哪些其他Agent）
        available_agents = list(self.agents.keys())
        for agent in self.agents.values():
            if hasattr(agent, 'project_context'):
                agent.project_context['available_agents'] = available_agents

            # 设置orchestrator引用（用于sub_agent调用）
            if hasattr(agent, 'set_orchestrator'):
                agent.set_orchestrator(self)

        # 确定起始Agent
        if start_agent is None:
            current_agent_name = list(self.agents.keys())[0]
        else:
            current_agent_name = start_agent

        if current_agent_name not in self.agents:
            return {
                'success': False,
                'message': f'起始Agent不存在: {current_agent_name}',
                'execution_path': self.execution_path
            }

        # 主循环
        while self.total_iterations < self.max_total_iterations:
            self.total_iterations += 1

            # 检查Agent是否存在
            if current_agent_name not in self.agents:
                print(f"\n❌ Agent不存在: {current_agent_name}")
                return self._escalate_to_human(
                    task, current_agent_name,
                    f"Agent不存在: {current_agent_name}"
                )

            agent = self.agents[current_agent_name]

            # 检查单个Agent迭代次数
            self.agent_iteration_count[current_agent_name] += 1
            if self.agent_iteration_count[current_agent_name] > self.max_iterations_per_agent:
                print(f"\n⚠️  {current_agent_name} 迭代次数超限")
                return self._escalate_to_human(
                    task, current_agent_name,
                    f"{current_agent_name} 迭代次数超过 {self.max_iterations_per_agent} 次"
                )

            # 记录执行路径
            self.execution_path.append({
                'agent': current_agent_name,
                'iteration': self.agent_iteration_count[current_agent_name],
                'total_iteration': self.total_iterations
            })

            # 显示当前状态
            print(f"\n{'='*80}")
            print(f"🔄 轮次 {self.total_iterations}: {current_agent_name} ({agent.role})")
            print(f"   Agent迭代: {self.agent_iteration_count[current_agent_name]}/{self.max_iterations_per_agent}")
            print(f"{'='*80}\n")

            # 执行Agent
            try:
                start_time = time.time()
                result = agent.process(task)
                elapsed_time = time.time() - start_time

                print(f"\n⏱️  耗时: {elapsed_time:.2f}秒")

                if not result.get('success', False):
                    print(f"❌ {current_agent_name} 处理失败: {result.get('message', '未知错误')}")

                    # 检查是否指定了next_agent
                    next_agent = result.get('next_agent')
                    if next_agent and next_agent in self.agents:
                        print(f"   → 转交给: {next_agent}")
                        current_agent_name = next_agent
                        continue
                    else:
                        # Agent失败且没有指定有效的下一个Agent，终止工作流
                        return {
                            'success': False,
                            'message': f"{current_agent_name} 处理失败",
                            'execution_path': self.execution_path
                        }

                print(f"✅ {current_agent_name} 处理成功")

                # 显示输出摘要
                if 'output' in result and result['output']:
                    output_preview = str(result['output'])[:200]
                    print(f"📄 输出: {output_preview}...")

                # 检查任务是否完成
                if result.get('task_completed', False):
                    print(f"\n🎉 {current_agent_name} 标记任务完成")
                    task.update_status(TaskStatus.COMPLETED, current_agent_name)

                    return {
                        'success': True,
                        'message': '任务完成',
                        'completed_by': current_agent_name,
                        'execution_path': self.execution_path,
                        'total_iterations': self.total_iterations
                    }

                # 获取下一个Agent
                next_agent = result.get('next_agent')

                if not next_agent:
                    print(f"\n⚠️  {current_agent_name} 未指定下一个Agent")

                    # 尝试自动推断
                    next_agent = self._infer_next_agent(current_agent_name, task)

                    if next_agent:
                        print(f"   → 自动推断: {next_agent}")
                    else:
                        print(f"   → 无法推断，请求人工决策")
                        return self._escalate_to_human(
                            task, current_agent_name,
                            f"{current_agent_name} 未指定下一个Agent"
                        )

                # 验证next_agent是否存在
                if next_agent not in self.agents:
                    print(f"\n⚠️  指定的Agent不存在: {next_agent}")
                    print(f"   可用Agent: {', '.join(self.agents.keys())}")

                    return self._escalate_to_human(
                        task, current_agent_name,
                        f"指定的Agent不存在: {next_agent}"
                    )

                print(f"\n→ 下一个Agent: {next_agent}")
                current_agent_name = next_agent

            except Exception as e:
                print(f"\n❌ {current_agent_name} 执行异常: {str(e)}")
                import traceback
                traceback.print_exc()

                return {
                    'success': False,
                    'message': f'{current_agent_name} 执行异常: {str(e)}',
                    'execution_path': self.execution_path
                }

        # 达到总迭代次数限制
        print(f"\n⚠️  达到总迭代次数限制: {self.max_total_iterations}")
        return {
            'success': False,
            'message': f'达到总迭代次数限制: {self.max_total_iterations}',
            'execution_path': self.execution_path,
            'total_iterations': self.total_iterations
        }

    def _infer_next_agent(self, current_agent: str, task: Task) -> Optional[str]:
        """
        自动推断下一个Agent（基于标准工作流）

        Args:
            current_agent: 当前Agent名称
            task: 任务对象

        Returns:
            Optional[str]: 下一个Agent名称
        """
        # 标准工作流顺序（使用小写+下划线格式，与配置文件一致）
        standard_flow = [
            'requester',
            'product_manager',
            'architect',
            'developer',
            'code_reviewer',
            'tester',
            'devops'
        ]

        # 标准化当前Agent名称（转小写，替换空格为下划线）
        current_normalized = current_agent.lower().replace(' ', '_')

        # 查找当前Agent在标准流程中的位置
        for i, agent_name in enumerate(standard_flow):
            if agent_name == current_normalized or current_normalized in agent_name:
                # 返回下一个Agent（如果存在）
                if i + 1 < len(standard_flow):
                    next_agent_name = standard_flow[i + 1]
                    # 检查是否在可用Agent中（精确匹配）
                    if next_agent_name in self.agents:
                        return next_agent_name

        return None

    def _escalate_to_human(
        self,
        task: Task,
        agent_name: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        升级到人工介入

        Args:
            task: 任务对象
            agent_name: 当前Agent
            reason: 原因

        Returns:
            Dict: 人工决策结果
        """
        print("\n" + "🔔" * 40)
        print("⚠️  需要人工介入")
        print("🔔" * 40)
        print(f"\n当前Agent: {agent_name}")
        print(f"原因: {reason}")
        print(f"\n执行路径:")
        for step in self.execution_path[-5:]:  # 显示最后5步
            print(f"  {step['total_iteration']}. {step['agent']} (第{step['iteration']}次)")

        if self.human_input_callback:
            decision = self.human_input_callback(task, agent_name, reason)

            action = decision.get('action', 'abort')

            if action == 'continue':
                # 指定下一个Agent
                next_agent = decision.get('next_agent')
                if next_agent and next_agent in self.agents:
                    print(f"\n👤 人工决策: 继续 → {next_agent}")
                    # 重置计数器，继续执行
                    return self.execute(task, start_agent=next_agent)
                else:
                    print(f"\n👤 人工决策: 终止（未指定有效的下一个Agent）")
                    return {
                        'success': False,
                        'message': '人工终止',
                        'execution_path': self.execution_path
                    }

            elif action == 'abort':
                print(f"\n👤 人工决策: 终止")
                return {
                    'success': False,
                    'message': '人工终止',
                    'execution_path': self.execution_path
                }

        # 没有回调或默认终止
        return {
            'success': False,
            'message': f'需要人工介入: {reason}',
            'execution_path': self.execution_path
        }

    def print_execution_summary(self):
        """打印执行摘要"""
        print("\n" + "=" * 80)
        print("📊 执行摘要")
        print("=" * 80)
        print(f"总迭代次数: {self.total_iterations}")
        print(f"\nAgent迭代统计:")
        for agent_name, count in self.agent_iteration_count.items():
            if count > 0:
                print(f"  {agent_name}: {count}次")

        print(f"\n执行路径 ({len(self.execution_path)}步):")
        for i, step in enumerate(self.execution_path, 1):
            print(f"  {i}. {step['agent']}")
