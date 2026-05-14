"""
任务分解器

提供智能任务分解功能：
- LLM分析任务复杂度
- 建议子任务分解方案
- 用户确认后创建子任务
- 自动建立子任务依赖关系
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


class TaskComplexity(str, Enum):
    """任务复杂度"""
    SIMPLE = "simple"      # 简单任务，无需分解
    MEDIUM = "medium"      # 中等任务，建议分解
    COMPLEX = "complex"    # 复杂任务，强烈建议分解


@dataclass
class SubTask:
    """
    子任务

    Attributes:
        id: 子任务ID
        title: 子任务标题
        description: 子任务描述
        agent: 负责的Agent
        dependencies: 依赖的子任务ID列表
        estimated_time: 预估时间（分钟）
        priority: 优先级（1-5，5最高）
    """
    id: str
    title: str
    description: str
    agent: str
    dependencies: List[str]
    estimated_time: int
    priority: int = 3


@dataclass
class DecompositionSuggestion:
    """
    分解建议

    Attributes:
        complexity: 任务复杂度
        should_decompose: 是否建议分解
        reason: 建议原因
        subtasks: 建议的子任务列表
        total_estimated_time: 总预估时间
    """
    complexity: TaskComplexity
    should_decompose: bool
    reason: str
    subtasks: List[SubTask]
    total_estimated_time: int


class TaskDecomposer:
    """
    任务分解器

    功能：
    1. 分析任务复杂度
    2. 生成子任务分解建议
    3. 用户确认后创建子任务
    4. 自动建立依赖关系

    Why:
    - 复杂任务分解为小任务，降低失败风险
    - 并行执行子任务，提高效率
    - 清晰的任务结构，便于追踪进度

    How to apply:
    - 用户创建任务时，自动分析复杂度
    - 如果复杂，提供分解建议
    - 用户确认后，创建子任务并建立依赖

    Example:
        decomposer = TaskDecomposer(llm_client)
        suggestion = await decomposer.analyze("开发一个用户管理系统")
        if suggestion.should_decompose:
            # 展示建议给用户
            # 用户确认后创建子任务
            subtasks = await decomposer.create_subtasks(suggestion)
    """

    def __init__(self, llm_client=None):
        """
        初始化任务分解器

        Args:
            llm_client: LLM客户端（用于智能分析）

        Why: 使用LLM理解任务内容，生成合理的分解方案
        """
        self.llm_client = llm_client

    async def analyze(self, task_description: str) -> DecompositionSuggestion:
        """
        分析任务并生成分解建议

        Args:
            task_description: 任务描述

        Returns:
            分解建议

        Why: 自动评估任务复杂度，提供专业的分解建议

        Algorithm:
        1. 使用LLM分析任务描述
        2. 评估复杂度（关键词、长度、涉及模块数）
        3. 生成子任务建议
        4. 建立子任务依赖关系
        """
        # 如果没有LLM，使用规则分析
        if not self.llm_client:
            return self._rule_based_analysis(task_description)

        # 使用LLM分析
        prompt = f"""
分析以下任务，判断是否需要分解为子任务：

任务描述：
{task_description}

请按以下格式回答：

1. 复杂度：simple/medium/complex
2. 是否建议分解：是/否
3. 原因：（简要说明）
4. 如果建议分解，请列出子任务：
   - 子任务1：标题 | 描述 | 负责Agent | 依赖 | 预估时间（分钟）
   - 子任务2：...

