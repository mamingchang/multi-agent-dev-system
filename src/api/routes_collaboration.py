"""
Agent协作API路由

提供Agent协作相关的API端点：
- DAG工作流执行
- 任务分解
- Agent投票
- 冲突解决
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from src.workflow.dag_executor import DAGExecutor, TaskStatus
from src.workflow.task_decomposer import TaskDecomposer, TaskComplexity
from src.workflow.voting_system import VotingSystem, VoteOption, ConflictResolver


router = APIRouter(prefix="/collaboration", tags=["collaboration"])


# ============ Request/Response Models ============

class DAGNodeRequest(BaseModel):
    """DAG节点请求"""
    node_id: str
    dependencies: List[str] = []


class DAGExecutionRequest(BaseModel):
    """DAG执行请求"""
    nodes: List[DAGNodeRequest]
    max_parallel: int = 3


class TaskDecompositionRequest(BaseModel):
    """任务分解请求"""
    task_description: str


class VoteRequest(BaseModel):
    """投票请求"""
    agent_name: str
    option: str  # approve/reject/abstain/conditional
    reason: str
    conditions: Optional[List[str]] = None


class VotingSessionRequest(BaseModel):
    """投票会话请求"""
    session_id: str
    threshold: float = 0.6
    agent_weights: Optional[Dict[str, float]] = None


# ============ DAG Workflow Endpoints ============

@router.post("/dag/plan")
async def create_dag_execution_plan(request: DAGExecutionRequest):
    """
    创建DAG执行计划

    Args:
        request: DAG执行请求

    Returns:
        执行计划（分层顺序）

    Why: 让用户预览工作流执行顺序，确认无误后再执行

    Example:
        POST /api/collaboration/dag/plan
        {
            "nodes": [
                {"node_id": "Requester", "dependencies": []},
                {"node_id": "Architect", "dependencies": ["Requester"]},
                {"node_id": "Developer", "dependencies": ["Architect"]}
            ],
            "max_parallel": 3
        }

        Response:
        {
            "execution_plan": [
                ["Requester"],
                ["Architect"],
                ["Developer"]
            ],
            "total_layers": 3,
            "visualization": "..."
        }
    """
    executor = DAGExecutor(max_parallel=request.max_parallel)

    # 添加节点
    for node in request.nodes:
        executor.add_node(node.node_id, node.dependencies)

    # 获取执行计划
    try:
        execution_plan = executor.get_execution_plan()
        visualization = executor.visualize()

        return {
            "execution_plan": execution_plan,
            "total_layers": len(execution_plan),
            "total_nodes": len(request.nodes),
            "visualization": visualization
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/dag/execute")
async def execute_dag_workflow(request: DAGExecutionRequest):
    """
    执行DAG工作流

    Args:
        request: DAG执行请求

    Returns:
        执行结果

    Why: 并行执行无依赖的Agent，提高效率

    Note: 这是简化版本，实际应该异步执行并返回任务ID
    """
    executor = DAGExecutor(max_parallel=request.max_parallel)

    # 添加节点（这里使用mock executor）
    for node in request.nodes:
        async def mock_executor(deps):
            # 实际应该调用真实的Agent
            return {"status": "completed", "output": f"Mock output for {node.node_id}"}

        executor.add_node(node.node_id, node.dependencies, mock_executor)

    # 执行
    try:
        results = await executor.execute()
        return {
            "status": "completed",
            "results": results,
            "execution_plan": executor.execution_order
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dag/status/{node_id}")
async def get_dag_node_status(node_id: str):
    """
    获取DAG节点状态

    Args:
        node_id: 节点ID

    Returns:
        节点状态

    Note: 实际应该从持久化存储中获取
    """
    # 简化实现
    return {
        "node_id": node_id,
        "status": "completed",
        "result": None
    }


# ============ Task Decomposition Endpoints ============

@router.post("/decompose/analyze")
async def analyze_task_complexity(request: TaskDecompositionRequest):
    """
    分析任务复杂度并生成分解建议

    Args:
        request: 任务分解请求

    Returns:
        分解建议

    Why: 帮助用户判断是否需要分解任务

    Example:
        POST /api/collaboration/decompose/analyze
        {
            "task_description": "开发一个完整的用户管理系统，包括注册、登录、权限管理等功能"
        }

        Response:
        {
            "complexity": "complex",
            "should_decompose": true,
            "reason": "任务描述较长或包含系统级关键词，建议分解为多个子任务",
            "subtasks": [...],
            "total_estimated_time": 270
        }
    """
    decomposer = TaskDecomposer()

    try:
        suggestion = await decomposer.analyze(request.task_description)

        return {
            "complexity": suggestion.complexity.value,
            "should_decompose": suggestion.should_decompose,
            "reason": suggestion.reason,
            "subtasks": [
                {
                    "id": st.id,
                    "title": st.title,
                    "description": st.description,
                    "agent": st.agent,
                    "dependencies": st.dependencies,
                    "estimated_time": st.estimated_time,
                    "priority": st.priority
                }
                for st in suggestion.subtasks
            ],
            "total_estimated_time": suggestion.total_estimated_time
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decompose/create")
async def create_subtasks(
    task_description: str,
    parent_task_id: str
):
    """
    创建子任务

    Args:
        task_description: 任务描述
        parent_task_id: 父任务ID

    Returns:
        创建的子任务列表

    Why: 将分解建议转换为实际的子任务
    """
    decomposer = TaskDecomposer()

    try:
        # 分析任务
        suggestion = await decomposer.analyze(task_description)

        if not suggestion.should_decompose:
            return {
                "message": "任务无需分解",
                "subtasks": []
            }

        # 创建子任务
        subtasks = await decomposer.create_subtasks(suggestion, parent_task_id)

        return {
            "message": f"成功创建{len(subtasks)}个子任务",
            "subtasks": subtasks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Voting System Endpoints ============

@router.post("/voting/create")
async def create_voting_session(request: VotingSessionRequest):
    """
    创建投票会话

    Args:
        request: 投票会话请求

    Returns:
        会话信息

    Why: 初始化投票会话，设置阈值和权重

    Note: 实际应该持久化会话信息
    """
    voting = VotingSystem(threshold=request.threshold)

    # 设置Agent权重
    if request.agent_weights:
        for agent_name, weight in request.agent_weights.items():
            voting.set_agent_weight(agent_name, weight)

    return {
        "session_id": request.session_id,
        "threshold": request.threshold,
        "agent_weights": voting.agent_weights,
        "status": "active"
    }


@router.post("/voting/{session_id}/vote")
async def submit_vote(session_id: str, vote: VoteRequest):
    """
    提交投票

    Args:
        session_id: 会话ID
        vote: 投票请求

    Returns:
        投票确认

    Why: 记录Agent的投票意见

    Example:
        POST /api/collaboration/voting/session-123/vote
        {
            "agent_name": "Architect",
            "option": "approve",
            "reason": "技术方案可行"
        }
    """
    # 简化实现：实际应该从存储中获取会话
    voting = VotingSystem()

    try:
        vote_option = VoteOption(vote.option)
        voting.add_vote(
            agent_name=vote.agent_name,
            option=vote_option,
            reason=vote.reason,
            conditions=vote.conditions
        )

        return {
            "session_id": session_id,
            "agent_name": vote.agent_name,
            "option": vote.option,
            "status": "recorded"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid vote option: {vote.option}")


@router.get("/voting/{session_id}/result")
async def get_voting_result(session_id: str):
    """
    获取投票结果

    Args:
        session_id: 会话ID

    Returns:
        投票结果

    Why: 计算投票结果，判断是否通过

    Example:
        GET /api/collaboration/voting/session-123/result

        Response:
        {
            "passed": true,
            "approve_score": 7.5,
            "reject_score": 1.5,
            "abstain_count": 0,
            "consensus_level": 0.83,
            "conflicts": [],
            "summary": "..."
        }
    """
    # 简化实现：实际应该从存储中获取会话和投票
    voting = VotingSystem()

    # Mock一些投票
    voting.add_vote("Architect", VoteOption.APPROVE, "技术方案可行")
    voting.add_vote("Developer", VoteOption.APPROVE, "可以实现")
    voting.add_vote("Tester", VoteOption.CONDITIONAL, "需要增加测试", ["添加单元测试"])

    result = voting.calculate_result()
    summary = voting.get_summary()

    return {
        "session_id": session_id,
        "passed": result.passed,
        "approve_score": result.approve_score,
        "reject_score": result.reject_score,
        "abstain_count": result.abstain_count,
        "consensus_level": result.consensus_level,
        "conflicts": result.conflicts,
        "votes": [
            {
                "agent_name": v.agent_name,
                "option": v.option.value,
                "reason": v.reason,
                "weight": v.weight
            }
            for v in result.votes
        ],
        "summary": summary
    }


@router.post("/voting/{session_id}/resolve")
async def resolve_conflict(session_id: str):
    """
    解决投票冲突

    Args:
        session_id: 会话ID

    Returns:
        冲突分析和解决建议

    Why: 自动分析冲突，提供解决方案

    Example:
        POST /api/collaboration/voting/session-123/resolve

        Response:
        {
            "has_conflict": true,
            "analysis": "...",
            "suggestions": [...]
        }
    """
    # 简化实现
    voting = VotingSystem()
    voting.add_vote("Architect", VoteOption.APPROVE, "可行")
    voting.add_vote("Tester", VoteOption.REJECT, "测试不足")

    result = voting.calculate_result()

    resolver = ConflictResolver()
    analysis = await resolver.analyze_conflict(result)

    return {
        "session_id": session_id,
        **analysis
    }
