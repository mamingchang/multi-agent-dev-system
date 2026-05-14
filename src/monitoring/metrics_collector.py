"""
指标收集器

收集系统运行时的各种指标，用于监控和分析。

指标类型：
1. 基础指标：CPU、内存、磁盘、网络
2. 业务指标：任务数、成功率、平均执行时间、Token消耗
3. LLM指标：调用次数、响应时间、错误率、Token使用
"""

import time
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque


class MetricPoint:
    """指标数据点"""

    def __init__(self, name: str, value: float, labels: Dict[str, str] = None, timestamp: Optional[datetime] = None):
        """
        初始化指标数据点

        Args:
            name: 指标名称
            value: 指标值
            labels: 标签（用于多维度分组）
            timestamp: 时间戳
        """
        self.name = name
        self.value = value
        self.labels = labels or {}
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "value": self.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat()
        }


class Counter:
    """计数器指标"""

    def __init__(self, name: str, description: str = ""):
        """
        初始化计数器

        Args:
            name: 指标名称
            description: 指标描述
        """
        self.name = name
        self.description = description
        self.value = 0

    def inc(self, amount: float = 1):
        """增加计数"""
        self.value += amount

    def get(self) -> float:
        """获取当前值"""
        return self.value

    def reset(self):
        """重置计数"""
        self.value = 0


class Gauge:
    """仪表盘指标（可增可减）"""

    def __init__(self, name: str, description: str = ""):
        """
        初始化仪表盘

        Args:
            name: 指标名称
            description: 指标描述
        """
        self.name = name
        self.description = description
        self.value = 0

    def set(self, value: float):
        """设置值"""
        self.value = value

    def inc(self, amount: float = 1):
        """增加"""
        self.value += amount

    def dec(self, amount: float = 1):
        """减少"""
        self.value -= amount

    def get(self) -> float:
        """获取当前值"""
        return self.value