注意：
- simple任务：单个Agent可在30分钟内完成
- medium任务：需要2-3个Agent协作，1-2小时
- complex任务：需要多个Agent协作，超过2小时
"""

        try:
            response = await self.llm_client.generate(prompt)
            return self._parse_llm_response(response)
        except Exception as e:
            print(f"LLM分析失败，使用规则分析: {e}")
            return self._rule_based_analysis(task_description)

    def _rule_based_analysis(self, task_description: str) -> DecompositionSuggestion:
        """
        基于规则的任务分析（无LLM时的后备方案）

        Args:
            task_description: 任务描述

        Returns:
            分解建议

        Why: 提供基础的分解能力，即使没有LLM也能工作

        Rules:
        - 长度>200字：complex
        - 长度>100字：medium
        - 长度<=100字：simple
        - 包含"系统"、"平台"、"完整"等关键词：complex
        """
        desc_length = len(task_description)

        # 复杂度关键词
        complex_keywords = ["系统", "平台", "完整", "全面", "端到端", "整体"]
        medium_keywords = ["功能", "模块", "组件", "接口", "集成"]

        # 判断复杂度
        if desc_length > 200 or any(kw in task_description for kw in complex_keywords):
            complexity = TaskComplexity.COMPLEX
            should_decompose = True
            reason = "任务描述较长或包含系统级关键词，建议分解为多个子任务"

            # 生成默认子任务
            subtasks = [
                SubTask(
                    id="subtask-1",
                    title="需求分析",
                    description="分析和明确需求",
                    agent="Requester",
                    dependencies=[],
                    estimated_time=30,
                    priority=5
                ),
                SubTask(
                    id="subtask-2",
                    title="架构设计",
                    description="设计系统架构",
                    agent="Architect",
                    dependencies=["subtask-1"],
                    estimated_time=60,
                    priority=4
                ),
                SubTask(
                    id="subtask-3",
                    title="核心功能开发",
                    description="开发核心功能模块",
                    agent="Developer",
                    dependencies=["subtask-2"],
                    estimated_time=120,
                    priority=5
                ),
                SubTask(
                    id="subtask-4",
                    title="测试验证",
                    description="功能测试和验证",
                    agent="Tester",
                    dependencies=["subtask-3"],
                    estimated_time=60,
                    priority=4
                ),
            ]
            total_time = 270

        elif desc_length > 100 or any(kw in task_description for kw in medium_keywords):
            complexity = TaskComplexity.MEDIUM
            should_decompose = True
            reason = "任务涉及多个模块，建议分解以提高效率"

            subtasks = [
                SubTask(
                    id="subtask-1",
                    title="需求确认",
                    description="确认具体需求",
                    agent="Requester",
                    dependencies=[],
                    estimated_time=20,
                    priority=4
                ),
                SubTask(
                    id="subtask-2",
                    title="实现开发",
                    description="实现功能",
                    agent="Developer",
                    dependencies=["subtask-1"],
                    estimated_time=60,
                    priority=5
                ),
                SubTask(
                    id="subtask-3",
                    title="测试",
                    description="测试功能",
                    agent="Tester",
                    dependencies=["subtask-2"],
                    estimated_time=30,
                    priority=4
                ),
            ]
            total_time = 110

        else:
            complexity = TaskComplexity.SIMPLE
            should_decompose = False
            reason = "任务较简单，无需分解"
            subtasks = []
            total_time = 30

        return DecompositionSuggestion(
            complexity=complexity,
            should_decompose=should_decompose,
            reason=reason,
            subtasks=subtasks,
            total_estimated_time=total_time
        )

    def _parse_llm_response(self, response: str) -> DecompositionSuggestion:
        """
        解析LLM响应

        Args:
            response: LLM响应文本

        Returns:
            分解建议

        Why: 将LLM的自然语言响应转换为结构化数据
        """
        # 简化实现：实际应该使用更robust的解析逻辑
        # 这里仅作示例
        lines = response.strip().split('\n')

        complexity = TaskComplexity.SIMPLE
        should_decompose = False
        reason = ""
        subtasks = []

        for line in lines:
            line = line.strip()
            if "复杂度" in line:
                if "complex" in line.lower():
                    complexity = TaskComplexity.COMPLEX
                elif "medium" in line.lower():
                    complexity = TaskComplexity.MEDIUM
            elif "是否建议分解" in line:
                should_decompose = "是" in line
            elif "原因" in line:
                reason = line.split("：", 1)[1] if "：" in line else line

        # 简化：返回默认子任务
        if should_decompose:
            subtasks = self._rule_based_analysis("").subtasks

        return DecompositionSuggestion(
            complexity=complexity,
            should_decompose=should_decompose,
            reason=reason,
            subtasks=subtasks,
            total_estimated_time=sum(st.estimated_time for st in subtasks)
        )

    async def create_subtasks(
        self,
        suggestion: DecompositionSuggestion,
        parent_task_id: str
    ) -> List[Dict[str, Any]]:
        """
        创建子任务

        Args:
            suggestion: 分解建议
            parent_task_id: 父任务ID

        Returns:
            创建的子任务列表

        Why: 将分解建议转换为实际的子任务记录
        """
        created_subtasks = []

        for subtask in suggestion.subtasks:
            task_data = {
                "id": f"{parent_task_id}-{subtask.id}",
                "parent_id": parent_task_id,
                "title": subtask.title,
                "description": subtask.description,
                "agent": subtask.agent,
                "dependencies": [f"{parent_task_id}-{dep}" for dep in subtask.dependencies],
                "estimated_time": subtask.estimated_time,
                "priority": subtask.priority,
                "status": "pending"
            }
            created_subtasks.append(task_data)

        return created_subtasks

    def get_execution_order(self, subtasks: List[SubTask]) -> List[List[str]]:
        """
        获取子任务执行顺序（拓扑排序）

        Args:
            subtasks: 子任务列表

        Returns:
            分层执行顺序

        Why: 确定子任务的执行顺序，识别可并行执行的子任务
        """
        from collections import deque

        # 构建依赖图
        in_degree = {st.id: len(st.dependencies) for st in subtasks}
        queue = deque([st.id for st in subtasks if len(st.dependencies) == 0])

        result = []
        while queue:
            current_layer = []
            layer_size = len(queue)

            for _ in range(layer_size):
                task_id = queue.popleft()
                current_layer.append(task_id)

                # 减少依赖此任务的其他任务的入度
                for st in subtasks:
                    if task_id in st.dependencies:
                        in_degree[st.id] -= 1
                        if in_degree[st.id] == 0:
                            queue.append(st.id)

            result.append(current_layer)

        return result
