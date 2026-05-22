"""
协作式Orchestrator - 支持多轮对话和Agent协商

核心改进：
1. 多轮对话：Agent之间可以讨论、质疑、提出建议
2. 需求锚点：防止偏离原始需求
3. 角色坚持：每个Agent坚持专业立场
4. 收敛机制：3轮争议后升级人工，迭代限制
5. 人工介入：3级升级机制

为什么需要这个新的Orchestrator：
- SimpleOrchestrator是串行的，没有真正的协作
- 需要支持Agent之间的反馈循环和讨论
- 需要检测争议并升级到人工
"""

from typing import List, Dict, Any, Optional, Callable
from ..workflow.task import Task, TaskStatus
from ..agents.base_agent import BaseAgent
from ..conversation import MessageType
import time


class CollaborativeOrchestrator:
    """
    协作式工作流编排器

    支持：
    - Agent之间的多轮对话
    - 反馈循环和修改请求
    - 需求偏离检测
    - 争议检测和人工介入
    - 迭代限制和收敛控制
    """

    def __init__(
        self,
        agents: List[BaseAgent],
        max_iterations_per_agent: int = 5,
        max_dispute_rounds: int = 3,
        decision_queue = None,
        human_input_callback: Optional[Callable] = None
    ):
        """
        初始化协作式Orchestrator

        Args:
            agents: Agent列表（按执行顺序）
            max_iterations_per_agent: 每个Agent最多执行次数
            max_dispute_rounds: 最多争议轮次（超过后升级人工）
            decision_queue: 决策队列（用于人工介入）
            human_input_callback: 人工输入回调函数（用于同步获取人工输入）
        """
        self.agents = agents
        self.max_iterations_per_agent = max_iterations_per_agent
        self.max_dispute_rounds = max_dispute_rounds
        self.decision_queue = decision_queue
        self.human_input_callback = human_input_callback

        # 创建Agent名称到Agent对象的映射
        self.agent_map = {agent.name: agent for agent in agents}

        # 争议计数器
        self.dispute_count = {}

    def execute(self, task: Task) -> Dict[str, Any]:
        """
        执行协作式工作流

        流程：
        1. 按顺序执行Agent
        2. 每个Agent执行后，其他Agent可以提出反馈
        3. 如果有反馈，Agent需要修改
        4. 如果争议超过3轮，升级到人工
        5. 所有Agent通过后，进入下一个Agent

        Args:
            task: 任务对象

        Returns:
            Dict: 执行结果
        """
        print(f"\n{'='*60}")
        print(f"🚀 开始协作式工作流: {task.title}")
        print(f"{'='*60}\n")

        current_agent_index = 0

        while current_agent_index < len(self.agents):
            agent = self.agents[current_agent_index]

            print(f"\n{'='*60}")
            print(f"👤 {agent.name} ({agent.role}) 开始工作")
            print(f"{'='*60}\n")

            # 检查迭代次数
            iteration_count = task.get_iteration_count(agent.name)
            if iteration_count >= self.max_iterations_per_agent:
                print(f"⚠️  {agent.name} 迭代次数超限({iteration_count}次)")
                return self._escalate_to_human(
                    task, agent.name, "迭代次数超限", level="critical"
                )

            # 更新任务状态
            task.update_status(self._get_task_status(agent.name), agent.name)

            # 执行Agent
            try:
                result = agent.process(task)

                if not result['success']:
                    print(f"❌ {agent.name} 处理失败: {result.get('message', '未知错误')}")
                    return {
                        'success': False,
                        'message': f"{agent.name} 处理失败",
                        'final_status': task.status.value
                    }

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
                        return self._escalate_to_human(
                            task, agent.name,
                            f"需求不够明确，需要人工澄清: {clarity_check['reason']}",
                            level="critical"
                        )

                # 检查需求偏离
                if 'output' in result:
                    deviation = task.check_requirement_deviation(str(result['output']))
                    if deviation['is_deviated'] and deviation['severity'] == 'high':
                        print(f"⚠️  检测到严重偏离需求: {deviation['reason']}")
                        return self._escalate_to_human(
                            task, agent.name,
                            f"需求偏离: {deviation['reason']}",
                            level="critical"
                        )

                # 进入反馈循环：让其他Agent审查
                feedback_result = self._collect_feedback(task, agent, current_agent_index)

                if feedback_result['has_objections']:
                    print(f"\n⚠️  收到反对意见，需要修改")

                    # 检查争议轮次
                    dispute_key = f"{agent.name}_round"
                    self.dispute_count[dispute_key] = self.dispute_count.get(dispute_key, 0) + 1

                    if self.dispute_count[dispute_key] > self.max_dispute_rounds:
                        print(f"⚠️  争议轮次超限({self.dispute_count[dispute_key]}轮)")

                        # 升级到人工介入
                        escalation_result = self._escalate_to_human(
                            task, agent.name,
                            "争议无法解决，需要人工裁决",
                            level="critical"
                        )

                        # 处理人工决策
                        if escalation_result['success'] and escalation_result.get('human_decision'):
                            human_decision = escalation_result['human_decision']
                            action = human_decision.get('action', 'continue')

                            print(f"\n👤 人工决策: {action}")

                            if action == 'continue':
                                # 继续执行，进入下一个Agent
                                print(f"   继续执行，进入下一阶段")
                                current_agent_index += 1
                                self.dispute_count[dispute_key] = 0
                                continue

                            elif action == 'retry':
                                # 重试当前Agent
                                print(f"   重试当前Agent")
                                self.dispute_count[dispute_key] = 0
                                continue

                            elif action == 'skip':
                                # 跳过当前Agent
                                print(f"   跳过当前Agent")
                                current_agent_index += 1
                                self.dispute_count[dispute_key] = 0
                                continue

                            elif action == 'abort':
                                # 终止任务
                                print(f"   终止任务")
                                return {
                                    'success': False,
                                    'message': '任务被人工终止',
                                    'final_status': task.status.value
                                }

                            else:
                                # 自定义指令，传给Agent
                                print(f"   执行自定义指令: {human_decision.get('instruction', '')}")
                                # 可以把指令添加到task的context中，让Agent读取
                                continue

                        else:
                            # 人工介入失败，返回错误
                            return escalation_result

                    # 继续当前Agent（重新执行）
                    print(f"🔄 {agent.name} 将根据反馈修改")
                    continue

                # 没有反对意见，进入下一个Agent
                print(f"✅ 所有Agent批准，进入下一阶段")
                current_agent_index += 1

                # 重置争议计数
                dispute_key = f"{agent.name}_round"
                self.dispute_count[dispute_key] = 0

            except Exception as e:
                print(f"💥 {agent.name} 执行异常: {str(e)}")
                import traceback
                traceback.print_exc()
                return {
                    'success': False,
                    'message': f"{agent.name} 执行异常: {str(e)}",
                    'final_status': task.status.value
                }

        # 所有Agent执行完成
        task.update_status(TaskStatus.COMPLETED, "Orchestrator")

        print(f"\n{'='*60}")
        print(f"🎉 任务完成: {task.title}")
        print(f"{'='*60}\n")

        return {
            'success': True,
            'message': '任务执行完成',
            'final_status': task.status.value
        }

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
            {
                'has_objections': bool,  # 是否有反对意见
                'feedback_count': int,   # 反馈数量
                'objections': List       # 反对意见列表
            }
        """
        print(f"\n📋 收集其他Agent的反馈...")

        objections = []
        feedback_count = 0

        # 只让已经执行过的Agent审查（避免未来Agent提前介入）
        for i in range(current_index):
            reviewer = self.agents[i]

            print(f"   {reviewer.name} 正在审查...")

            # 简化版：使用LLM让Agent审查
            # 实际应该调用Agent的review方法
            try:
                review_result = self._agent_review(task, reviewer, current_agent)

                if review_result['has_objection']:
                    objections.append({
                        'from': reviewer.name,
                        'reason': review_result['reason'],
                        'suggestion': review_result.get('suggestion', '')
                    })

                    # 发送反对消息
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
            {
                'has_objection': bool,
                'reason': str,
                'suggestion': str
            }
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
            # 简单提取JSON（实际应该更robust）
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

    def _get_task_status(self, agent_name: str) -> TaskStatus:
        """根据Agent名称获取对应的任务状态"""
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

    def _check_requirement_clarity(self, requirement_output: str) -> Dict[str, Any]:
        """
        检查需求分析师的输出是否足够明确

        检查项：
        1. 是否包含具体的功能需求
        2. 是否有明确的验收标准
        3. 是否有可识别的用户故事或用例
        4. 是否有足够的细节供架构师设计

        Args:
            requirement_output: 需求分析师的输出内容

        Returns:
            Dict: {
                'is_clear': bool,  # 是否明确
                'reason': str      # 不明确的原因
            }
        """
        if not requirement_output or len(requirement_output.strip()) < 50:
            return {
                'is_clear': False,
                'reason': '需求描述过于简短，缺少必要细节'
            }

        # 检查关键要素
        has_functional_req = any(keyword in requirement_output for keyword in [
            '功能', '需求', '用户', '系统', '应该', '必须', '需要'
        ])

        has_acceptance = any(keyword in requirement_output for keyword in [
            '验收', '标准', '条件', '完成', '成功'
        ])

        has_details = any(keyword in requirement_output for keyword in [
            '输入', '输出', '流程', '步骤', '界面', '数据', '接口'
        ])

        # 检查是否包含疑问或不确定的表述
        has_uncertainty = any(keyword in requirement_output for keyword in [
            '不确定', '可能', '也许', '不清楚', '需要确认', '待定', '？'
        ])

        # 判断逻辑
        if has_uncertainty:
            return {
                'is_clear': False,
                'reason': '需求中包含不确定的表述，需要人工澄清'
            }

        if not has_functional_req:
            return {
                'is_clear': False,
                'reason': '缺少明确的功能需求描述'
            }

        if not has_details:
            return {
                'is_clear': False,
                'reason': '缺少具体的实现细节（输入/输出/流程等）'
            }

        # 所有检查通过
        return {
            'is_clear': True,
            'reason': ''
        }

    def _escalate_to_human(
        self,
        task: Task,
        agent_name: str,
        reason: str,
        level: str = "warning"
    ) -> Dict[str, Any]:
        """
        升级到人工介入

        3级升级机制：
        - warning: 警告，继续执行
        - critical: 关键，暂停执行，等待人工决策
        - emergency: 紧急，立即停止

        Args:
            task: 任务对象
            agent_name: 触发升级的Agent名称
            reason: 升级原因
            level: 升级级别

        Returns:
            Dict: 执行结果（包含人工决策）
        """
        level_icons = {
            'warning': '⚠️',
            'critical': '🚨',
            'emergency': '🆘'
        }

        icon = level_icons.get(level, '⚠️')

        print(f"\n{icon} 升级到人工介入 [{level.upper()}]")
        print(f"原因: {reason}")
        print(f"当前Agent: {agent_name}")

        # 发送系统消息到对话系统
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

        # 如果是warning级别，不需要等待人工，直接继续
        if level == "warning":
            return {
                'success': True,
                'message': f'警告已记录，继续执行',
                'human_decision': None
            }

        # 如果是emergency级别，立即停止
        if level == "emergency":
            return {
                'success': False,
                'message': f'紧急停止: {reason}',
                'final_status': task.status.value,
                'escalation': {
                    'level': level,
                    'reason': reason,
                    'agent': agent_name
                }
            }

        # critical级别：等待人工决策
        print(f"\n⏸️  暂停执行，等待人工决策...")

        # 方式1：使用DecisionQueue（异步，适合Web应用）
        if self.decision_queue:
            decision = self._wait_for_decision_queue(task, agent_name, reason)
            if decision:
                return {
                    'success': True,
                    'message': '人工决策已收到',
                    'human_decision': decision
                }

        # 方式2：使用回调函数（同步，适合CLI/测试）
        if self.human_input_callback:
            decision = self._wait_for_human_input(task, agent_name, reason)
            if decision:
                return {
                    'success': True,
                    'message': '人工决策已收到',
                    'human_decision': decision
                }

        # 如果没有配置人工介入机制，返回失败
        return {
            'success': False,
            'message': f'需要人工介入但未配置人工介入机制 [{level}]: {reason}',
            'final_status': task.status.value,
            'escalation': {
                'level': level,
                'reason': reason,
                'agent': agent_name
            }
        }

    def _wait_for_decision_queue(
        self,
        task: Task,
        agent_name: str,
        reason: str,
        timeout_seconds: int = 300
    ) -> Optional[Dict[str, Any]]:
        """
        等待DecisionQueue中的人工决策（异步方式）

        Args:
            task: 任务对象
            agent_name: Agent名称
            reason: 升级原因
            timeout_seconds: 超时时间（秒）

        Returns:
            Dict: 人工决策，如果超时返回None
        """
        # 创建决策到队列
        decision = self.decision_queue.create_decision(
            task_id=task.task_id,
            agent_name=agent_name,
            decision_type="dispute_resolution",
            context={
                'reason': reason,
                'conversation': task.conversation.to_dict() if task.conversation else {},
                'artifacts': task.artifacts
            }
        )

        print(f"📋 决策已创建: ID={decision.id}")
        print(f"   请在Web界面或API中处理此决策")

        # 轮询等待决策被解决
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            # 刷新决策状态
            self.decision_queue.db.refresh(decision)

            if decision.status.value == "resolved":
                print(f"✅ 收到人工决策")
                return decision.response

            if decision.status.value in ["cancelled", "timeout"]:
                print(f"❌ 决策被取消或超时")
                return None

            # 每5秒检查一次
            time.sleep(5)

        # 超时
        print(f"⏱️  等待人工决策超时 ({timeout_seconds}秒)")
        self.decision_queue.check_timeout(decision.id, timeout_minutes=timeout_seconds // 60)
        return None

    def _wait_for_human_input(
        self,
        task: Task,
        agent_name: str,
        reason: str
    ) -> Optional[Dict[str, Any]]:
        """
        等待人工输入（同步方式，通过回调函数）

        Args:
            task: 任务对象
            agent_name: Agent名称
            reason: 升级原因

        Returns:
            Dict: 人工决策
        """
        print(f"\n{'='*60}")
        print(f"🙋 需要人工决策")
        print(f"{'='*60}")
        print(f"Agent: {agent_name}")
        print(f"原因: {reason}")
        print(f"\n请提供决策:")
        print(f"  1. 'continue' - 继续执行")
        print(f"  2. 'retry' - 重试当前Agent")
        print(f"  3. 'skip' - 跳过当前Agent")
        print(f"  4. 'abort' - 终止任务")
        print(f"  5. 或输入具体指令")
        print(f"{'='*60}\n")

        # 调用回调函数获取人工输入
        human_response = self.human_input_callback(task, agent_name, reason)

        # 记录人工决策到对话系统
        if task.conversation:
            task.conversation.add_message(
                from_agent="Human",
                to_agent=agent_name,
                content=human_response,
                message_type=MessageType.CLARIFICATION
            )

        return {
            'action': human_response.get('action', 'continue'),
            'instruction': human_response.get('instruction', ''),
            'timestamp': time.time()
        }
