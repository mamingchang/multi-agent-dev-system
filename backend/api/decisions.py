"""
Decisions API - Handle human decision workflow
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from ..dependencies import get_db, get_current_user
from ..config import settings
from src.decision_queue import DecisionQueue
from src.database.models import DecisionStatus

router = APIRouter(prefix="/api/decisions", tags=["decisions"])


class DecisionResponse(BaseModel):
    approved: bool
    feedback: str = ""
    data: dict = {}


@router.get("/pending")
async def get_pending_decisions(
    project_id: int = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get pending decisions for current user"""
    decision_queue = DecisionQueue(db)

    decisions = decision_queue.get_pending_decisions(
        user_id=current_user["id"],
        project_id=project_id
    )

    return {
        "decisions": [
            {
                "id": d.id,
                "task_id": d.task_id,
                "agent_name": d.agent_name,
                "decision_type": d.decision_type,
                "context": d.context,
                "created_at": d.created_at.isoformat()
            }
            for d in decisions
        ]
    }


@router.get("/{decision_id}")
async def get_decision(
    decision_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get decision details"""
    from src.database.models import PendingDecision

    decision = db.query(PendingDecision).filter(
        PendingDecision.id == decision_id
    ).first()

    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    # Check permission
    if decision.assigned_to != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    return {
        "id": decision.id,
        "task_id": decision.task_id,
        "agent_name": decision.agent_name,
        "decision_type": decision.decision_type,
        "context": decision.context,
        "status": decision.status,
        "response": decision.response,
        "created_at": decision.created_at.isoformat(),
        "resolved_at": decision.resolved_at.isoformat() if decision.resolved_at else None
    }


@router.post("/{decision_id}/resolve")
async def resolve_decision(
    decision_id: int,
    response: DecisionResponse,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Resolve a pending decision"""
    decision_queue = DecisionQueue(db)

    success = decision_queue.resolve_decision(
        decision_id=decision_id,
        user_id=current_user["id"],
        response=response.dict()
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to resolve decision")

    return {"message": "Decision resolved successfully"}


@router.get("/my-history")
async def get_my_decision_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get user's decision history"""
    from src.database.models import PendingDecision

    decisions = db.query(PendingDecision).filter(
        PendingDecision.assigned_to == current_user["id"],
        PendingDecision.status == DecisionStatus.RESOLVED
    ).order_by(PendingDecision.resolved_at.desc()).limit(limit).all()

    return {
        "decisions": [
            {
                "id": d.id,
                "task_id": d.task_id,
                "agent_name": d.agent_name,
                "decision_type": d.decision_type,
                "response": d.response,
                "resolved_at": d.resolved_at.isoformat()
            }
            for d in decisions
        ]
    }
