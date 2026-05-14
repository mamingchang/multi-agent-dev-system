"""
成本优化API路由

端点：
- GET /cost/organization/{organization_id} - 获取组织成本
- GET /cost/project/{project_id} - 获取项目成本
- GET /cost/task/{task_id} - 获取任务成本
- GET /cost/agent/{agent_name}/average - 获取Agent平均成本
- GET /cost/trend/{organization_id} - 获取成本趋势
- GET /cost/alerts - 获取成本告警
- POST /cost/alerts/check - 检查成本告警
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from ..database.models import User
from ..cost.cost_analyzer import cost_analyzer
from ..cost.alert_manager import cost_alert_manager, AlertLevel
from .auth import get_current_active_user

router = APIRouter(prefix="/cost", tags=["成本优化"])


class CheckAlertsRequest(BaseModel):
    """检查告警请求"""
    organization_id: int
    current_usage: int
    total_quota: int
    task_id: Optional[int] = None
    task_cost: Optional[float] = None


@router.get("/organization/{organization_id}")
def get_organization_cost(
    organization_id: int,
    start_date: Optional[str] = Query(None, description="开始日期 (ISO格式)"),
    end_date: Optional[str] = Query(None, description="结束日期 (ISO格式)"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取组织成本统计

    需要登录。
    """
    # 解析日期
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None

    return cost_analyzer.get_organization_cost(
        organization_id=organization_id,
        start_date=start,
        end_date=end
    )


@router.get("/project/{project_id}")
def get_project_cost(
    project_id: int,
    start_date: Optional[str] = Query(None, description="开始日期 (ISO格式)"),
    end_date: Optional[str] = Query(None, description="结束日期 (ISO格式)"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取项目成本统计

    需要登录。
    """
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None

    return cost_analyzer.get_project_cost(
        project_id=project_id,
        start_date=start,
        end_date=end
    )


@router.get("/task/{task_id}")
def get_task_cost(
    task_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    获取任务成本统计

    需要登录。
    """
    return cost_analyzer.get_task_cost(task_id=task_id)


@router.get("/agent/{agent_name}/average")
def get_agent_average_cost(
    agent_name: str,
    organization_id: Optional[int] = Query(None, description="组织ID"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取Agent平均成本

    需要登录。
    """
    return cost_analyzer.get_agent_average_cost(
        agent_name=agent_name,
        organization_id=organization_id
    )


@router.get("/trend/{organization_id}")
def get_cost_trend(
    organization_id: int,
    days: int = Query(7, ge=1, le=90, description="天数"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取成本趋势

    需要登录。
    """
    trend = cost_analyzer.get_cost_trend(
        organization_id=organization_id,
        days=days
    )

    return {
        "organization_id": organization_id,
        "days": days,
        "trend": trend
    }


@router.get("/alerts")
def get_cost_alerts(
    organization_id: Optional[int] = Query(None, description="组织ID"),
    level: Optional[str] = Query(None, description="告警级别"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取成本告警

    需要登录。
    """
    # 解析告警级别
    alert_level = None
    if level:
        try:
            alert_level = AlertLevel(level.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的告警级别: {level}"
            )

    alerts = cost_alert_manager.get_active_alerts(
        organization_id=organization_id,
        level=alert_level
    )

    return {
        "total": len(alerts),
        "alerts": [alert.to_dict() for alert in alerts]
    }


@router.post("/alerts/check")
def check_cost_alerts(
    request: CheckAlertsRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    检查成本告警

    需要登录。
    """
    alerts = cost_alert_manager.check_all_alerts(
        organization_id=request.organization_id,
        current_usage=request.current_usage,
        total_quota=request.total_quota,
        task_id=request.task_id,
        task_cost=request.task_cost
    )

    return {
        "checked": True,
        "alert_count": len(alerts),
        "alerts": [alert.to_dict() for alert in alerts]
    }


@router.get("/models/prices")
def get_model_prices(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取模型价格表

    需要登录。
    """
    return {
        "models": cost_analyzer.MODEL_PRICES,
        "unit": "USD per 1000 tokens"
    }
