"""
Agent注册表

管理所有可用的Agent，支持动态注册和查询。
"""

from typing import List, Dict, Any, Optional
from .capability import AgentCapability, AgentScope, BUILTIN_AGENTS


class AgentRegistry:
    """Agent注册表"""

    def __init__(self):
        """初始化注册表"""
        self.agents: Dict[str, AgentCapability] = {}

        # 注册内置Agent
        self._register_builtin_agents()

    def _register_builtin_agents(self):
        """注册内置Agent"""
        for agent in BUILTIN_AGENTS:
            self.agents[agent.name] = agent

    def register(
        self,
        capability: AgentCapability,
        override: bool = False
    ) -> bool:
        """
        注册Agent

        Args:
            capability: Agent能力声明
            override: 是否覆盖已存在的Agent

        Returns:
            bool: 是否注册成功
        """
        if capability.name in self.agents and not override:
            return False

        self.agents[capability.name] = capability
        return True

    def unregister(self, agent_name: str) -> bool:
        """
        注销Agent

        Args:
            agent_name: Agent名称

        Returns:
            bool: 是否注销成功
        """
        if agent_name not in self.agents:
            return False

        del self.agents[agent_name]
        return True

    def get(self, agent_name: str) -> Optional[AgentCapability]:
        """
        获取Agent能力声明

        Args:
            agent_name: Agent名称

        Returns:
            Optional[AgentCapability]: Agent能力声明
        """
        return self.agents.get(agent_name)

    def list_all(self) -> List[AgentCapability]:
        """
        列出所有Agent

        Returns:
            List[AgentCapability]: Agent列表
        """
        return list(self.agents.values())

    def list_by_scope(
        self,
        scope: AgentScope,
        scope_id: Optional[int] = None
    ) -> List[AgentCapability]:
        """
        按作用域列出Agent

        Args:
            scope: 作用域
            scope_id: 作用域ID

        Returns:
            List[AgentCapability]: Agent列表
        """
        agents = []

        for agent in self.agents.values():
            # 全局Agent对所有人可见
            if agent.scope == AgentScope.GLOBAL:
                agents.append(agent)
            # 匹配特定作用域
            elif agent.scope == scope and agent.scope_id == scope_id:
                agents.append(agent)

        return agents

    def search(
        self,
        task_type: Optional[str] = None,
        tech_stack: Optional[str] = None,
        domain: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[AgentCapability]:
        """
        搜索Agent

        Args:
            task_type: 任务类型
            tech_stack: 技术栈
            domain: 领域
            tags: 标签

        Returns:
            List[AgentCapability]: 匹配的Agent列表
        """
        results = []

        for agent in self.agents.values():
            # 检查任务类型
            if task_type and task_type not in agent.task_types:
                if "*" not in agent.task_types:
                    continue

            # 检查技术栈
            if tech_stack and tech_stack not in agent.tech_stacks:
                if "*" not in agent.tech_stacks:
                    continue

            # 检查领域
            if domain and domain not in agent.domains:
                continue

            # 检查标签
            if tags:
                if not any(tag in agent.tags for tag in tags):
                    continue

            results.append(agent)

        return results

    def get_workflow_candidates(
        self,
        task_description: str,
        project_tech_stack: List[str],
        available_artifacts: List[str] = None
    ) -> List[AgentCapability]:
        """
        获取工作流候选Agent

        根据任务描述、项目技术栈、已有产物等信息，
        推荐合适的Agent列表。

        Args:
            task_description: 任务描述
            project_tech_stack: 项目技术栈
            available_artifacts: 已有产物类型

        Returns:
            List[AgentCapability]: 候选Agent列表
        """
        available_artifacts = available_artifacts or []
        candidates = []

        for agent in self.agents.values():
            # 检查技术栈匹配
            if "*" not in agent.tech_stacks:
                if not any(tech in agent.tech_stacks for tech in project_tech_stack):
                    continue

            # 检查依赖是否满足
            if agent.required_inputs:
                if not all(inp in available_artifacts for inp in agent.required_inputs):
                    continue

            candidates.append(agent)

        return candidates

    def validate_workflow(self, workflow: List[str]) -> Dict[str, Any]:
        """
        验证工作流

        检查工作流中的Agent是否存在、依赖是否满足等。

        Args:
            workflow: Agent名称列表

        Returns:
            dict: 验证结果
        """
        errors = []
        warnings = []

        # 检查Agent是否存在
        for agent_name in workflow:
            if agent_name not in self.agents:
                errors.append(f"Agent不存在: {agent_name}")

        if errors:
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings
            }

        # 检查依赖关系
        available_artifacts = []

        for agent_name in workflow:
            agent = self.agents[agent_name]

            # 检查所需输入是否可用
            for required_input in agent.required_inputs:
                if required_input not in available_artifacts:
                    warnings.append(
                        f"{agent_name} 需要 {required_input}，但前面的Agent未产生"
                    )

            # 添加该Agent产生的产物
            available_artifacts.extend(agent.output_artifacts)

        return {
            "valid": True,
            "errors": errors,
            "warnings": warnings
        }

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """
        获取Agent依赖图

        Returns:
            dict: Agent名称 -> 依赖的Agent列表
        """
        graph = {}

        for agent_name, agent in self.agents.items():
            graph[agent_name] = agent.depends_on.copy()

        return graph

    def topological_sort(self, agents: List[str]) -> List[str]:
        """
        拓扑排序

        根据依赖关系对Agent进行排序。

        Args:
            agents: Agent名称列表

        Returns:
            List[str]: 排序后的Agent列表
        """
        # 构建依赖图
        graph = {}
        in_degree = {}

        for agent_name in agents:
            agent = self.agents.get(agent_name)
            if not agent:
                continue

            graph[agent_name] = []
            in_degree[agent_name] = 0

        for agent_name in agents:
            agent = self.agents.get(agent_name)
            if not agent:
                continue

            for dep in agent.depends_on:
                if dep in agents:
                    graph[dep].append(agent_name)
                    in_degree[agent_name] += 1

        # 拓扑排序
        queue = [name for name in agents if in_degree[name] == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # 检查是否有环
        if len(result) != len(agents):
            # 有环，返回原始顺序
            return agents

        return result


# 全局注册表实例
agent_registry = AgentRegistry()
