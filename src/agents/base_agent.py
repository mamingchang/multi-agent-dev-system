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

    def __init__(self, name: str, role: str, config: Dict[str, Any] = None, llm_client=None, project_context: Dict[str, Any] = None):
        """
        初始化Agent

        Args:
            name: Agent名称（如"Requester"、"Developer"）
            role: Agent角色描述（如"需求分析师"、"开发工程师"）
            config: 配置字典（完整的Agent配置，包含tools/skills/plugins等）
            llm_client: LLM客户端（用于调用AI模型）
            project_context: 项目上下文（包含workspace_path、artifacts_path等）
        """
        self.name = name
        self.role = role
        self.config = config or {}
        self.llm_client = llm_client
        self.history: List[Dict] = []

        # 项目上下文（新增：支持项目级文件隔离）
        self.project_context = project_context or {}

        # Agent ID（全局唯一，格式：{user_id}_{agent_name}）
        # 用于记忆目录命名，确保不同用户的同名Agent记忆不冲突
        self.agent_id = name  # 默认使用name，会在加载时被覆盖

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

        # 能力加载器（新增：使用CapabilityLoader加载工具、技能、插件）
        self.capability_loader = None
        self.tools = {}  # 加载的工具字典
        self.skills = {}  # 加载的技能字典
        self.plugins = []  # 加载的插件列表
        self.mcp_servers = []  # 加载的MCP服务器配置
        self.data_paths = {}  # 数据路径
        self._init_capabilities()

        # 工具系统（保留兼容性）
        self.tool_registry = None
        self.enabled_tools = []  # 该Agent可用的工具列表
        self.current_project_id = None  # 当前操作的项目ID
        self._init_tool_system()

    def _init_memory_system(self):
        """
        初始化记忆系统（双轨：内存+文件）

        改进：记忆保存到项目目录，而不是Agent目录
        - 格式：projects/{project_name}/agent_memories/{agent_id}/
        - agent_id格式：{user_id}_{agent_name}（全局唯一）
        - 这样Agent可以跨项目迁移，不同项目的记忆互不影响
        """
        from ..memory.memory_system import get_memory_manager
        from ..memory.auto_memory import AutoMemoryManager
        from ..memory.markdown_memory import MemoryIndex
        import os

        # 轨道1：内存记忆（运行时）
        self.memory_manager = get_memory_manager()
        self.memory_store = self.memory_manager.get_store(self.name)

        # 轨道2：文件记忆（持久化）
        # 自动记忆管理器
        self.auto_memory = AutoMemoryManager(self)

        # Markdown记忆索引
        # 如果有项目上下文，记忆保存到项目目录
        # 否则保存到Agent目录（向后兼容）
        if hasattr(self, 'project_context') and self.project_context and 'workspace_path' in self.project_context:
            # 新架构：记忆在项目下
            # 格式：projects/{project_name}/agent_memories/{agent_id}/
            workspace_path = self.project_context['workspace_path']
            project_root = os.path.dirname(workspace_path)  # 回到项目根目录

            # 使用agent_id（如果还没设置，先用name）
            agent_identifier = getattr(self, 'agent_id', self.name)

            memory_dir = os.path.join(
                project_root,
                'agent_memories',
                agent_identifier
            )
        else:
            # 旧架构：记忆在Agent目录（向后兼容）
            memory_dir = os.path.join('.memory', self.name)

        self.memory_index = MemoryIndex(memory_dir)

    def _init_capabilities(self):
        """
        初始化能力系统（新增）

        使用CapabilityLoader加载Agent的工具、技能、插件、MCP服务器
        根据配置文件中的whitelist/blacklist进行过滤
        """
        from .capability_loader import CapabilityLoader

        # 如果config中包含完整的Agent配置，使用CapabilityLoader
        if self.config and ('tools' in self.config or 'skills' in self.config):
            self.capability_loader = CapabilityLoader(self.config)

            # 加载工具
            self.tools = self.capability_loader.load_tools()

            # 加载技能
            self.skills = self.capability_loader.load_skills()

            # 加载插件
            self.plugins = self.capability_loader.load_plugins()

            # 加载MCP服务器
            self.mcp_servers = self.capability_loader.load_mcp_servers()

            # 获取数据路径
            self.data_paths = self.capability_loader.get_data_paths()

            print(f"[{self.name}] 加载能力: {len(self.tools)}个工具, {len(self.skills)}个技能, {len(self.plugins)}个插件")
        else:
            # 如果没有配置，使用默认值
            print(f"[{self.name}] 未提供能力配置，使用默认工具系统")

    def _init_tool_system(self):
        """
        初始化工具系统

        所有Agent默认启用基础工具（read_file, write_file, search_files, search_code）
        子类可以在自己的__init__中添加专业工具
        """
        try:
            from ..tools.base import get_tool_registry
            self.tool_registry = get_tool_registry()

            # 默认启用基础工具（所有Agent都需要）
            self.enabled_tools = [
                'read_file',    # 读取文件
                'write_file',   # 写入文件
                'search_files', # 搜索文件
                'search_code'   # 搜索代码
            ]

        except ImportError:
            # 如果工具系统不可用，跳过
            self.tool_registry = None

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
        2. 可用Agent列表（重要！防止调用不存在的Agent）
        3. 人工最新指令（最重要！）
        4. 对话历史（了解上下文）
        5. 需求锚点（防止偏离）
        6. 前置Agent的输出（作为输入）

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

        # 2. 可用Agent列表（重要！）
        available_agents = self.get_available_agents()
        if available_agents:
            prompt_parts.append(f"\n# ⚠️ 项目可用Agent列表\n")
            prompt_parts.append(f"当前项目配置的Agent: {', '.join(available_agents)}\n")
            prompt_parts.append(f"\n**重要**: 你只能指定上述Agent作为next_agent，不能指定其他Agent！\n")
            prompt_parts.append(f"如果指定了不存在的Agent，工作流会失败。\n")

        # 3. 人工最新指令（最重要！放在最前面）
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

        # 4. 需求锚点（不可偏离）
        anchor = task.get_requirement_anchor()
        if anchor.get('title') or anchor.get('description'):
            prompt_parts.append(f"\n# 需求锚点（不可偏离）\n")
            prompt_parts.append(f"**核心需求**: {anchor.get('title', '')}\n")
            prompt_parts.append(f"**详细说明**: {anchor.get('description', '')}\n")
            prompt_parts.append(f"\n⚠️ 所有工作都必须围绕这个需求，不能擅自扩展功能。\n")

        # 5. 对话历史（如果有）
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

    # ========================================================================
    # 工具调用系统
    # ========================================================================

    def enable_tools(self, tool_names: List[str]):
        """
        启用指定的工具

        Args:
            tool_names: 工具名称列表
        """
        self.enabled_tools = tool_names

    def set_project_context(self, project_context: Dict[str, Any]):
        """
        设置项目上下文（新增：支持项目级文件隔离）

        Args:
            project_context: 项目上下文字典
                - project_name: 项目名称
                - workspace_path: 项目工作空间路径
                - artifacts_path: 项目产物路径
                - docs_path: 项目文档路径
                - sessions_path: 项目会话路径
        """
        self.project_context = project_context

        # 向后兼容：如果有project_name，设置current_project_id
        if 'project_name' in project_context:
            self.current_project_id = project_context['project_name']

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        获取可用工具列表（LLM格式）

        Returns:
            List[Dict]: 工具定义列表
        """
        if not self.tool_registry:
            return []

        all_tools = self.tool_registry.get_tools_for_llm()

        # 只返回启用的工具
        if self.enabled_tools:
            return [t for t in all_tools if t['name'] in self.enabled_tools]

        return []

    def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        调用工具（带权限检查）

        Args:
            tool_name: 工具名称
            **kwargs: 工具参数

        Returns:
            Dict: 工具执行结果
        """
        if not self.tool_registry:
            return {
                'success': False,
                'error': '工具系统未初始化'
            }

        # 检查工具是否启用
        if self.enabled_tools and tool_name not in self.enabled_tools:
            return {
                'success': False,
                'error': f'工具未启用: {tool_name}'
            }

        # 执行工具（带权限检查）
        result = self.tool_registry.execute_tool(
            tool_name,
            project_id=self.current_project_id,  # 传入项目ID进行权限检查
            **kwargs
        )

        return {
            'success': result.is_success(),
            'output': result.output,
            'error': result.error,
            'metadata': result.metadata
        }

    def _build_tools_prompt(self) -> str:
        """
        构建工具提示词

        告诉LLM有哪些工具可用以及如何使用

        Returns:
            str: 工具提示词
        """
        tools = self.get_available_tools()

        if not tools:
            return ""

        prompt_parts = ["\n# 可用工具\n"]
        prompt_parts.append("你可以使用以下工具来完成任务：\n")

        for tool in tools:
            prompt_parts.append(f"\n## {tool['name']}")
            prompt_parts.append(f"{tool['description']}\n")
            prompt_parts.append(f"参数: {tool['parameters']}\n")

        prompt_parts.append("\n## 如何使用工具\n")
        prompt_parts.append("在你的回复中，使用以下JSON格式调用工具：\n")
        prompt_parts.append("```json\n")
        prompt_parts.append("{\n")
        prompt_parts.append('  "tool": "工具名称",\n')
        prompt_parts.append('  "arguments": {\n')
        prompt_parts.append('    "参数名": "参数值"\n')
        prompt_parts.append('  }\n')
        prompt_parts.append("}\n")
        prompt_parts.append("```\n")
        prompt_parts.append("\n工具执行后，我会把结果返回给你，你可以继续使用工具或完成任务。\n")

        return "\n".join(prompt_parts)

    def _execute_with_tools(self, task, max_iterations: int = 10) -> Dict[str, Any]:
        """
        执行任务（支持工具调用循环）

        这是核心的工具调用循环：
        1. LLM生成响应
        2. 检查是否包含工具调用
        3. 如果有，执行工具
        4. 把工具结果传回LLM
        5. 重复直到任务完成

        Args:
            task: 任务对象
            max_iterations: 最大迭代次数

        Returns:
            Dict: 执行结果
        """
        if not self.llm_client:
            return {
                'success': False,
                'message': 'LLM客户端未初始化'
            }

        # 构建初始提示词
        system_prompt = self._build_system_prompt()
        if self.enabled_tools:
            system_prompt += self._build_tools_prompt()

        user_prompt = self._build_user_prompt(task)

        # 工具调用循环
        conversation_history = []
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            print(f"  [工具循环 {iteration}/{max_iterations}]")

            # 调用LLM
            try:
                response = self.llm_client.call(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    temperature=0.3
                )

                response_content = response.content

                # 检查是否包含工具调用
                tool_call = self._parse_tool_call(response_content)

                if tool_call:
                    # 执行工具
                    tool_name = tool_call['tool']
                    tool_args = tool_call['arguments']

                    print(f"  🔧 调用工具: {tool_name}")
                    print(f"     参数: {tool_args}")

                    tool_result = self.call_tool(tool_name, **tool_args)

                    print(f"  {'✅' if tool_result['success'] else '❌'} 工具结果: {tool_result.get('output', tool_result.get('error'))[:100]}...")

                    # 把工具结果传回LLM
                    conversation_history.append({
                        'role': 'assistant',
                        'content': response_content
                    })

                    conversation_history.append({
                        'role': 'user',
                        'content': f"工具执行结果:\n```\n{tool_result}\n```\n\n请继续完成任务。"
                    })

                    # 更新user_prompt
                    user_prompt = conversation_history[-1]['content']

                else:
                    # 没有工具调用，任务完成
                    print(f"  ✅ 任务完成")

                    return {
                        'success': True,
                        'output': response_content,
                        'message': '任务完成',
                        'iterations': iteration
                    }

            except Exception as e:
                return {
                    'success': False,
                    'message': f'LLM调用失败: {str(e)}',
                    'iterations': iteration
                }

        # 达到最大迭代次数
        return {
            'success': False,
            'message': f'达到最大迭代次数({max_iterations})',
            'iterations': iteration
        }

    def _parse_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """
        解析LLM响应中的工具调用

        Args:
            response: LLM响应内容

        Returns:
            Dict: 工具调用信息，如果没有返回None
        """
        import json
        import re

        # 查找JSON代码块
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, response, re.DOTALL)

        if not matches:
            # 尝试直接查找JSON对象
            json_pattern = r'\{[^{}]*"tool"[^{}]*\}'
            matches = re.findall(json_pattern, response, re.DOTALL)

        if not matches:
            return None

        # 解析第一个匹配的JSON
        try:
            tool_call = json.loads(matches[0])

            # 验证格式
            if 'tool' in tool_call and 'arguments' in tool_call:
                return tool_call

        except json.JSONDecodeError:
            pass

        return None

    # ========================================================================
    # 跨领域关注点的统一接口（基于工具系统）
    # ========================================================================

    def save_memory(self, memory_type: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        保存记忆到文件（长期记忆）

        Args:
            memory_type: 记忆类型（如"requirement", "design_decision", "implementation_detail"）
            content: 记忆内容（字典格式）

        Returns:
            Dict: 保存结果
        """
        import json
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f".memory/{self.name}/{memory_type}_{timestamp}.json"

        return self.call_tool(
            'write_file',
            file_path=path,
            content=json.dumps(content, indent=2, ensure_ascii=False)
        )

    def save_work_log(self, action: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        保存工作日志（短期记忆）

        Args:
            action: 操作类型（如"read_code", "write_code", "run_test"）
            details: 操作详情

        Returns:
            Dict: 保存结果
        """
        import json
        from datetime import datetime, date

        timestamp = datetime.now().isoformat()
        today = date.today().strftime("%Y%m%d")
        path = f".logs/{self.name}/work_{today}.jsonl"

        log_entry = {
            'timestamp': timestamp,
            'action': action,
            'details': details
        }

        # 追加模式写入
        return self.call_tool(
            'write_file',
            file_path=path,
            content=json.dumps(log_entry, ensure_ascii=False) + '\n',
            mode='append'
        )

    def save_artifact(self, artifact_type: str, content: str, format: str = 'md') -> Dict[str, Any]:
        """
        保存工作产物

        Args:
            artifact_type: 产物类型（如"requirement_doc", "architecture_design", "code"）
            content: 产物内容
            format: 文件格式（默认md）

        Returns:
            Dict: 保存结果
        """
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"artifacts/{self.name}/{artifact_type}_{timestamp}.{format}"

        return self.call_tool(
            'write_file',
            file_path=path,
            content=content
        )

    def read_memory(self, memory_type: str) -> Dict[str, Any]:
        """
        读取最新的记忆

        Args:
            memory_type: 记忆类型

        Returns:
            Dict: 记忆内容，如果不存在返回None
        """
        import json

        # 搜索记忆文件
        pattern = f"{memory_type}_*.json"
        result = self.call_tool(
            'search_files',
            pattern=pattern,
            path=f".memory/{self.name}"
        )

        if not result['success'] or not result['output']:
            return None

        # 获取最新的文件
        files = sorted(result['output'], reverse=True)
        if not files:
            return None

        # 读取文件
        read_result = self.call_tool('read_file', file_path=files[0])

        if read_result['success']:
            try:
                return json.loads(read_result['output'])
            except:
                return None

        return None

    def read_artifact(self, artifact_type: str) -> str:
        """
        读取最新的产物

        Args:
            artifact_type: 产物类型

        Returns:
            str: 产物内容，如果不存在返回None
        """
        # 搜索产物文件
        pattern = f"{artifact_type}_*.*"
        result = self.call_tool(
            'search_files',
            pattern=pattern,
            path=f"artifacts/{self.name}"
        )

        if not result['success'] or not result['output']:
            return None

        # 获取最新的文件
        files = sorted(result['output'], reverse=True)
        if not files:
            return None

        # 读取文件
        read_result = self.call_tool('read_file', file_path=files[0])

        return read_result['output'] if read_result['success'] else None

    # ========================================================================
    # 增强的记忆方法（借鉴Claude Code）
    # ========================================================================

    def process_user_message(self, user_message: str, agent_context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        处理用户消息，自动触发记忆保存

        Args:
            user_message: 用户消息
            agent_context: Agent上下文（包含之前的响应、行动等）

        Returns:
            List[Dict]: 自动保存的记忆列表
        """
        return self.auto_memory.process_user_message(user_message, agent_context)

    def save_memory_as_markdown(self, name: str, description: str, content: Any,
                                 memory_type: str = 'general', importance: str = 'medium',
                                 tags: List[str] = None) -> Dict[str, Any]:
        """
        保存记忆为Markdown格式

        Args:
            name: 记忆名称
            description: 记忆描述（一句话）
            content: 记忆内容
            memory_type: 记忆类型（user, feedback, project, reference）
            importance: 重要性（low, medium, high, critical）
            tags: 标签列表

        Returns:
            Dict: 保存结果
        """
        from datetime import datetime

        # 构建记忆数据
        memory_data = {
            'name': name,
            'description': description,
            'content': content,
            'type': memory_type,
            'importance': importance,
            'tags': tags or [],
            'created_at': datetime.now().isoformat()
        }

        # 生成文件名
        safe_name = name.replace(' ', '_').replace('/', '_')
        file_name = f"{memory_type}_{safe_name}.md"

        # 添加到索引
        self.memory_index.add_memory_to_index(memory_data, file_name)

        return {
            'success': True,
            'output': f"记忆已保存: {file_name}",
            'file_name': file_name
        }

    def forget_memory(self, file_name: str) -> Dict[str, Any]:
        """
        删除记忆

        Args:
            file_name: 记忆文件名

        Returns:
            Dict: 删除结果
        """
        self.memory_index.remove_memory_from_index(file_name)

        return {
            'success': True,
            'output': f"记忆已删除: {file_name}"
        }

    def search_markdown_memories(self, query: str = None, memory_type: str = None) -> List[Dict[str, Any]]:
        """
        搜索Markdown记忆

        Args:
            query: 搜索关键词
            memory_type: 记忆类型

        Returns:
            List[Dict]: 匹配的记忆列表
        """
        return self.memory_index.search_memories(query, memory_type)

    def get_memory_index(self) -> str:
        """
        获取记忆索引内容

        Returns:
            str: 索引内容（Markdown格式）
        """
        return self.memory_index.get_index_content()

    def update_memory_index(self):
        """更新记忆索引"""
        self.memory_index.update_index()

    def get_all_memories_summary(self) -> str:
        """
        获取所有记忆的摘要（用于添加到prompt）

        整合内存记忆和文件记忆

        Returns:
            str: 记忆摘要
        """
        summary_parts = []

        # 1. 内存记忆摘要
        memory_summary = self.get_memory_summary()
        if memory_summary:
            summary_parts.append("# 内存记忆（当前会话）")
            summary_parts.append(memory_summary)

        # 2. 文件记忆索引
        index_content = self.get_memory_index()
        if index_content:
            summary_parts.append("\n# 持久化记忆（跨会话）")
            # 只取前50行（避免太长）
            index_lines = index_content.split('\n')[:50]
            summary_parts.append('\n'.join(index_lines))
            if len(index_content.split('\n')) > 50:
                summary_parts.append("\n... (更多记忆请查看完整索引)")

        return '\n'.join(summary_parts) if summary_parts else ""

    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}', role='{self.role}')>"

    # ========================================================================
    # 项目级文件操作（新增：支持项目workspace隔离）
    # ========================================================================

    def write_file(self, relative_path: str, content: str, mode: str = 'w') -> Dict[str, Any]:
        """
        写入文件到项目workspace（带安全检查）

        Args:
            relative_path: 相对于workspace的路径（如"src/main.py"）
            content: 文件内容
            mode: 写入模式（'w'覆盖, 'a'追加）

        Returns:
            Dict: 操作结果
                - success: bool
                - output: str (成功时的消息)
                - error: str (失败时的错误信息)

        安全保证：
        - 只能访问项目workspace内的文件
        - 路径遍历攻击防护（../ 等）
        - 自动创建父目录
        """
        from pathlib import Path

        # 检查是否设置了项目上下文
        if not self.project_context or 'workspace_path' not in self.project_context:
            return {
                'success': False,
                'error': '未设置项目上下文，无法写入文件'
            }

        workspace = Path(self.project_context['workspace_path'])
        target = (workspace / relative_path).resolve()

        # 安全检查：确保目标路径在workspace内
        try:
            target.relative_to(workspace)
        except ValueError:
            return {
                'success': False,
                'error': f'安全错误：不允许访问workspace外的文件 ({relative_path})'
            }

        # 创建父目录
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return {
                'success': False,
                'error': f'创建目录失败: {str(e)}'
            }

        # 写入文件
        try:
            with open(target, mode, encoding='utf-8') as f:
                f.write(content)

            return {
                'success': True,
                'output': f'文件已写入: {relative_path} ({len(content)} 字符)'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'写入文件失败: {str(e)}'
            }

    def read_file(self, relative_path: str) -> Dict[str, Any]:
        """
        从项目workspace读取文件（带安全检查）

        Args:
            relative_path: 相对于workspace的路径

        Returns:
            Dict: 操作结果
                - success: bool
                - output: str (文件内容)
                - error: str (失败时的错误信息)
        """
        from pathlib import Path

        # 检查是否设置了项目上下文
        if not self.project_context or 'workspace_path' not in self.project_context:
            return {
                'success': False,
                'error': '未设置项目上下文，无法读取文件'
            }

        workspace = Path(self.project_context['workspace_path'])
        target = (workspace / relative_path).resolve()

        # 安全检查：确保目标路径在workspace内
        try:
            target.relative_to(workspace)
        except ValueError:
            return {
                'success': False,
                'error': f'安全错误：不允许访问workspace外的文件 ({relative_path})'
            }

        # 检查文件是否存在
        if not target.exists():
            return {
                'success': False,
                'error': f'文件不存在: {relative_path}'
            }

        # 读取文件
        try:
            with open(target, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                'success': True,
                'output': content
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'读取文件失败: {str(e)}'
            }

    def list_files(self, relative_path: str = '.', pattern: str = '*') -> Dict[str, Any]:
        """
        列出项目workspace中的文件（带安全检查）

        Args:
            relative_path: 相对于workspace的路径（默认根目录）
            pattern: 文件匹配模式（如"*.py"）

        Returns:
            Dict: 操作结果
                - success: bool
                - output: List[str] (文件路径列表)
                - error: str (失败时的错误信息)
        """
        from pathlib import Path

        # 检查是否设置了项目上下文
        if not self.project_context or 'workspace_path' not in self.project_context:
            return {
                'success': False,
                'error': '未设置项目上下文，无法列出文件'
            }

        workspace = Path(self.project_context['workspace_path'])
        target = (workspace / relative_path).resolve()

        # 安全检查：确保目标路径在workspace内
        try:
            target.relative_to(workspace)
        except ValueError:
            return {
                'success': False,
                'error': f'安全错误：不允许访问workspace外的目录 ({relative_path})'
            }

        # 检查目录是否存在
        if not target.exists():
            return {
                'success': False,
                'error': f'目录不存在: {relative_path}'
            }

        # 列出文件
        try:
            files = []
            for file_path in target.glob(pattern):
                # 计算相对于workspace的路径
                rel_path = file_path.relative_to(workspace)
                files.append(str(rel_path))

            return {
                'success': True,
                'output': sorted(files)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'列出文件失败: {str(e)}'
            }

    def delete_file(self, relative_path: str) -> Dict[str, Any]:
        """
        删除项目workspace中的文件（带安全检查）

        Args:
            relative_path: 相对于workspace的路径

        Returns:
            Dict: 操作结果
                - success: bool
                - output: str (成功消息)
                - error: str (失败时的错误信息)
        """
        from pathlib import Path

        # 检查是否设置了项目上下文
        if not self.project_context or 'workspace_path' not in self.project_context:
            return {
                'success': False,
                'error': '未设置项目上下文，无法删除文件'
            }

        workspace = Path(self.project_context['workspace_path'])
        target = (workspace / relative_path).resolve()

        # 安全检查：确保目标路径在workspace内
        try:
            target.relative_to(workspace)
        except ValueError:
            return {
                'success': False,
                'error': f'安全错误：不允许访问workspace外的文件 ({relative_path})'
            }

        # 检查文件是否存在
        if not target.exists():
            return {
                'success': False,
                'error': f'文件不存在: {relative_path}'
            }

        # 删除文件
        try:
            if target.is_file():
                target.unlink()
            elif target.is_dir():
                import shutil
                shutil.rmtree(target)

            return {
                'success': True,
                'output': f'已删除: {relative_path}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'删除失败: {str(e)}'
            }

    def get_workspace_path(self) -> str:
        """
        获取项目workspace路径

        Returns:
            str: workspace绝对路径，如果未设置返回None
        """
        if self.project_context and 'workspace_path' in self.project_context:
            return self.project_context['workspace_path']
        return None

    def get_artifacts_path(self) -> str:
        """
        获取项目artifacts路径

        Returns:
            str: artifacts绝对路径，如果未设置返回None
        """
        if self.project_context and 'artifacts_path' in self.project_context:
            return self.project_context['artifacts_path']
        return None

    # ==================== Agent感知和路由方法 ====================

    def get_available_agents(self) -> List[str]:
        """
        获取项目中可用的Agent列表

        Returns:
            List[str]: Agent名称列表
        """
        if self.project_context and 'available_agents' in self.project_context:
            return self.project_context['available_agents']
        return []

    def can_delegate_to(self, agent_name: str) -> bool:
        """
        检查是否可以委托给某个Agent

        Args:
            agent_name: Agent名称

        Returns:
            bool: 是否可以委托
        """
        return agent_name in self.get_available_agents()

    def suggest_next_agent(self, task_context: Dict[str, Any] = None) -> Optional[str]:
        """
        建议下一个处理Agent（子类可以覆盖实现智能路由）

        Args:
            task_context: 任务上下文

        Returns:
            Optional[str]: 建议的下一个Agent名称
        """
        # 默认实现：返回None，让Orchestrator自动推断
        return None

    def mark_task_completed(self) -> Dict[str, Any]:
        """
        标记任务完成

        Returns:
            Dict: 包含task_completed=True的结果
        """
        return {
            'success': True,
            'task_completed': True,
            'message': f'{self.name} 标记任务完成'
        }

    def delegate_to(self, agent_name: str, reason: str = "") -> Dict[str, Any]:
        """
        委托给另一个Agent

        Args:
            agent_name: 目标Agent名称
            reason: 委托原因

        Returns:
            Dict: 包含next_agent的结果
        """
        if not self.can_delegate_to(agent_name):
            return {
                'success': False,
                'message': f'无法委托给 {agent_name}：Agent不可用',
                'available_agents': self.get_available_agents()
            }

        return {
            'success': True,
            'next_agent': agent_name,
            'message': f'{self.name} 委托给 {agent_name}' + (f': {reason}' if reason else '')
        }

    def extract_and_validate_next_agent(self, llm_response: Dict[str, Any], default_agent: str = None) -> str:
        """
        从LLM响应中提取并验证next_agent

        Args:
            llm_response: LLM返回的字典
            default_agent: 默认Agent（如果LLM没有指定）

        Returns:
            str: 验证后的next_agent名称
        """
        # 从LLM响应中获取next_agent
        next_agent = llm_response.get('next_agent', default_agent)

        # 如果是null或None，返回None
        if next_agent is None or next_agent == 'null':
            return None

        # 验证next_agent是否在可用列表中
        available_agents = self.get_available_agents()
        if available_agents and next_agent not in available_agents:
            print(f"[{self.name}] ⚠️  LLM指定的Agent '{next_agent}' 不在可用列表中")
            if default_agent:
                print(f"[{self.name}] 使用默认值: {default_agent}")
                return default_agent
            else:
                print(f"[{self.name}] 可用Agent: {', '.join(available_agents)}")
                return None

        return next_agent



