"""
Tasks and Decisions API
任务和决策管理API（简化版）
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime

from ..dependencies import get_current_user, get_decision_queue, get_event_logger
from src.decision_queue import DecisionQueue
from src.event_logger import EventLogger

router = APIRouter(prefix="/api", tags=["Tasks & Decisions"])


# Pydantic模型
class DecisionResponse(BaseModel):
    id: int
    task_id: str
    agent_name: str
    decision_type: str
    status: str
    created_at: datetime


class DecisionResolve(BaseModel):
    approved: bool
    message: str
    next_agent: str = None


class TimelineEvent(BaseModel):
    id: int
    agent_name: str
    agent_type: str
    event_type: str
    created_at: datetime


@router.get("/decisions/pending", response_model=List[DecisionResponse])
async def get_pending_decisions(
    current_user: dict = Depends(get_current_user),
    decision_queue: DecisionQueue = Depends(get_decision_queue)
):
    """获取待处理决策"""
    decisions = decision_queue.get_pending_decisions(user_id=current_user["id"])
    return [
        {
            "id": d.id,
            "task_id": d.task_id,
            "agent_name": d.agent_name,
            "decision_type": d.decision_type,
            "status": d.status.value,
            "created_at": d.created_at
        }
        for d in decisions
    ]


@router.post("/decisions/{decision_id}/resolve")
async def resolve_decision(
    decision_id: int,
    response: DecisionResolve,
    current_user: dict = Depends(get_current_user),
    decision_queue: DecisionQueue = Depends(get_decision_queue)
):
    """解决决策"""
    try:
        decision = decision_queue.resolve_decision(
            decision_id=decision_id,
            user_id=current_user["id"],
            response=response.dict()
        )
        return {"message": "Decision resolved", "decision_id": decision.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/{task_id}/timeline", response_model=List[TimelineEvent])
async def get_task_timeline(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    event_logger: EventLogger = Depends(get_event_logger)
):
    """获取任务时间线"""
    timeline = event_logger.get_task_timeline(task_id)
    return [
        {
            "id": e["id"],
            "agent_name": e["agent_name"],
            "agent_type": e["agent_type"],
            "event_type": e["event_type"],
            "created_at": datetime.fromisoformat(e["created_at"])
        }
        for e in timeline
    ]
