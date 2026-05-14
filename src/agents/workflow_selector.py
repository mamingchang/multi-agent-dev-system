"""
动态工作流选择器

使用LLM根据任务描述和可用Agent自动选择工作流。
"""

from typing import List, Dict, Any, Optional
from .registry import agent_registry
from .capability import AgentCapability


class WorkflowSelector:
    """工作流选择器"""

    def __init__(self, llm_client=None):
        """
        初始化选择器

        Args:
            llm_client: LLM客户端（用于智能选择）
        """
        self.llm_client = llm_client

    def select_workflow(
        self,
        task_description: str,
        task_type: str,
        project_tech_stack: List[str],
        organization_id: int,
        project_id: Optional[int] = None,
        user_preference: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        选择工作流

        Args:
            task_description: 任务描述
            task_type: 任务类型
            project_tech_stack: 项目技术栈
            organization_id: 组织ID
            project_id: 项目ID
            user_preference: 用户偏好的Agent列表

        Returns:
            dict: 工作流选择结果
        """
        # 如果用户指定了工作流，直接使用
        if user_preference:
            validation = agent_registry.validate_workflow(user_preference)
            if validation["valid"]:
                return {
                    "workflow": user_preference,
                    "reason": "用户指定",
                    "confidence": 1.0,
                    "warnings": validation["warnings"]
                }

        # 获取可用的Agent
        available_agents = self._get_available_agents(
            organization_id,
            project_id,
            task_type,
            project_tech_stack
        )

        if not available_agents:
            return {
                "workflow": [],
                "reason": "没有可用的Agent",
                "confidence": 0.0,
                "warnings": ["没有找到匹配的Agent"]
            }

        # 使用LLM智能选择
        if self.llm_client:
            return self._select_with_llm(
                task_description,
                task_type,
                project_tech_stack,
                available_agents
            )

        # 降级到规则选择
        return self._select_with_rules(
            task_type,
            project_tech_stack,
            available_agents
        )

    def _get_available_agents(
        self,
        organization_id: int,
        project_id: Optional[int],
        task_type: str,
        tech_stack: List[str]
    ) -> List[AgentCapability]:
        """
        获取可用的Agent

        Args:
            organization_id: 组织ID
            project_id: 项目ID
            task_type: 任务类型
            tech_stack: 技术栈

        Returns:
            List[AgentCapability]: 可用Agent列表
        """
        # 搜索匹配的Agent
        agents = agent_registry.search(task_type=task_type)

        # 过滤技术栈
        filtered = []
        for agent in agents:
            if "*" in agent.tech_stacks:
                filtered.append(agent)
            elif any(tech in agent.tech_stacks for tech in tech_stack):
                filtered.append(agent)

        return filtered

    def _select_with_llm(
        self,
        task_description: str,
        task_type: str,
        tech_stack: List[str],
        available_agents: List[AgentCapability]
    ) -> Dict[str, Any]:
        """
        使用LLM选择工作流

        Args:
            task_description: 任务描述
            task_type: 任务类型
            tech_stack: 技术栈
            available_agents: 可用Agent列表

        Returns:
            dict: 选择结果
        """
        # 构建提示词
        agent_descriptions = []
        for agent in available_agents:
            agent_descriptions.append(
                f"- {agent.name}: {agent.description}\n"
                f"  能力: {', '.join(agent.domains)}\n"
                f"  产出: {', '.join(agent.output_artifacts)}"
            )

        prompt = f"""请根据以下信息选择合适的Agent工作流：

任务描述: {task_description}
任务类型: {task_type}
技术栈: {', '.join(tech_stack)}

可用的Agent:
{chr(10).join(agent_descriptions)}

请选择合适的Agent序列，并说明理由。
输出格式：
工作流: [Agent1, Agent2, Agent3, ...]
理由: ...
"""

        try:
            # 调用LLM
            response = self.llm_client.generate(prompt)

            # 解析响应
            workflow, reason = self._parse_llm_response(response.content)

            # 验证工作流
            validation = agent_registry.validate_workflow(workflow)

            return {
                "workflow": workflow,
                "reason": reason,
                "confidence": 0.8,
                "warnings": validation["warnings"]
            }

        except Exception as e:
            print(f"LLM选择失败: {e}")
            # 降级到规则选择
            return self._select_with_rules(
                task_type,
                tech_stack,
                available_agents
            )

    def _parse_llm_response(self, response: str) -> tuple:
        """
        解析LLM响应

        Args:
            response: LLM响应

        Returns:
            tuple: (workflow, reason)
        """
        workflow = []
        reason = ""

        lines = response.split("\n")
        for line in lines:
            if line.startswith("工作流:"):
                # 提取Agent列表
                workflow_str = line.split(":", 1)[1].strip()
                workflow_str = workflow_str.strip("[]")
                workflow = [name.strip() for name in workflow_str.split(",")]
            elif line.startswith("理由:"):
                reason = line.split(":", 1)[1].strip()

        return workflow, reason

    def _select_with_rules(
        self,
        task_type: str,
        tech_stack: List[str],
        available_agents: List[AgentCapability]
    ) -> Dict[str, Any]:
        """
        使用规则选择工作流

        Args:
            task_type: 任务类型
            tech_stack: 技术栈
            available_agents: 可用Agent列表

        Returns:
            dict: 选择结果
        """
        # 预定义的工作流模板
        templates = {
            "feature": ["ProductManager", "Architect", "Developer", "CodeReviewer", "Tester"],
            "enhancement": ["ProductManager", "Developer", "CodeReviewer", "Tester"],
            "bugfix": ["Developer", "CodeReviewer", "Tester"],
            "refactor": ["Architect", "Developer", "CodeReviewer", "Tester"],
            "deployment": ["Deployer"],
            "documentation": ["DocumentWriter"]
        }

        # 获取模板
        template = templates.get(task_type, ["ProductManager", "Developer", "Tester"])

        # 过滤可用的Agent
        available_names = {agent.name for agent in available_agents}
        workflow = [name for name in template if name in available_names]

        # 拓扑排序
        workflow = agent_registry.topological_sort(workflow)

        return {
            "workflow": workflow,
            "reason": f"基于{task_type}类型的标准工作流模板",
            "confidence": 0.6,
            "warnings": []
        }

    def adjust_workflow(
        self,
        current_workflow: List[str],
        current_step: int,
        adjustment_type: str,
        agent_name: Optional[str] = None,
        reason: str = ""
    ) -> Dict[str, Any]:
        """
        调整工作流

        Args:
            current_workflow: 当前工作流
            current_step: 当前步骤
            adjustment_type: 调整类型（add/skip/replace）
            agent_name: Agent名称
            reason: 调整原因

        Returns:
            dict: 调整结果
        """
        new_workflow = current_workflow.copy()

        if adjustment_type == "add" and agent_name:
            # 在当前步骤后添加Agent
            new_workflow.insert(current_step + 1, agent_name)

        elif adjustment_type == "skip":
            # 跳过当前Agent
            if current_step < len(new_workflow):
                new_workflow.pop(current_step)

        elif adjustment_type == "replace" and agent_name:
            # 替换当前Agent
            if current_step < len(new_workflow):
                new_workflow[current_step] = agent_name

        # 验证新工作流
        validation = agent_registry.validate_workflow(new_workflow)

        return {
            "new_workflow": new_workflow,
            "valid": validation["valid"],
            "reason": reason,
            "warnings": validation["warnings"]
        }


# 全局选择器实例
workflow_selector = WorkflowSelector()
