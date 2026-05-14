"""
成本预警系统

实现智能的成本预警机制。

预警类型：
1. 异常消耗告警：任务Token消耗超过历史平均值2倍
2. 趋势预警：按当前速度预计7天内配额耗尽
3. 对比预警：本月消耗比上月增长>50%
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from .cost_analyzer import cost_analyzer


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class CostAlert:
    """成本告警"""

    def __init__(
        self,
        alert_type: str,
        level: AlertLevel,
        message: str,
        details: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ):
        """
        初始化告警

        Args:
            alert_type: 告警类型
            level: 告警级别
            message: 告警消息
            details: 详细信息
            timestamp: 时间戳
        """
        self.alert_type = alert_type
        self.level = level
        self.message = message
        self.details = details
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "alert_type": self.alert_type,
            "level": self.level.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class CostAlertManager:
    """成本告警管理器"""

    def __init__(self):
        """初始化告警管理器"""
        self.alerts: List[CostAlert] = []
        self.task_history: Dict[int, List[float]] = {}  # task_id -> [costs]

    def check_task_anomaly(
        self,
        task_id: int,
        current_cost: float,
        threshold_multiplier: float = 2.0
    ) -> Optional[CostAlert]:
        """
        检查任务异常消耗

        Args:
            task_id: 任务ID
            current_cost: 当前成本
            threshold_multiplier: 阈值倍数

        Returns:
            Optional[CostAlert]: 告警（如果有）
        """
        # 获取历史成本
        history = self.task_history.get(task_id, [])

        if not history:
            # 没有历史数据，记录当前成本
            self.task_history[task_id] = [current_cost]
            return None

        # 计算历史平均值
        avg_cost = sum(history) / len(history)

        # 检查是否超过阈值
        if current_cost > avg_cost * threshold_multiplier:
            alert = CostAlert(
                alert_type="task_anomaly",
                level=AlertLevel.WARNING,
                message=f"任务 {task_id} 成本异常：当前 ${current_cost:.4f}，历史平均 ${avg_cost:.4f}",
                details={
                    "task_id": task_id,
                    "current_cost": current_cost,
                    "average_cost": avg_cost,
                    "threshold": avg_cost * threshold_multiplier,
                    "multiplier": current_cost / avg_cost
                }
            )

            self.alerts.append(alert)
            return alert

        # 记录当前成本
        self.task_history[task_id].append(current_cost)

        return None

    def check_quota_depletion(
        self,
        organization_id: int,
        current_usage: int,
        total_quota: int,
        days_to_check: int = 7
    ) -> Optional[CostAlert]:
        """
        检查配额耗尽趋势

        Args:
            organization_id: 组织ID
            current_usage: 当前使用量
            total_quota: 总配额
            days_to_check: 检查天数

        Returns:
            Optional[CostAlert]: 告警（如果有）
        """
        # 获取最近N天的使用趋势
        trend = cost_analyzer.get_cost_trend(
            organization_id=organization_id,
            days=days_to_check
        )

        if not trend:
            return None

        # 计算每日平均消耗
        total_tokens = sum(day["tokens"] for day in trend)
        daily_avg = total_tokens / days_to_check

        if daily_avg == 0:
            return None

        # 计算剩余配额可用天数
        remaining_quota = total_quota - current_usage
        days_remaining = remaining_quota / daily_avg

        # 如果预计7天内耗尽，发出告警
        if days_remaining < 7:
            level = AlertLevel.CRITICAL if days_remaining < 3 else AlertLevel.WARNING

            alert = CostAlert(
                alert_type="quota_depletion",
                level=level,
                message=f"组织 {organization_id} 配额预计 {days_remaining:.1f} 天内耗尽",
                details={
                    "organization_id": organization_id,
                    "current_usage": current_usage,
                    "total_quota": total_quota,
                    "remaining_quota": remaining_quota,
                    "daily_average": int(daily_avg),
                    "days_remaining": round(days_remaining, 1)
                }
            )

            self.alerts.append(alert)
            return alert

        return None

    def check_monthly_growth(
        self,
        organization_id: int,
        growth_threshold: float = 0.5
    ) -> Optional[CostAlert]:
        """
        检查月度增长

        Args:
            organization_id: 组织ID
            growth_threshold: 增长阈值（50%）

        Returns:
            Optional[CostAlert]: 告警（如果有）
        """
        now = datetime.utcnow()

        # 本月成本
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month_cost = cost_analyzer.get_organization_cost(
            organization_id=organization_id,
            start_date=this_month_start,
            end_date=now
        )

        # 上月成本
        last_month_end = this_month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_cost = cost_analyzer.get_organization_cost(
            organization_id=organization_id,
            start_date=last_month_start,
            end_date=last_month_end
        )

        this_cost = this_month_cost["total_cost"]
        last_cost = last_month_cost["total_cost"]

        if last_cost == 0:
            return None

        # 计算增长率
        growth_rate = (this_cost - last_cost) / last_cost

        # 如果增长超过阈值，发出告警
        if growth_rate > growth_threshold:
            alert = CostAlert(
                alert_type="monthly_growth",
                level=AlertLevel.WARNING,
                message=f"组织 {organization_id} 本月成本增长 {growth_rate*100:.1f}%",
                details={
                    "organization_id": organization_id,
                    "this_month_cost": this_cost,
                    "last_month_cost": last_cost,
                    "growth_rate": round(growth_rate, 3),
                    "growth_percentage": f"{growth_rate*100:.1f}%",
                    "threshold": growth_threshold
                }
            )

            self.alerts.append(alert)
            return alert

        return None

    def check_all_alerts(
        self,
        organization_id: int,
        current_usage: int,
        total_quota: int,
        task_id: Optional[int] = None,
        task_cost: Optional[float] = None
    ) -> List[CostAlert]:
        """
        检查所有告警

        Args:
            organization_id: 组织ID
            current_usage: 当前使用量
            total_quota: 总配额
            task_id: 任务ID（可选）
            task_cost: 任务成本（可选）

        Returns:
            List[CostAlert]: 告警列表
        """
        alerts = []

        # 检查任务异常
        if task_id is not None and task_cost is not None:
            alert = self.check_task_anomaly(task_id, task_cost)
            if alert:
                alerts.append(alert)

        # 检查配额耗尽
        alert = self.check_quota_depletion(
            organization_id,
            current_usage,
            total_quota
        )
        if alert:
            alerts.append(alert)

        # 检查月度增长
        alert = self.check_monthly_growth(organization_id)
        if alert:
            alerts.append(alert)

        return alerts

    def get_active_alerts(
        self,
        organization_id: Optional[int] = None,
        level: Optional[AlertLevel] = None
    ) -> List[CostAlert]:
        """
        获取活跃告警

        Args:
            organization_id: 组织ID（可选）
            level: 告警级别（可选）

        Returns:
            List[CostAlert]: 告警列表
        """
        alerts = self.alerts

        # 过滤组织
        if organization_id is not None:
            alerts = [
                a for a in alerts
                if a.details.get("organization_id") == organization_id
            ]

        # 过滤级别
        if level is not None:
            alerts = [a for a in alerts if a.level == level]

        # 只返回最近24小时的告警
        cutoff = datetime.utcnow() - timedelta(hours=24)
        alerts = [a for a in alerts if a.timestamp >= cutoff]

        return alerts

    def clear_old_alerts(self, hours: int = 24):
        """
        清理旧告警

        Args:
            hours: 保留小时数
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        self.alerts = [a for a in self.alerts if a.timestamp >= cutoff]


# 全局告警管理器实例
cost_alert_manager = CostAlertManager()
