"""
Base Agent Class
所有角色Agent的基类，定义通用接口和行为

改进：
1. 支持多轮对话和反馈循环
2. 支持LLM调用
3. 支持需求锚点检查
4. 支持角色原则坚持
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime


class BaseAgent(ABC):
    """
    Agent基类

    所有Agent都必须继承这个类并实现process方法。

    改进点：
    - 添加LLM客户端支持
    - 添加专业原则声明
    - 添加能力声明（用于动态工作流）
    - 支持多轮对话和反馈处理
    """

    def __init__(self, name: str, role: str, config: Dict[str, Any] = None, llm_client=None):
        """
        初始化Agent

        Args:
            name: Agent名称（如"Requester"、"Developer"）
            role: Agent角色描述（如"需求分析师"、"开发工程师"）
            config: 配置字典
            llm_client: LLM客户端（用于调用AI模型）
        """
        self.name = name
        self.role = role
        self.config = config or {}
        self.llm_client = llm_client
        self.history: List[Dict] = []

        # Agent的专业原则（子类可以覆盖）
        self.principles = []

        # Agent的能力声明（用于动态工作流）
        self.capabilities = {
            'task_types': [],  # 能处理的任务类型
            'output_types': [],  # 能产生的输出类型
            'tech_stacks': [],  # 支持的技术栈
            'dependencies': []  # 依赖的前置Agent
        }

        # 记忆系统
        self._init_memory_system()

    def _init_memory_system(self):
        """初始化记忆系统"""
        from ..memory.memory_system import get_memory_manager
        self.memory_manager = get_memory_manager()
        self.memory_store = self.memory_manager.get_store(self.name)

    @abstractmethod
    def process(self, task: Any) -> Dict[str, Any]:
        """
        处理任务的核心方法，每个具体Agent必须实现

        改进：现在支持多轮迭代
        - 首次执行：正常处理任务
        - 非首次：检查反馈并修改

        Args:
            task: 任务对象

        Returns:
            处理结果字典
            {
                'success': bool,  # 是否成功
                'output': Any,    # 输出内容
                'message': str,   # 消息说明
                'next_agent': str  # 下一个Agent（可选）
            }
        """
        pass

    def _build_system_prompt(self) -> str:
        """
        构建系统提示词

        系统提示词定义了Agent的角色、职责和原则。
        这是让LLM理解自己身份的关键。

        Returns:
            str: 系统提示词
        """
        prompt = f"""你是{self.name}，一个专业的{self.role}。

你的职责：
{self._get_responsibilities()}

你必须坚持以下原则：
{self._format_principles()}

在协作中：
1. 如果其他Agent的输出违反了你的专业原则，你应该明确指出问题
2. 提出具体的修改建议，而不是模糊的批评
3. 保持专业和尊重，但不要轻易妥协专业底线
4. 如果需要澄清，主动提问

