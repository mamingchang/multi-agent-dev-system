"""
交互式Orchestrator - 支持人工随时介入的持久化工作流

核心特性：
1. 工作流不会因为人工介入而结束
2. 进入"等待人工反馈"状态，保持WebSocket连接
3. 人工通过@Agent发送消息后，继续工作流
4. 支持随时暂停/继续
"""

from typing import List, Dict, Any, Optional
from enum import Enum
import asyncio
from ..workflow.task import Task, TaskStatus
from ..agents.base_agent import BaseAgent
from ..conversation import MessageType


class WorkflowState(Enum):
    """工作流状态"""
    IDLE = "idle"  # 空闲，等待启动
    RUNNING = "running"  # 运行中
    WAITING_HUMAN = "waiting_human"  # 等待人工反馈
    PAUSED = "paused"  # 暂停
    COMPLETED = "completed"  # 完成
    FAILED = "failed"  # 失败


class InteractiveOrchestrator:
    """
    交互式工作流编排器

    与CollaborativeOrchestrator的区别：
    - 不会因为人工介入而结束
    - 支持持久化状态
    - 支持随时唤醒和继续
    """

    def __init__(
        self,
        agents: List[BaseAgent],
        max_iterations_per_agent: int = 5,
        max_dispute_rounds: int = 3
    ):
        self.agents = agents
        self.max_iterations_per_agent = max_iterations_per_agent
        self.max_dispute_rounds = max_dispute_rounds

        # 工作流状态
        self.state = WorkflowState.IDLE
        self.current_agent_index = 0
        self.dispute_count = {}

        # 人工反馈队列
        self.human_feedback_queue = asyncio.Queue()

        # Agent映射
        self.agent_map = {agent.name: agent for agent in agents}

    async def execute(self, task: Task, websocket_callback=None) -> Dict[str, Any]:
        """
        执行交互式工作流

        Args:
            task: 任务对象
            websocket_callback: WebSocket回调函数，用于发送消息

        Returns:
            Dict: 执行结果
        """
        print(f"\n{'='*60}")
        print(f"🚀 开始交互式工作流: {task.title}")
        print(f"{'='*60}\n")

        self.state = WorkflowState.RUNNING
        self.websocket_callback = websocket_callback

        while self.current_agent_index < len(self.agents):
            agent = self.agents[self.current_agent_index]

            print(f"\n{'='*60}")
            print(f"👤 {agent.name} ({agent.role}) 开始工作")
            print(f"{'='*60}\n")

            # 检查迭代次数
            iteration_count = task.get_iteration_count(agent.name)
            if iteration_count >= self.max_iterations_per_agent:
                print(f"⚠️  {agent.name} 迭代次数超限({iteration_count}次)")
                await self._request_human_intervention(
                    task, agent.name, "迭代次数超限", level="critical"
                )
                # 等待人工反馈
                feedback = await self._wait_for_human_feedback()
                if feedback:
                    # 处理人工反馈后继续
                    continue
                else:
                    # 人工取消任务
                    return self._create_result(False, "任务被取消")

            # 更新任务状态
            task.update_status(self._get_task_status(agent.name), agent.name)

            # 执行Agent
            try:
                result = agent.process(task)

                if not result['success']:
                    print(f"❌ {agent.name} 处理失败: {result.get('message', '未知错误')}")
                    return self._create_result(False, f"{agent.name} 处理失败")

                print(f"✅ {agent.name} 完成工作")

                # 保存产物
                if 'output' in result and result['output']:
                    task.add_artifact(
                        artifact_type=self._get_artifact_type(agent.name),
                        content=result['output'],
                        agent=agent.name
                    )

                # 特殊处理：需求分析师的输出需要检查明确性
                if agent.name == 'RequirementAnalyst':
                    clarity_check = self._check_requirement_clarity(result.get('output', ''))
                    if not clarity_check['is_clear']:
                        print(f"\n⚠️  需求不够明确: {clarity_check['reason']}")
                        await self._request_human_intervention(
                            task, agent.name,
                            f"需求不够明确，需要人工澄清: {clarity_check['reason']}",
                            level="critical"
                        )
                        # 等待人工反馈
                        feedback = await self._wait_for_human_feedback()
                        if feedback:
                            # 人工提供了澄清，重新执行当前Agent
                            continue
                        else:
                            return self._create_result(False, "任务被取消")

                # 检查需求偏离
                if 'output' in result:
                    deviation = task.check_requirement_deviation(str(result['output']))
                    if deviation['is_deviated'] and deviation['severity'] == 'high':
                        print(f"⚠️  检测到严重偏离需求: {deviation['reason']}")
                        await self._request_human_intervention(
                            task, agent.name,
                            f"需求偏离: {deviation['reason']}",
                            level="critical"
                        )
                        feedback = await self._wait_for_human_feedback()
                        if feedback:
                            continue
                        else:
                            return self._create_result(False, "任务被取消")

                # 进入反馈循环：让其他Agent审查
                feedback_result = self._collect_feedback(task, agent, self.current_agent_index)

                if feedback_result['has_objections']:
                    print(f"\n⚠️  收到反对意见，需要修改")

                    # 检查争议轮次
                    dispute_key = f"{agent.name}_round"
                    self.dispute_count[dispute_key] = self.dispute_count.get(dispute_key, 0) + 1

                    if self.dispute_count[dispute_key] > self.max_dispute_rounds:
                        print(f"⚠️  争议轮次超限({self.dispute_count[dispute_key]}轮)")
                        await self._request_human_intervention(
                            task, agent.name,
                            "争议无法解决，需要人工裁决",
                            level="critical"
                        )
                        feedback = await self._wait_for_human_feedback()
                        if feedback:
                            # 重置争议计数，继续
                            self.dispute_count[dispute_key] = 0
                            continue
                        else:
                            return self._create_result(False, "任务被取消")

                    # 继续当前Agent（重新执行）
                    print(f"🔄 {agent.name} 将根据反馈修改")
                    continue

                # 没有反对意见，进入下一个Agent
                print(f"✅ 所有Agent批准，进入下一阶段")
                self.current_agent_index += 1

                # 重置争议计数
                dispute_key = f"{agent.name}_round"
                self.dispute_count[dispute_key] = 0

            except Exception as e:
                print(f"💥 {agent.name} 执行异常: {str(e)}")
                import traceback
                traceback.print_exc()
                return self._create_result(False, f"{agent.name} 执行异常: {str(e)}")

        # 所有Agent执行完成
        task.update_status(TaskStatus.COMPLETED, "Orchestrator")
        self.state = WorkflowState.COMPLETED

        print(f"\n{'='*60}")
        print(f"🎉 任务完成: {task.title}")
        print(f"{'='*60}\n")

        return self._create_result(True, "任务执行完成")

    async def _request_human_intervention(
        self,
        task: Task,
        agent_name: str,
        reason: str,
        level: str = "critical"
    ):
        """
        请求人工介入（不结束工作流）

        Args:
            task: 任务对象
            agent_name: 触发介入的Agent
            reason: 原因
            level: 级别
        """
        print(f"\n🚨 请求人工介入: {reason}")

        # 切换到等待状态
        self.state = WorkflowState.WAITING_HUMAN

        # 发送WebSocket消息
        if self.websocket_callback:
            await self.websocket_callback({
                "type": "human_intervention_required",
                "agent_name": agent_name,
                "reason": reason,
                "level": level
            })

        # 保存到对话历史
        if task.conversation:
            task.conversation.add_message(
                from_agent="System",
                to_agent="Human",
                content={
                    'level': level,
                    'reason': reason,
                    'agent': agent_name,
                    'task_id': task.task_id
                },
                message_type=MessageType.INFO
            )

    async def _wait_for_human_feedback(self) -> Optional[Dict]:
        """
        等待人工反馈

        Returns:
            Optional[Dict]: 人工反馈内容，如果取消则返回None
        """
        print("⏳ 等待人工反馈...")

        try:
            # 等待人工反馈（带超时）
            feedback = await asyncio.wait_for(
                self.human_feedback_queue.get(),
                timeout=3600  # 1小时超时
            )

            print(f"✅ 收到人工反馈: {feedback.get('action', 'unknown')}")

            # 恢复运行状态
            self.state = WorkflowState.RUNNING

            return feedback

        except asyncio.TimeoutError:
            print("⏰ 等待人工反馈超时")
            self.state = WorkflowState.FAILED
            return None

    async def handle_human_message(self, message: Dict[str, Any]):
        """
        处理人工发送的消息

        Args:
            message: 人工消息
                {
                    'content': str,  # 消息内容
                    'mentioned_agents': List[str],  # @提及的Agent
                    'action': str  # 'continue', 'cancel', 'retry'
                }
        """
        print(f"📨 收到人工消息: {message.get('content', '')[:50]}...")

        # 将消息放入队列
        await self.human_feedback_queue.put(message)

    def _collect_feedback(
        self,
        task: Task,
        current_agent: BaseAgent,
        current_index: int
    ) -> Dict[str, Any]:
        """
        收集其他Agent的反馈

        让已经执行过的Agent审查当前Agent的输出。

        Args:
            task: 任务对象
            current_agent: 当前Agent
            current_index: 当前Agent索引

        Returns:
            Dict: 反馈结果
        """
        print(f"\n📋 收集其他Agent的反馈...")

        objections = []
        feedback_count = 0

        # 只让已经执行过的Agent审查（避免未来Agent提前介入）
        for i in range(current_index):
            reviewer = self.agents[i]

            print(f"   {reviewer.name} 正在审查...")

            try:
                review_result = self._agent_review(task, reviewer, current_agent)

                if review_result['has_objection']:
                    objections.append({
                        'from': reviewer.name,
                        'reason': review_result['reason'],
                        'suggestion': review_result.get('suggestion', '')
                    })

                    # 发送反对消息
                    from ..conversation import MessageType
                    task.conversation.add_message(
                        from_agent=reviewer.name,
                        to_agent=current_agent.name,
                        content={
                            'reason': review_result['reason'],
                            'suggestion': review_result.get('suggestion', '')
                        },
                        message_type=MessageType.OBJECTION
                    )

                    print(f"   ⚠️  {reviewer.name} 提出反对")
                else:
                    # 发送批准消息
                    task.conversation.add_message(
                        from_agent=reviewer.name,
                        to_agent=current_agent.name,
                        content="批准通过",
                        message_type=MessageType.APPROVAL
                    )

                    print(f"   ✅ {reviewer.name} 批准通过")

                feedback_count += 1

            except Exception as e:
                print(f"   ⚠️  {reviewer.name} 审查失败: {str(e)}")
                # 审查失败不影响流程，继续

        return {
            'has_objections': len(objections) > 0,
            'feedback_count': feedback_count,
            'objections': objections
        }

    def _agent_review(
        self,
        task: Task,
        reviewer: BaseAgent,
        reviewed_agent: BaseAgent
    ) -> Dict[str, Any]:
        """
        让Agent审查另一个Agent的输出

        Args:
            task: 任务对象
            reviewer: 审查者Agent
            reviewed_agent: 被审查的Agent

        Returns:
            Dict: 审查结果
        """
        # 获取被审查Agent的最新产物
        artifact = task.get_latest_artifact(self._get_artifact_type(reviewed_agent.name))

        if not artifact:
            return {'has_objection': False, 'reason': '无产物可审查'}

        # 构建审查提示词
        review_prompt = f"""你是{reviewer.name}，现在需要审查{reviewed_agent.name}的工作成果。

## 需求锚点
{task.get_requirement_anchor()}

## {reviewed_agent.name}的输出
```
{artifact['content']}
```

## 你的任务
请从你的专业角度审查以上输出，判断是否存在问题。

如果存在以下情况，你应该提出反对：
1. 违反了你的专业原则
2. 偏离了需求锚点
3. 存在明显错误或风险
4. 不符合最佳实践

请以JSON格式回复：
{{
    "has_objection": true/false,
    "reason": "反对原因（如果有）",
    "suggestion": "具体建议（如果有）"
}}
"""

        try:
            response = reviewer._call_llm(
                reviewer._build_system_prompt(),
                review_prompt
            )

            # 解析JSON响应
            import json
            if '{' in response and '}' in response:
                json_start = response.index('{')
                json_end = response.rindex('}') + 1
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                return result
            else:
                # 如果没有JSON，默认批准
                return {'has_objection': False, 'reason': ''}

        except Exception as e:
            print(f"   审查解析失败: {str(e)}")
            # 失败时默认批准（避免阻塞流程）
            return {'has_objection': False, 'reason': ''}

    def _check_requirement_clarity(self, requirement_output: str) -> Dict[str, Any]:
        """检查需求明确性（从CollaborativeOrchestrator复制）"""
        if not requirement_output or len(requirement_output.strip()) < 50:
            return {'is_clear': False, 'reason': '需求描述过于简短'}
        return {'is_clear': True, 'reason': ''}

    def _get_task_status(self, agent_name: str) -> TaskStatus:
        """根据Agent名称获取任务状态"""
        status_map = {
            'RequirementAnalyst': TaskStatus.IN_REQUIREMENT,
            'ProductManager': TaskStatus.IN_DESIGN,
            'Architect': TaskStatus.IN_DESIGN,
            'Developer': TaskStatus.IN_DEVELOPMENT,
            'CodeReviewer': TaskStatus.IN_REVIEW,
            'Tester': TaskStatus.IN_TESTING,
            'DevOps': TaskStatus.IN_DEPLOYMENT
        }
        return status_map.get(agent_name, TaskStatus.IN_DEVELOPMENT)

    def _get_artifact_type(self, agent_name: str) -> str:
        """根据Agent名称获取产物类型"""
        artifact_map = {
            'RequirementAnalyst': 'requirement',
            'ProductManager': 'prd',
            'Architect': 'architecture',
            'Developer': 'code',
            'CodeReviewer': 'review',
            'Tester': 'test_report',
            'DevOps': 'deployment'
        }
        return artifact_map.get(agent_name, 'output')

    def _create_result(self, success: bool, message: str) -> Dict[str, Any]:
        """创建执行结果"""
        return {
            'success': success,
            'message': message,
            'state': self.state.value
        }
