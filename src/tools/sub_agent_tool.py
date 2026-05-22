"""
Sub-Agent工具：允许Agent调用其他Agent作为工具

这个工具让Agent可以在处理任务时，将子任务委托给其他专业Agent处理，
然后获取结果继续自己的工作。

使用场景：
1. 数据分析师调用开发者Agent生成数据处理脚本
2. 架构师调用安全专家Agent审查架构安全性
3. 产品经理调用UI设计师Agent生成界面原型
4. 任何Agent需要其他专业能力时

示例：
    # 在Agent的system_prompt中说明可以使用sub_agent工具
    "你可以使用sub_agent工具调用其他Agent来完成子任务"

    # Agent在输出中请求调用sub_agent
    {
        "analysis": "需要生成数据处理脚本",
        "sub_agent_call": {
            "agent": "developer",
            "task": "编写Python脚本处理CSV数据",
            "context": {...}
        }
    }
"""

from typing import Dict, Any, Optional
from ..workflow.task import Task
from .base import Tool, ToolResult, ToolResultStatus


class SubAgentTool(Tool):
    """
    Sub-Agent工具

    允许Agent调用其他Agent作为工具来完成子任务。
    """

    def __init__(self, orchestrator=None):
        """
        初始化Sub-Agent工具

        Args:
            orchestrator: 工作流编排器（用于访问其他Agent）
        """
        self.orchestrator = orchestrator
        super().__init__()

    def get_name(self) -> str:
        """返回工具名称"""
        return "sub_agent"

    def get_description(self) -> str:
        """返回工具描述"""
        return "调用其他Agent作为工具来完成子任务"

    def get_parameters(self) -> Dict[str, Any]:
        """返回参数定义"""
        return {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "要调用的Agent名称"
                },
                "task_description": {
                    "type": "string",
                    "description": "子任务描述"
                },
                "context": {
                    "type": "object",
                    "description": "传递给子Agent的上下文信息"
                }
            },
            "required": ["agent_name", "task_description"]
        }

    def get_required_permission(self) -> str:
        """返回所需权限"""
        return "agent_call"

    def is_dangerous(self) -> bool:
        """是否为危险工具"""
        return False

    def execute(self, agent_name: str, task_description: str, context: Dict[str, Any] = None) -> ToolResult:
        """
        执行sub-agent调用

        Args:
            agent_name: 要调用的Agent名称
            task_description: 子任务描述
            context: 上下文信息

        Returns:
            ToolResult: 子Agent的执行结果
        """
        if not self.orchestrator:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                output=None,
                error='Sub-Agent工具未正确初始化（缺少orchestrator）'
            )

        # 检查目标Agent是否存在
        if agent_name not in self.orchestrator.agents:
            available = ', '.join(self.orchestrator.agents.keys())
            return ToolResult(
                status=ToolResultStatus.ERROR,
                output=None,
                error=f'Agent "{agent_name}" 不存在。可用Agent: {available}'
            )

        # 创建子任务
        sub_task = Task(
            task_id=f"sub_{context.get('parent_task_id', 'unknown') if context else 'unknown'}_{agent_name}",
            title=f"子任务: {task_description}",
            description=task_description
        )

        # 如果有上下文，添加到子任务
        if context:
            sub_task.context = context

        # 调用目标Agent
        target_agent = self.orchestrator.agents[agent_name]

        try:
            result = target_agent.process(sub_task)

            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                output={
                    'agent': agent_name,
                    'result': result,
                    'artifacts': sub_task.artifacts
                },
                metadata={
                    'agent': agent_name,
                    'task_id': sub_task.task_id
                }
            )

        except Exception as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                output=None,
                error=f'Sub-Agent调用失败: {str(e)}'
            )

    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具的JSON Schema（用于LLM理解如何调用）

        Returns:
            Dict: JSON Schema
        """
        return {
            "name": "sub_agent",
            "description": "调用其他Agent作为工具来完成子任务。当你需要其他专业能力时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "要调用的Agent名称（如developer、ui_designer、security_expert等）"
                    },
                    "task_description": {
                        "type": "string",
                        "description": "子任务的详细描述，要清晰具体"
                    },
                    "context": {
                        "type": "object",
                        "description": "传递给子Agent的上下文信息（可选）",
                        "properties": {
                            "parent_task_id": {"type": "string"},
                            "requirements": {"type": "object"},
                            "constraints": {"type": "array"}
                        }
                    }
                },
                "required": ["agent_name", "task_description"]
            }
        }


def register_sub_agent_tool(agent, orchestrator):
    """
    为Agent注册sub_agent工具

    Args:
        agent: 要注册工具的Agent
        orchestrator: 工作流编排器
    """
    tool = SubAgentTool(orchestrator=orchestrator)

    # 添加到Agent的工具列表
    if not hasattr(agent, 'tools'):
        agent.tools = {}

    agent.tools['sub_agent'] = tool

    # 更新Agent的system_prompt，告知可以使用sub_agent
    if hasattr(agent, '_build_system_prompt'):
        original_prompt = agent._build_system_prompt()

        # 添加sub_agent使用说明
        sub_agent_guidance = f"""

## 可用的Sub-Agent工具

你可以调用其他Agent作为工具来完成子任务。

可用的Agent：
{', '.join(orchestrator.agents.keys())}

使用方式：
在你的输出JSON中添加 "sub_agent_call" 字段：
{{
    "analysis": "你的分析",
    "sub_agent_call": {{
        "agent": "agent_name",
        "task": "子任务描述",
        "context": {{...}}
    }},
    "output": "你的输出"
}}

示例：
- 需要代码实现时，调用 "developer"
- 需要UI设计时，调用 "ui_designer"
- 需要安全审查时，调用 "security_expert"
- 需要数据分析时，调用 "data_analyst"
"""

        # 注入到system_prompt
        agent._original_system_prompt = original_prompt
        agent._system_prompt_with_sub_agent = original_prompt + sub_agent_guidance