记住：你的专业判断很重要，不要因为其他Agent的意见就放弃自己的原则。
"""
        return prompt

    def _get_responsibilities(self) -> str:
        """
        获取职责描述（子类可以覆盖）

        Returns:
            str: 职责描述
        """
        return "处理分配的任务"

    def _format_principles(self) -> str:
        """
        格式化原则列表

        Returns:
            str: 格式化后的原则
        """
        if not self.principles:
            return "- 保证工作质量\n- 遵循最佳实践"

        return "\n".join([f"- {p}" for p in self.principles])

    def _build_user_prompt(self, task) -> str:
        """
        构建用户提示词

        用户提示词包含：
        1. 任务描述
        2. 人工最新指令（最重要！）
        3. 对话历史（了解上下文）
        4. 需求锚点（防止偏离）
        5. 前置Agent的输出（作为输入）

        Args:
            task: Task对象

        Returns:
            str: 用户提示词
        """
        prompt_parts = []

        # 1. 任务基本信息
        prompt_parts.append(f"# 任务信息\n")
        prompt_parts.append(f"**任务标题**: {task.title}\n")
        prompt_parts.append(f"**任务描述**: {task.description}\n")

        # 2. 人工最新指令（最重要！放在最前面）
        if task.conversation and len(task.conversation.messages) > 0:
            # 获取最近的人工消息
            human_messages = [msg for msg in task.conversation.messages
                            if msg.from_agent == "Human" and msg.to_agent == self.name]
            if human_messages:
                latest_human_msg = human_messages[-1]
                prompt_parts.append(f"\n# 🎯 人工指令（请优先关注）\n")
                prompt_parts.append(f"**来自**: Human\n")
                prompt_parts.append(f"**内容**: {latest_human_msg.content}\n")
                prompt_parts.append(f"\n⚠️ 这是人工刚刚发送的指令，请优先响应这个指令！\n")

        # 3. 需求锚点（不可偏离）
        anchor = task.get_requirement_anchor()
        if anchor.get('title') or anchor.get('description'):
            prompt_parts.append(f"\n# 需求锚点（不可偏离）\n")
            prompt_parts.append(f"**核心需求**: {anchor.get('title', '')}\n")
            prompt_parts.append(f"**详细说明**: {anchor.get('description', '')}\n")
            prompt_parts.append(f"\n⚠️ 所有工作都必须围绕这个需求，不能擅自扩展功能。\n")

        # 4. 对话历史（如果有）
        if task.conversation and len(task.conversation.messages) > 1:
            conversation_context = task.conversation.get_conversation_context(self.name)
            prompt_parts.append(f"\n# 对话历史\n")
            prompt_parts.append(conversation_context)

        # 5. 前置Agent的输出（作为输入）
        latest_artifacts = self._get_relevant_artifacts(task)
        if latest_artifacts:
            prompt_parts.append(f"\n# 前置输入\n")
            for artifact in latest_artifacts:
                prompt_parts.append(f"\n## {artifact['type']} (来自 {artifact['agent']})\n")
                prompt_parts.append(f"```\n{artifact['content']}\n```\n")

        # 6. 当前任务要求
        prompt_parts.append(f"\n# 你的任务\n")
        prompt_parts.append(self._get_task_instruction(task))

        return "\n".join(prompt_parts)

    def _get_relevant_artifacts(self, task) -> List[Dict[str, Any]]:
        """
        获取相关的前置产物

        Args:
            task: Task对象

        Returns:
            List[Dict]: 相关产物列表
        """
        # 简化版：返回所有产物
        # 未来可以根据Agent类型智能筛选
        return task.artifacts

    def _get_task_instruction(self, task) -> str:
        """
        获取任务指令（子类可以覆盖）

        Args:
            task: Task对象

        Returns:
            str: 任务指令
        """
        return "请根据以上信息完成你的工作。"

    def _check_feedback(self, task) -> Optional[List]:
        """
        检查是否有反馈需要处理

        Args:
            task: Task对象

        Returns:
            Optional[List]: 反馈消息列表，如果没有返回None
        """
        if not task.conversation:
            return None

        feedback = task.conversation.get_feedback_for(self.name)
        return feedback if feedback else None

    def _send_message(self, task, to_agent: str, content: Any, message_type):
        """
        发送消息给其他Agent

        Args:
            task: Task对象
            to_agent: 接收者Agent名称
            content: 消息内容
            message_type: 消息类型（MessageType枚举）
        """
        if task.conversation:
            task.conversation.add_message(
                from_agent=self.name,
                to_agent=to_agent,
                content=content,
                message_type=message_type
            )

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """
        调用LLM

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词

        Returns:
            str: LLM响应

        为什么单独封装：
        - 统一错误处理
        - 方便Mock测试
        - 未来可以添加重试、缓存等逻辑
        """
        if not self.llm_client:
            raise ValueError(f"{self.name} 没有配置LLM客户端")

        try:
            response = self.llm_client.chat(
                system=system_prompt,
                user=user_prompt
            )
            return response
        except Exception as e:
            raise RuntimeError(f"LLM调用失败: {str(e)}")

    def receive_message(self, message: Dict[str, Any]) -> None:
        """接收消息"""
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'received',
            'content': message
        })

    def send_message(self, to_agent: str, content: Any) -> Dict[str, Any]:
        """发送消息"""
        message = {
            'from': self.name,
            'to': to_agent,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'sent',
            'content': message
        })
        return message

    def get_history(self) -> List[Dict]:
        """获取历史记录"""
        return self.history

    # ==================== 记忆系统方法 ====================

    def remember(self, content: str, memory_type_str: str = "short_term",
                 importance: str = "medium", tags: List[str] = None,
                 metadata: Dict[str, Any] = None):
        """
        记住某个信息

        Args:
            content: 记忆内容
            memory_type_str: 记忆类型（"short_term", "long_term", "working"）
            importance: 重要性（"low", "medium", "high", "critical"）
            tags: 标签列表
            metadata: 元数据
        """
        from ..memory.memory_system import MemoryType, MemoryImportance

        # 转换类型
        memory_type_map = {
            "short_term": MemoryType.SHORT_TERM,
            "long_term": MemoryType.LONG_TERM,
            "working": MemoryType.WORKING
        }
        importance_map = {
            "low": MemoryImportance.LOW,
            "medium": MemoryImportance.MEDIUM,
            "high": MemoryImportance.HIGH,
            "critical": MemoryImportance.CRITICAL
        }

        memory_type = memory_type_map.get(memory_type_str, MemoryType.SHORT_TERM)
        importance_level = importance_map.get(importance, MemoryImportance.MEDIUM)

        return self.memory_store.add_memory(
            content=content,
            memory_type=memory_type,
            importance=importance_level,
            tags=tags,
            metadata=metadata
        )

    def recall(self, query: str = None, memory_type: str = None,
               tags: List[str] = None, limit: int = 5) -> List:
        """
        回忆相关信息

        Args:
            query: 查询关键词
            memory_type: 记忆类型过滤
            tags: 标签过滤
            limit: 返回数量

        Returns:
            List[Memory]: 匹配的记忆列表
        """
        from ..memory.memory_system import MemoryType

        memory_type_obj = None
        if memory_type:
            memory_type_map = {
                "short_term": MemoryType.SHORT_TERM,
                "long_term": MemoryType.LONG_TERM,
                "working": MemoryType.WORKING
            }
            memory_type_obj = memory_type_map.get(memory_type)

        return self.memory_store.search_memories(
            query=query,
            memory_type=memory_type_obj,
            tags=tags,
            limit=limit
        )

    def get_recent_context(self, hours: int = 24, limit: int = 10) -> List:
        """
        获取最近的上下文记忆

        Args:
            hours: 时间范围（小时）
            limit: 返回数量

        Returns:
            List[Memory]: 最近的记忆列表
        """
        from ..memory.memory_system import MemoryType

        return self.memory_store.get_recent_memories(
            memory_type=MemoryType.SHORT_TERM,
            hours=hours,
            limit=limit
        )

    def clear_working_memory(self):
        """清空工作记忆"""
        return self.memory_store.clear_working_memory()

    def get_memory_summary(self) -> str:
        """
        获取记忆摘要（用于添加到prompt）

        Returns:
            str: 记忆摘要文本
        """
        # 获取最近的短期记忆
        recent_memories = self.get_recent_context(hours=24, limit=5)

        # 获取重要的长期记忆
        from ..memory.memory_system import MemoryType, MemoryImportance
        important_memories = self.memory_store.search_memories(
            memory_type=MemoryType.LONG_TERM,
            min_importance=MemoryImportance.HIGH,
            limit=3
        )

        summary_parts = []

        if recent_memories:
            summary_parts.append("## 最近的上下文")
            for i, mem in enumerate(recent_memories, 1):
                summary_parts.append(f"{i}. {mem.content}")

        if important_memories:
            summary_parts.append("\n## 重要经验")
            for i, mem in enumerate(important_memories, 1):
                summary_parts.append(f"{i}. {mem.content}")

        return "\n".join(summary_parts) if summary_parts else ""

    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}', role='{self.role}')>"

