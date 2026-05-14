"""
DAG工作流执行器

提供基于有向无环图(DAG)的并行工作流执行功能：
- Agent任务依赖管理
- 并行执行无依赖的Agent
- 拓扑排序确定执行顺序
- 动态依赖调整
"""

from typing import Dict, List, Set, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import deque


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"      # 等待执行
    READY = "ready"          # 准备就绪（依赖已满足）
    RUNNING = "running"      # 正在执行
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    SKIPPED = "skipped"      # 跳过


@dataclass
class DAGNode:
    """
    DAG节点（代表一个Agent任务）

    Attributes:
        id: 节点ID（Agent名称）
        dependencies: 依赖的节点ID列表（必须先完成的Agent）
        status: 当前状态
        result: 执行结果
        error: 错误信息（如果失败）
        executor: 执行函数（async callable）

    Why: 封装Agent任务的元数据和执行逻辑，便于DAG管理
    """
    id: str
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    executor: Optional[Callable] = None


class DAGExecutor:
    """
    DAG工作流执行器

    功能：
    1. 构建Agent依赖图
    2. 拓扑排序确定执行顺序
    3. 并行执行无依赖的Agent
    4. 动态调整依赖关系
    5. 错误处理和失败传播

    Why:
    - 提高执行效率：无依赖的Agent可以并行执行
    - 灵活的工作流：支持动态依赖调整
    - 清晰的依赖关系：通过DAG可视化Agent协作

    How to apply:
    - 定义Agent之间的依赖关系
    - 添加Agent节点到DAG
    - 执行DAG，自动并行调度

    Example:
        executor = DAGExecutor()
        executor.add_node("Requester", dependencies=[])
        executor.add_node("Architect", dependencies=["Requester"])
        executor.add_node("Developer", dependencies=["Architect"])
        executor.add_node("Tester", dependencies=["Developer"])
        await executor.execute()
    """

    def __init__(self, max_parallel: int = 3):
        """
        初始化DAG执行器

        Args:
            max_parallel: 最大并行任务数

        Why: 限制并行数避免资源耗尽（LLM API限流、内存占用）
        """
        self.nodes: Dict[str, DAGNode] = {}
        self.max_parallel = max_parallel
        self.execution_order: List[List[str]] = []  # 分层执行顺序

    def add_node(
        self,
        node_id: str,
        dependencies: Optional[List[str]] = None,
        executor: Optional[Callable] = None
    ):
        """
        添加节点到DAG

        Args:
            node_id: 节点ID（Agent名称）
            dependencies: 依赖的节点ID列表
            executor: 执行函数（async callable）

        Why: 构建Agent依赖图，定义工作流结构
        """
        if dependencies is None:
            dependencies = []

        self.nodes[node_id] = DAGNode(
            id=node_id,
            dependencies=dependencies,
            executor=executor
        )

    def add_dependency(self, node_id: str, dependency_id: str):
        """
        添加依赖关系

        Args:
            node_id: 节点ID
            dependency_id: 依赖的节点ID

        Why: 支持动态调整依赖关系，适应运行时变化
        """
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        if dependency_id not in self.nodes:
            raise ValueError(f"Dependency {dependency_id} not found")

        if dependency_id not in self.nodes[node_id].dependencies:
            self.nodes[node_id].dependencies.append(dependency_id)

    def remove_dependency(self, node_id: str, dependency_id: str):
        """
        移除依赖关系

        Args:
            node_id: 节点ID
            dependency_id: 依赖的节点ID

        Why: 支持动态优化工作流，跳过不必要的依赖
        """
        if node_id in self.nodes and dependency_id in self.nodes[node_id].dependencies:
            self.nodes[node_id].dependencies.remove(dependency_id)

    def topological_sort(self) -> List[List[str]]:
        """
        拓扑排序，返回分层执行顺序

        Returns:
            分层节点ID列表，每层的节点可以并行执行
            例如: [["Requester"], ["Architect", "ProductManager"], ["Developer"]]

        Why:
        - 确保依赖顺序正确（依赖的Agent先执行）
        - 识别可并行执行的Agent（同一层）
        - 检测循环依赖

        Algorithm:
        - Kahn算法：计算入度，逐层移除入度为0的节点
        """
        # 计算入度
        in_degree = {node_id: len(node.dependencies) for node_id, node in self.nodes.items()}

        # 找到入度为0的节点（没有依赖）
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])

        result = []
        while queue:
            # 当前层的所有节点（可并行执行）
            current_layer = []
            layer_size = len(queue)

            for _ in range(layer_size):
                node_id = queue.popleft()
                current_layer.append(node_id)

                # 减少依赖此节点的其他节点的入度
                for other_id, other_node in self.nodes.items():
                    if node_id in other_node.dependencies:
                        in_degree[other_id] -= 1
                        if in_degree[other_id] == 0:
                            queue.append(other_id)

            result.append(current_layer)

        # 检查是否有循环依赖
        if sum(len(layer) for layer in result) != len(self.nodes):
            raise ValueError("Circular dependency detected in DAG")

        return result

    async def execute_node(self, node_id: str) -> bool:
        """
        执行单个节点

        Args:
            node_id: 节点ID

        Returns:
            是否执行成功

        Why: 封装节点执行逻辑，统一错误处理
        """
        node = self.nodes[node_id]

        # 检查依赖是否都已完成
        for dep_id in node.dependencies:
            dep_node = self.nodes[dep_id]
            if dep_node.status != TaskStatus.COMPLETED:
                node.status = TaskStatus.SKIPPED
                node.error = f"Dependency {dep_id} not completed (status: {dep_node.status})"
                return False

        # 执行节点
        node.status = TaskStatus.RUNNING
        try:
            if node.executor:
                # 传递依赖节点的结果
                dep_results = {dep_id: self.nodes[dep_id].result for dep_id in node.dependencies}
                node.result = await node.executor(dep_results)
            else:
                node.result = None

            node.status = TaskStatus.COMPLETED
            return True

        except Exception as e:
            node.status = TaskStatus.FAILED
            node.error = str(e)
            return False

    async def execute(self) -> Dict[str, Any]:
        """
        执行整个DAG工作流

        Returns:
            所有节点的执行结果 {node_id: result}

        Why:
        - 自动并行调度，提高执行效率
        - 统一错误处理和状态管理
        - 返回完整执行结果

        Algorithm:
        1. 拓扑排序得到分层执行顺序
        2. 逐层执行，每层内并行执行（限制并发数）
        3. 如果某层有失败，后续依赖该节点的任务跳过
        """
        # 拓扑排序
        self.execution_order = self.topological_sort()

        # 逐层执行
        for layer in self.execution_order:
            # 标记为就绪
            for node_id in layer:
                self.nodes[node_id].status = TaskStatus.READY

            # 并行执行当前层（限制并发数）
            tasks = []
            for i in range(0, len(layer), self.max_parallel):
                batch = layer[i:i + self.max_parallel]
                batch_tasks = [self.execute_node(node_id) for node_id in batch]
                await asyncio.gather(*batch_tasks)

        # 收集结果
        results = {
            node_id: {
                "status": node.status.value,
                "result": node.result,
                "error": node.error
            }
            for node_id, node in self.nodes.items()
        }

        return results

    def get_execution_plan(self) -> List[List[str]]:
        """
        获取执行计划（不实际执行）

        Returns:
            分层执行顺序

        Why: 让用户预览工作流执行顺序，确认无误后再执行
        """
        return self.topological_sort()

    def visualize(self) -> str:
        """
        可视化DAG（文本格式）

        Returns:
            DAG的文本表示

        Why: 帮助理解Agent依赖关系，调试工作流

        Example:
            Layer 0: Requester
            Layer 1: Architect, ProductManager
            Layer 2: Developer
            Layer 3: CodeReviewer, Tester
            Layer 4: DevOps
        """
        execution_order = self.topological_sort()

        lines = ["DAG Execution Plan:", "=" * 50]
        for i, layer in enumerate(execution_order):
            lines.append(f"Layer {i}: {', '.join(layer)}")

        lines.append("=" * 50)
        lines.append(f"Total layers: {len(execution_order)}")
        lines.append(f"Total nodes: {len(self.nodes)}")

        return "\n".join(lines)

    def get_node_status(self, node_id: str) -> Optional[TaskStatus]:
        """
        获取节点状态

        Args:
            node_id: 节点ID

        Returns:
            节点状态
        """
        if node_id in self.nodes:
            return self.nodes[node_id].status
        return None

    def get_all_statuses(self) -> Dict[str, str]:
        """
        获取所有节点状态

        Returns:
            {node_id: status} 字典
        """
        return {node_id: node.status.value for node_id, node in self.nodes.items()}