class Histogram:
    """直方图指标（用于统计分布）"""

    def __init__(self, name: str, description: str = "", buckets: List[float] = None):
        """
        初始化直方图

        Args:
            name: 指标名称
            description: 指标描述
            buckets: 桶边界
        """
        self.name = name
        self.description = description
        self.buckets = buckets or [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        self.observations = []
        self.sum = 0
        self.count = 0

    def observe(self, value: float):
        """记录观测值"""
        self.observations.append(value)
        self.sum += value
        self.count += 1

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.observations:
            return {
                "count": 0,
                "sum": 0,
                "avg": 0,
                "min": 0,
                "max": 0,
                "p50": 0,
                "p95": 0,
                "p99": 0
            }

        sorted_obs = sorted(self.observations)
        count = len(sorted_obs)

        return {
            "count": count,
            "sum": self.sum,
            "avg": self.sum / count,
            "min": sorted_obs[0],
            "max": sorted_obs[-1],
            "p50": sorted_obs[int(count * 0.5)],
            "p95": sorted_obs[int(count * 0.95)] if count > 1 else sorted_obs[0],
            "p99": sorted_obs[int(count * 0.99)] if count > 1 else sorted_obs[0]
        }


class MetricsCollector:
    """
    指标收集器

    收集和管理所有系统指标。
    """

    def __init__(self):
        """初始化收集器"""
        # 指标存储
        self.counters: Dict[str, Counter] = {}
        self.gauges: Dict[str, Gauge] = {}
        self.histograms: Dict[str, Histogram] = {}

        # 时间序列数据（最近1小时）
        self.timeseries: Dict[str, deque] = defaultdict(lambda: deque(maxlen=3600))

        # 初始化基础指标
        self._init_metrics()

    def _init_metrics(self):
        """初始化基础指标"""
        # 任务指标
        self.counters["tasks_total"] = Counter("tasks_total", "总任务数")
        self.counters["tasks_success"] = Counter("tasks_success", "成功任务数")
        self.counters["tasks_failed"] = Counter("tasks_failed", "失败任务数")

        # LLM指标
        self.counters["llm_calls_total"] = Counter("llm_calls_total", "LLM调用总数")
        self.counters["llm_calls_failed"] = Counter("llm_calls_failed", "LLM调用失败数")
        self.counters["llm_tokens_total"] = Counter("llm_tokens_total", "LLM Token总数")

        # 执行时间
        self.histograms["task_duration_seconds"] = Histogram("task_duration_seconds", "任务执行时间")
        self.histograms["llm_response_time_seconds"] = Histogram("llm_response_time_seconds", "LLM响应时间")

        # 并发指标
        self.gauges["tasks_running"] = Gauge("tasks_running", "运行中的任务数")
        self.gauges["tasks_queued"] = Gauge("tasks_queued", "队列中的任务数")

    def get_counter(self, name: str) -> Counter:
        """获取计数器"""
        if name not in self.counters:
            self.counters[name] = Counter(name)
        return self.counters[name]

    def get_gauge(self, name: str) -> Gauge:
        """获取仪表盘"""
        if name not in self.gauges:
            self.gauges[name] = Gauge(name)
        return self.gauges[name]

    def get_histogram(self, name: str) -> Histogram:
        """获取直方图"""
        if name not in self.histograms:
            self.histograms[name] = Histogram(name)
        return self.histograms[name]

    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """
        记录指标

        Args:
            name: 指标名称
            value: 指标值
            labels: 标签
        """
        point = MetricPoint(name, value, labels)
        self.timeseries[name].append(point)

    def collect_system_metrics(self) -> Dict[str, Any]:
        """
        收集系统指标

        Returns:
            dict: 系统指标
        """
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_used_mb": psutil.virtual_memory().used / (1024 * 1024),
            "memory_available_mb": psutil.virtual_memory().available / (1024 * 1024),
            "disk_percent": psutil.disk_usage('/').percent,
            "disk_used_gb": psutil.disk_usage('/').used / (1024 * 1024 * 1024),
            "disk_free_gb": psutil.disk_usage('/').free / (1024 * 1024 * 1024)
        }

    def get_business_metrics(self) -> Dict[str, Any]:
        """
        获取业务指标

        Returns:
            dict: 业务指标
        """
        tasks_total = self.counters["tasks_total"].get()
        tasks_success = self.counters["tasks_success"].get()
        tasks_failed = self.counters["tasks_failed"].get()

        success_rate = (tasks_success / tasks_total * 100) if tasks_total > 0 else 0

        task_duration_stats = self.histograms["task_duration_seconds"].get_stats()

        return {
            "tasks_total": tasks_total,
            "tasks_success": tasks_success,
            "tasks_failed": tasks_failed,
            "success_rate": round(success_rate, 2),
            "tasks_running": self.gauges["tasks_running"].get(),
            "tasks_queued": self.gauges["tasks_queued"].get(),
            "avg_task_duration": round(task_duration_stats["avg"], 2),
            "p95_task_duration": round(task_duration_stats["p95"], 2)
        }

    def get_llm_metrics(self) -> Dict[str, Any]:
        """
        获取LLM指标

        Returns:
            dict: LLM指标
        """
        llm_calls_total = self.counters["llm_calls_total"].get()
        llm_calls_failed = self.counters["llm_calls_failed"].get()

        error_rate = (llm_calls_failed / llm_calls_total * 100) if llm_calls_total > 0 else 0

        llm_response_stats = self.histograms["llm_response_time_seconds"].get_stats()

        return {
            "llm_calls_total": llm_calls_total,
            "llm_calls_failed": llm_calls_failed,
            "llm_error_rate": round(error_rate, 2),
            "llm_tokens_total": self.counters["llm_tokens_total"].get(),
            "avg_llm_response_time": round(llm_response_stats["avg"], 2),
            "p95_llm_response_time": round(llm_response_stats["p95"], 2)
        }

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        获取所有指标

        Returns:
            dict: 所有指标
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": self.collect_system_metrics(),
            "business": self.get_business_metrics(),
            "llm": self.get_llm_metrics()
        }

    def reset_metrics(self):
        """重置所有指标"""
        for counter in self.counters.values():
            counter.reset()

        for gauge in self.gauges.values():
            gauge.set(0)

        for histogram in self.histograms.values():
            histogram.observations.clear()
            histogram.sum = 0
            histogram.count = 0


# 全局指标收集器实例
metrics_collector = MetricsCollector()
