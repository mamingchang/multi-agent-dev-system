"""
告警系统

实现阈值告警和趋势告警。

告警规则：
1. 阈值告警：指标超过设定阈值
2. 趋势告警：指标变化趋势异常

告警级别：
- Warning：邮件通知
- Critical：IM消息通知
- Emergency：短信通知
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from collections import deque


class AlertLevel(str, Enum):
    """告警级别"""
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertRule:
    """告警规则"""

    def __init__(
        self,
        name: str,
        metric_name: str,
        condition: Callable[[float], bool],
        level: AlertLevel,
        description: str = ""
    ):
        """
        初始化告警规则

        Args:
            name: 规则名称
            metric_name: 指标名称
            condition: 条件函数（返回True表示触发告警）
            level: 告警级别
            description: 规则描述
        """
        self.name = name
        self.metric_name = metric_name
        self.condition = condition
        self.level = level
        self.description = description


class Alert:
    """告警记录"""

    def __init__(
        self,
        rule_name: str,
        level: AlertLevel,
        message: str,
        metric_value: float,
        timestamp: Optional[datetime] = None
    ):
        """
        初始化告警记录

        Args:
            rule_name: 规则名称
            level: 告警级别
            message: 告警消息
            metric_value: 指标值
            timestamp: 时间戳
        """
        self.rule_name = rule_name
        self.level = level
        self.message = message
        self.metric_value = metric_value
        self.timestamp = timestamp or datetime.utcnow()
        self.resolved = False
        self.resolved_at: Optional[datetime] = None

    def resolve(self):
        """解决告警"""
        self.resolved = True
        self.resolved_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rule_name": self.rule_name,
            "level": self.level.value,
            "message": self.message,
            "metric_value": self.metric_value,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


class AlertManager:
    """告警管理器"""

    def __init__(self):
        """初始化告警管理器"""
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: List[Alert] = []
        self.alert_history: deque = deque(maxlen=1000)  # 保留最近1000条告警

        # 初始化默认规则
        self._init_default_rules()

    def _init_default_rules(self):
        """初始化默认告警规则"""
        # CPU使用率告警
        self.add_rule(AlertRule(
            name="high_cpu_usage",
            metric_name="cpu_percent",
            condition=lambda x: x > 80,
            level=AlertLevel.WARNING,
            description="CPU使用率超过80%"
        ))

        # 内存使用率告警
        self.add_rule(AlertRule(
            name="high_memory_usage",
            metric_name="memory_percent",
            condition=lambda x: x > 85,
            level=AlertLevel.CRITICAL,
            description="内存使用率超过85%"
        ))

        # 任务失败率告警
        self.add_rule(AlertRule(
            name="high_task_failure_rate",
            metric_name="task_failure_rate",
            condition=lambda x: x > 10,
            level=AlertLevel.CRITICAL,
            description="任务失败率超过10%"
        ))

        # LLM错误率告警
        self.add_rule(AlertRule(
            name="high_llm_error_rate",
            metric_name="llm_error_rate",
            condition=lambda x: x > 5,
            level=AlertLevel.WARNING,
            description="LLM错误率超过5%"
        ))

        # 系统错误率告警
        self.add_rule(AlertRule(
            name="critical_system_error_rate",
            metric_name="system_error_rate",
            condition=lambda x: x > 50,
            level=AlertLevel.EMERGENCY,
            description="系统错误率超过50%"
        ))

    def add_rule(self, rule: AlertRule):
        """
        添加告警规则

        Args:
            rule: 告警规则
        """
        self.rules[rule.name] = rule

    def remove_rule(self, rule_name: str):
        """
        移除告警规则

        Args:
            rule_name: 规则名称
        """
        if rule_name in self.rules:
            del self.rules[rule_name]

    def check_metrics(self, metrics: Dict[str, float]) -> List[Alert]:
        """
        检查指标并触发告警

        Args:
            metrics: 指标字典

        Returns:
            List[Alert]: 触发的告警列表
        """
        triggered_alerts = []

        for rule in self.rules.values():
            if rule.metric_name not in metrics:
                continue

            metric_value = metrics[rule.metric_name]

            # 检查条件
            if rule.condition(metric_value):
                # 触发告警
                alert = Alert(
                    rule_name=rule.name,
                    level=rule.level,
                    message=f"{rule.description}: 当前值 {metric_value}",
                    metric_value=metric_value
                )

                triggered_alerts.append(alert)
                self.alerts.append(alert)
                self.alert_history.append(alert)

                print(f"[{rule.level.value.upper()}] {alert.message}")

        return triggered_alerts

    def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[Alert]:
        """
        获取活跃告警

        Args:
            level: 告警级别过滤

        Returns:
            List[Alert]: 活跃告警列表
        """
        active = [a for a in self.alerts if not a.resolved]

        if level:
            active = [a for a in active if a.level == level]

        return active

    def resolve_alert(self, rule_name: str):
        """
        解决告警

        Args:
            rule_name: 规则名称
        """
        for alert in self.alerts:
            if alert.rule_name == rule_name and not alert.resolved:
                alert.resolve()

    def get_alert_stats(self) -> Dict[str, Any]:
        """
        获取告警统计

        Returns:
            dict: 告警统计
        """
        total = len(self.alerts)
        active = len([a for a in self.alerts if not a.resolved])
        resolved = total - active

        by_level = {
            "warning": len([a for a in self.alerts if a.level == AlertLevel.WARNING]),
            "critical": len([a for a in self.alerts if a.level == AlertLevel.CRITICAL]),
            "emergency": len([a for a in self.alerts if a.level == AlertLevel.EMERGENCY])
        }

        return {
            "total": total,
            "active": active,
            "resolved": resolved,
            "by_level": by_level
        }


class TrendAnalyzer:
    """趋势分析器"""

    def __init__(self, window_size: int = 10):
        """
        初始化趋势分析器

        Args:
            window_size: 窗口大小（数据点数量）
        """
        self.window_size = window_size
        self.data: Dict[str, deque] = {}

    def add_data_point(self, metric_name: str, value: float):
        """
        添加数据点

        Args:
            metric_name: 指标名称
            value: 指标值
        """
        if metric_name not in self.data:
            self.data[metric_name] = deque(maxlen=self.window_size)

        self.data[metric_name].append(value)

    def detect_anomaly(self, metric_name: str, threshold: float = 2.0) -> bool:
        """
        检测异常（基于标准差）

        Args:
            metric_name: 指标名称
            threshold: 阈值（标准差倍数）

        Returns:
            bool: 是否异常
        """
        if metric_name not in self.data or len(self.data[metric_name]) < 3:
            return False

        values = list(self.data[metric_name])
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5

        # 检查最新值是否偏离均值超过阈值
        latest = values[-1]
        deviation = abs(latest - mean)

        return deviation > threshold * std_dev

    def get_trend(self, metric_name: str) -> str:
        """
        获取趋势方向

        Args:
            metric_name: 指标名称

        Returns:
            str: 趋势方向（"up", "down", "stable"）
        """
        if metric_name not in self.data or len(self.data[metric_name]) < 2:
            return "stable"

        values = list(self.data[metric_name])

        # 简单的线性趋势判断
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)

        diff = second_half - first_half
        threshold = first_half * 0.1  # 10%变化

        if diff > threshold:
            return "up"
        elif diff < -threshold:
            return "down"
        else:
            return "stable"


# 全局告警管理器实例
alert_manager = AlertManager()

# 全局趋势分析器实例
trend_analyzer = TrendAnalyzer()
