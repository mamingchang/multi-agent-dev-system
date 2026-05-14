"""
监控API路由

端点：
- GET /monitoring/metrics - 获取所有指标
- GET /monitoring/metrics/system - 获取系统指标
- GET /monitoring/metrics/business - 获取业务指标
- GET /monitoring/metrics/llm - 获取LLM指标
- GET /monitoring/traces/{trace_id} - 获取追踪详情
- GET /monitoring/traces/{trace_id}/summary - 获取追踪摘要
- GET /monitoring/alerts - 获取告警列表
- GET /monitoring/alerts/stats - 获取告警统计
- POST /monitoring/alerts/{rule_name}/resolve - 解决告警
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any

from ..database.models import User
from ..monitoring.metrics_collector import metrics_collector
from ..monitoring.tracer import tracer
from ..monitoring.alerting import alert_manager, AlertLevel
from .schemas import MessageResponse
from .auth import get_current_active_user

router = APIRouter(prefix="/monitoring", tags=["性能监控"])


@router.get("/metrics")
def get_all_metrics(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取所有指标

    需要登录。
    """
    return metrics_collector.get_all_metrics()


@router.get("/metrics/system")
def get_system_metrics(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取系统指标

    需要登录。
    """
    return metrics_collector.collect_system_metrics()


@router.get("/metrics/business")
def get_business_metrics(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取业务指标

    需要登录。
    """
    return metrics_collector.get_business_metrics()


@router.get("/metrics/llm")
def get_llm_metrics(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取LLM指标

    需要登录。
    """
    return metrics_collector.get_llm_metrics()


@router.get("/traces/{trace_id}")
def get_trace_details(
    trace_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    获取追踪详情

    需要登录。
    """
    spans = tracer.get_trace(trace_id)

    if not spans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="追踪不存在"
        )

    return {
        "trace_id": trace_id,
        "span_count": len(spans),
        "spans": [span.to_dict() for span in spans]
    }


@router.get("/traces/{trace_id}/summary")
def get_trace_summary(
    trace_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    获取追踪摘要

    需要登录。
    """
    summary = tracer.get_trace_summary(trace_id)

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="追踪不存在或未完成"
        )

    return summary


@router.get("/alerts")
def get_alerts(
    level: Optional[str] = Query(None, description="告警级别"),
    active_only: bool = Query(True, description="只返回活跃告警"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取告警列表

    需要登录。
    """
    # 转换告警级别
    alert_level = None
    if level:
        try:
            alert_level = AlertLevel[level.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的告警级别: {level}"
            )

    if active_only:
        alerts = alert_manager.get_active_alerts(alert_level)
    else:
        alerts = alert_manager.alerts
        if alert_level:
            alerts = [a for a in alerts if a.level == alert_level]

    return {
        "total": len(alerts),
        "alerts": [alert.to_dict() for alert in alerts]
    }


@router.get("/alerts/stats")
def get_alert_stats(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取告警统计

    需要登录。
    """
    return alert_manager.get_alert_stats()


@router.post("/alerts/{rule_name}/resolve", response_model=MessageResponse)
def resolve_alert(
    rule_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    解决告警

    需要登录。
    """
    alert_manager.resolve_alert(rule_name)

    return MessageResponse(message=f"告警 {rule_name} 已解决")


@router.post("/metrics/reset", response_model=MessageResponse)
def reset_metrics(
    current_user: User = Depends(get_current_active_user)
):
    """
    重置所有指标

    需要SuperAdmin权限。
    """
    # TODO: 检查SuperAdmin权限

    metrics_collector.reset_metrics()

    return MessageResponse(message="所有指标已重置")
