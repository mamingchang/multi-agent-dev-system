"""
GenericAgent - 通用Agent类
支持完全自定义的Agent角色，不局限于预定义类型

用户可以通过配置文件定义任意角色的Agent：
- 数据分析师 (DataAnalyst)
- UI设计师 (UIDesigner)
- 安全专家 (SecurityExpert)
- 数据库管理员 (DatabaseAdmin)
- ...任何角色

核心特性：
1. 基于配置的行为定义（system_prompt、角色描述）
2. 动态工具/技能/插件加载
3. 智能next_agent决策
4. 完全可配置的工作流程
"""

from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from ..workflow.task import Task, TaskStatus
from ..llm import LLMFactory, LLMClient, LLMError
import json


class GenericAgent(BaseAgent):
    """
    通用Agent类

    这个类可以根据配置文件动态创建任意角色的Agent。
    不需要为每个角色写单独的Python类。

    配置示例：
    ```yaml
    name: data_analyst
    role: 数据分析师
    description: 专注于数据分析和可视化的Agent

    system_prompt: |
      你是一个专业的数据分析师...

    capabilities:
      - 数据清洗
      - 统计分析
      - 数据可视化

    tools:
      whitelist:
        - read_file
        - write_file
        - execute_python
        - plot_chart

    default_next_agent: developer
    ```
    """

    def __init__(self, name: str, config: Dict[str, Any] = None, llm_client: LLMClient = None, project_context: Dict[str, Any] = None):
        """
        初始化通用Agent

        Args:
            name: Agent名称
            config: Agent配置（包含role、description、system_prompt等）
            llm_client: LLM客户端
            project_context: 项目上下文
        """
        # 从配置中获取角色描述
        role = config.get('role', 'Generic Agent') if config else 'Generic Agent'

        super().__init__(name, role, config, llm_client, project_context)

        # 从配置中提取关键信息
        self.description = config.get('description', '') if config else ''
        self.capabilities = config.get('capabilities', []) if config else []
        self.custom_system_prompt = config.get('system_prompt', '') if config else ''
        self.default_next_agent = config.get('default_next_agent', None) if config else None

        # 初始化LLM客户端（如果没有提供）
        if not self.llm_client:
            self._initialize_llm()

        # 加载工具
        self.tool_registry = self._load_tools()

        print(f"[{self.name}] ✓ 通用Agent初始化成功")
        print(f"  角色: {self.role}")
        print(f"  描述: {self.description[:50]}..." if len(self.description) > 50 else f"  描述: {self.description}")
        if self.capabilities:
            print(f"  能力: {', '.join(self.capabilities[:3])}" + ("..." if len(self.capabilities) > 3 else ""))
        if self.tool_registry:
            tool_count = len(self.tool_registry.list_tools())
            print(f"  工具: {tool_count}个可用")

    def _initialize_llm(self):
        """
        初始化LLM客户端

        优先使用Agent配置中的LLM设置
        """
        try:
            if self.config and 'llm' in self.config:
                llm_config_dict = self.config['llm']

                from ..llm.llm_client import ClaudeLLMAdapter
                self.llm_client = ClaudeLLMAdapter(
                    model=llm_config_dict.get('model', 'claude-sonnet-4-5')
                )

                print(f"[{self.name}] ✓ LLM客户端初始化成功: {llm_config_dict.get('provider', 'claude')}/{llm_config_dict.get('model', 'claude-sonnet-4-5')}")
            else:
                print(f"[{self.name}] ⚠️  未配置LLM，将使用简单模式")
                self.llm_client = None

        except Exception as e:
            print(f"[{self.name}] ⚠️  LLM客户端初始化失败: {str(e)}")
            self.llm_client = None

    def _load_tools(self):
        """
        加载工具

        根据Agent配置加载可用工具

        Returns:
            AgentToolRegistry: Agent工具注册表
        """
        try:
            from ..tools.tool_loader import ToolLoader

            loader = ToolLoader()
            tool_registry = loader.load_tools_for_agent(self.config or {})

            return tool_registry

        except Exception as e:
            print(f"[{self.name}] ⚠️  工具加载失败: {str(e)}")
            return None

    def _build_system_prompt(self) -> str:
        """
        构建系统提示词

        如果配置中提供了custom_system_prompt，使用它；
        否则使用默认模板。

        Returns:
            str: 系统提示词
        """
        # 如果有自定义system_prompt，使用它
        if self.custom_system_prompt:
            base_prompt = self.custom_system_prompt
        else:
            # 使用默认模板
            base_prompt = f"""你是一个{self.role}（{self.name}）。

角色描述：
{self.description}

你的能力：
{chr(10).join(f'- {cap}' for cap in self.capabilities) if self.capabilities else '（未指定具体能力）'}

你的职责：
1. 理解任务需求
2. 运用你的专业能力处理任务
3. 产生高质量的输出
4. 决定下一个处理该任务的Agent
"""

        # 添加工具说明
        tools_section = self._build_tools_section()

        # 添加next_agent说明
        available_agents = self.get_available_agents() if hasattr(self, 'get_available_agents') else []
        agents_list = ', '.join(available_agents) if available_agents else '（未指定可用Agent）'

        next_agent_guidance = f"""

输出格式（JSON）：
{{
    "analysis": "你对任务的分析",
    "output": "你的工作成果（可以是文本、代码、设计等）",
    "recommendations": ["建议1", "建议2"],
    "sub_agent_call": {{
        "agent": "agent_name",
        "task": "子任务描述",
        "context": {{...}}
    }},
    "next_agent": "下一个Agent的名称"
}}

可用的Agent列表：
{agents_list}

**重要：next_agent字段说明**
- 根据任务的当前状态和下一步需求，智能选择合适的Agent
- 如果任务已完成，设置为 null
- **必须使用小写+下划线格式**（如 product_manager，不是 ProductManager）
- **只能选择上述可用Agent列表中的Agent**

**Sub-Agent工具使用说明**
你可以在处理任务时调用其他Agent作为工具来完成子任务。

使用场景：
- 需要其他专业能力时（如需要代码实现、UI设计、安全审查等）
- 子任务可以独立完成，不影响主流程
- 需要专业Agent的输出作为你工作的一部分

使用方式：
在输出JSON中添加 "sub_agent_call" 字段：
{{
    "analysis": "我需要调用开发者生成代码",
    "sub_agent_call": {{
        "agent": "developer",
        "task": "编写Python脚本处理CSV数据",
        "context": {{
            "requirements": "读取CSV，计算统计值，输出JSON",
            "constraints": ["使用pandas库", "处理缺失值"]
        }}
    }},
    "output": "等待子Agent完成后继续..."
}}

子Agent完成后，结果会自动添加到你的输出中的 "sub_agent_result" 字段。

注意：
- sub_agent_call是可选的，只在需要时使用
- 可以在一次处理中调用一个子Agent
- 子Agent的结果会合并到你的输出中
- 你仍然需要指定next_agent来继续工作流
"""

        return base_prompt + tools_section + next_agent_guidance

    def _build_tools_section(self) -> str:
        """
        构建工具说明部分

        Returns:
            str: 工具说明
        """
        if not self.tool_registry:
            return ""

        try:
            from ..tools.tool_formatter import ToolFormatter

            formatter = ToolFormatter()
            return formatter.format_tools_for_llm(self.tool_registry)

        except Exception as e:
            print(f"[{self.name}] ⚠️  工具格式化失败: {str(e)}")
            return ""

    def _build_user_prompt(self, task: Task) -> str:
        """
        构建用户提示词

        Args:
            task: 任务对象

        Returns:
            str: 用户提示词
        """
        # 获取之前Agent的产物
        previous_artifacts = []
        for artifact in task.artifacts:
            previous_artifacts.append(f"- {artifact['type']} (来自 {artifact['agent']})")

        artifacts_summary = "\n".join(previous_artifacts) if previous_artifacts else "（暂无）"

        return f"""请处理以下任务：

任务标题：{task.title}

任务描述：
{task.description}

之前的产物：
{artifacts_summary}

请根据你的角色和能力，完成你负责的部分，并按照指定的JSON格式输出结果。"""

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析LLM的响应（增强容错版本）

        Args:
            response_text: LLM返回的文本

        Returns:
            Dict: 解析后的JSON对象
        """
        import re

        # 策略1: 尝试直接解析
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # 策略2: 提取```json代码块
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 策略3: 提取普通代码块
        code_match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
        if code_match:
            try:
                return json.loads(code_match.group(1))
            except json.JSONDecodeError:
                pass

        # 策略4: 查找{...}内容
        brace_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if brace_match:
            try:
                json_str = brace_match.group(0)
                # 移除尾部逗号
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # 所有策略失败，返回基本结构
        raise ValueError(f"无法从响应中提取有效的JSON。响应前200字符: {response_text[:200]}...")

    def process(self, task: Task) -> Dict[str, Any]:
        """
        处理任务（主入口）

        这是Agent的核心方法，被Orchestrator调用。

        Args:
            task: 任务对象

        Returns:
            Dict: 处理结果
        """
        print(f"\n{'='*80}")
        print(f"[{self.name}] 开始处理任务")
        print(f"{'='*80}")
        print(f"角色: {self.role}")
        print(f"任务: {task.title}")

        # 更新任务状态
        task.update_status(TaskStatus.IN_REQUIREMENT, self.name)

        try:
            # 如果有LLM客户端，使用智能模式
            if self.llm_client:
                result = self._process_with_llm(task)
            else:
                result = self._process_simple(task)

            # 检查是否有tool_calls调用请求
            if 'tool_calls' in result:
                result = self._handle_tool_calls(task, result)

            # 检查是否有sub_agent调用请求
            if 'sub_agent_call' in result:
                result = self._handle_sub_agent_call(task, result)

            # 保存产物
            task.add_artifact(
                artifact_type=f"{self.name}_output",
                content=result,
                agent=self.name
            )

            # 提取next_agent
            next_agent = self.extract_and_validate_next_agent(
                result,
                default_agent=self.default_next_agent
            )

            if next_agent:
                print(f"[{self.name}] → 下一个Agent: {next_agent}")
            else:
                print(f"[{self.name}] ✓ 任务处理完成，无需转交")

            return {
                'success': True,
                'message': f'{self.role}处理完成',
                'next_agent': next_agent,
                'output': result
            }

        except LLMError as e:
            print(f"\n[{self.name}] ✗ LLM调用失败: {str(e)}")
            return {
                'success': False,
                'message': f'LLM调用失败: {str(e)}',
                'next_agent': None
            }

        except Exception as e:
            print(f"\n[{self.name}] ✗ 处理失败: {str(e)}")
            return {
                'success': False,
                'message': f'处理失败: {str(e)}',
                'next_agent': None
            }

    def _handle_tool_calls(self, task: Task, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理工具调用请求

        当Agent的输出中包含tool_calls字段时，
        解析并执行工具调用，将结果合并回来。

        Args:
            task: 当前任务
            result: Agent的输出结果（包含tool_calls）

        Returns:
            Dict: 合并了工具结果的输出
        """
        if not self.tool_registry:
            print(f"[{self.name}] ⚠️  工具注册表未初始化，跳过工具调用")
            return result

        try:
            from ..llm.tool_call_parser import ToolCallParser

            parser = ToolCallParser()
            parse_result = parser.parse_tool_calls(result)

            if not parse_result.success:
                # 解析失败
                print(f"[{self.name}] ✗ 工具调用解析失败:")
                for error in parse_result.errors:
                    print(f"  - {error}")

                result['tool_errors'] = parse_result.errors
                return result

            if not parse_result.tool_calls:
                # 没有工具调用
                return result

            print(f"\n[{self.name}] 🔧 执行 {len(parse_result.tool_calls)} 个工具调用")

            tool_results = []
            for i, tool_call in enumerate(parse_result.tool_calls, 1):
                print(f"  {i}. {tool_call.tool_name}")

                try:
                    # 执行工具
                    tool_result = self.tool_registry.execute_tool(
                        tool_call.tool_name,
                        **tool_call.parameters
                    )

                    tool_results.append({
                        'tool': tool_call.tool_name,
                        'success': tool_result.success,
                        'output': tool_result.output,
                        'error': tool_result.error
                    })

                    if tool_result.success:
                        print(f"     ✓ 成功")
                    else:
                        print(f"     ✗ 失败: {tool_result.error}")

                except Exception as e:
                    print(f"     ✗ 异常: {str(e)}")
                    tool_results.append({
                        'tool': tool_call.tool_name,
                        'success': False,
                        'error': str(e)
                    })

            # 将工具结果合并到输出
            result['tool_results'] = tool_results

            return result

        except Exception as e:
            print(f"[{self.name}] ✗ 工具调用处理异常: {str(e)}")
            result['tool_errors'] = [str(e)]
            return result

    def _handle_sub_agent_call(self, task: Task, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理sub_agent调用请求

        当Agent的输出中包含sub_agent_call字段时，
        调用指定的子Agent处理子任务，并将结果合并回来。

        Args:
            task: 当前任务
            result: Agent的输出结果（包含sub_agent_call）

        Returns:
            Dict: 合并了子Agent结果的输出
        """
        sub_agent_call = result.get('sub_agent_call', {})
        agent_name = sub_agent_call.get('agent')
        sub_task_desc = sub_agent_call.get('task')
        context = sub_agent_call.get('context', {})

        if not agent_name or not sub_task_desc:
            print(f"[{self.name}] ⚠️  sub_agent_call格式不正确，忽略")
            return result

        print(f"\n[{self.name}] 🔄 调用子Agent: {agent_name}")
        print(f"  子任务: {sub_task_desc}")

        # 检查是否有orchestrator（需要访问其他Agent）
        if not hasattr(self, 'orchestrator') or not self.orchestrator:
            print(f"[{self.name}] ⚠️  无法调用子Agent：未设置orchestrator")
            result['sub_agent_result'] = {
                'success': False,
                'error': '未设置orchestrator，无法调用子Agent'
            }
            return result

        # 检查目标Agent是否存在
        if agent_name not in self.orchestrator.agents:
            available = ', '.join(self.orchestrator.agents.keys())
            print(f"[{self.name}] ⚠️  子Agent不存在: {agent_name}")
            print(f"  可用Agent: {available}")
            result['sub_agent_result'] = {
                'success': False,
                'error': f'Agent "{agent_name}" 不存在',
                'available_agents': available
            }
            return result

        # 创建子任务
        sub_task = Task(
            task_id=f"sub_{task.task_id}_{agent_name}",
            title=f"子任务: {sub_task_desc}",
            description=sub_task_desc
        )

        # 传递上下文
        sub_task.context = {
            'parent_task_id': task.task_id,
            'parent_agent': self.name,
            **context
        }

        # 调用子Agent
        target_agent = self.orchestrator.agents[agent_name]

        try:
            sub_result = target_agent.process(sub_task)

            print(f"[{self.name}] ✓ 子Agent完成: {agent_name}")

            # 将子Agent的结果合并到当前结果
            result['sub_agent_result'] = {
                'success': True,
                'agent': agent_name,
                'result': sub_result,
                'artifacts': sub_task.artifacts
            }

        except Exception as e:
            print(f"[{self.name}] ✗ 子Agent失败: {str(e)}")
            result['sub_agent_result'] = {
                'success': False,
                'agent': agent_name,
                'error': str(e)
            }

        return result

    def set_orchestrator(self, orchestrator):
        """
        设置orchestrator引用（用于sub_agent调用）

        Args:
            orchestrator: 工作流编排器
        """
        self.orchestrator = orchestrator

    def _process_with_llm(self, task: Task) -> Dict[str, Any]:
        """
        使用LLM处理任务（智能模式）

        Args:
            task: 任务对象

        Returns:
            Dict: 处理结果
        """
        print(f"\n[{self.name}] 正在使用LLM处理任务...")

        # 构建提示词
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(task)

        # 调用LLM
        response = self.llm_client.call(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=4096
        )

        print(f"[{self.name}] ✓ LLM响应成功 (使用了 {response.usage['total_tokens']} tokens)")

        # 解析响应
        try:
            result = self._parse_llm_response(response.content)

            print(f"\n[{self.name}] 处理结果:")
            if 'analysis' in result:
                print(f"  分析: {result['analysis'][:100]}..." if len(result.get('analysis', '')) > 100 else f"  分析: {result.get('analysis', '')}")
            if 'output' in result:
                output_preview = str(result['output'])[:100]
                print(f"  输出: {output_preview}..." if len(str(result.get('output', ''))) > 100 else f"  输出: {result.get('output', '')}")

            return result

        except Exception as e:
            print(f"[{self.name}] ⚠️  解析LLM响应失败: {str(e)}")
            # 返回基本结构
            return {
                "analysis": "解析失败，使用原始响应",
                "output": response.content[:500],
                "recommendations": [],
                "next_agent": self.default_next_agent
            }

    def _process_simple(self, task: Task) -> Dict[str, Any]:
        """
        简单模式处理（不使用LLM）

        Args:
            task: 任务对象

        Returns:
            Dict: 基本的处理结果
        """
        print(f"\n[{self.name}] 使用简单模式处理（未使用LLM）")

        return {
            "analysis": f"{self.role}已查看任务",
            "output": f"任务 '{task.title}' 已由 {self.role} 处理（简单模式）",
            "recommendations": ["建议启用LLM以获得更好的处理结果"],
            "next_agent": self.default_next_agent
        }
