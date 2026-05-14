"""
进度预估器

基于历史数据预估任务完成时间。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


class ProgressEstimator:
    """进度预估器"""

    def __init__(self):
        """初始化预估器"""
        self.task_history: Dict[str, List[float]] = defaultdict(list)  # task_type -> [durations]
        self.agent_history: Dict[str, List[float]] = defaultdict(list)  # agent_name -> [durations]

    def record_task_duration(
        self,
        task_type: str,
        duration_hours: float,
        workflow: List[str]
    ):
        """
        记录任务耗时

        Args:
            task_type: 任务类型
            duration_hours: 耗时（小时）
            workflow: 工作流
        """
        self.task_history[task_type].append(duration_hours)

        # 记录每个Agent的平均耗时
        agent_duration = duration_hours / len(workflow) if workflow else 0
        for agent_name in workflow:
            self.agent_history[agent_name].append(agent_duration)

    def estimate_task_duration(
        self,
        task_type: str,
        workflow: List[str],
        task_description: str = ""
    ) -> Dict[str, Any]:
        """
        预估任务耗时

        Args:
            task_type: 任务类型
            workflow: 工作流
            task_description: 任务描述

        Returns:
            dict: 预估结果
        """
        # 基于历史平均值预估
        if task_type in self.task_history and self.task_history[task_type]:
            history = self.task_history[task_type]
            avg_duration = statistics.mean(history)
            std_dev = statistics.stdev(history) if len(history) > 1 else 0

            # 置信度：历史数据越多，置信度越高
            confidence = min(len(history) / 10, 0.9)

            # 预估范围
            min_duration = max(avg_duration - std_dev, avg_duration * 0.5)
            max_duration = avg_duration + std_dev

        else:
            # 没有历史数据，基于Agent预估
            agent_durations = []
            for agent_name in workflow:
                if agent_name in self.agent_history and self.agent_history[agent_name]:
                    agent_durations.append(statistics.mean(self.agent_history[agent_name]))
                else:
                    # 默认每个Agent 2小时
                    agent_durations.append(2.0)

            avg_duration = sum(agent_durations)
            min_duration = avg_duration * 0.7
            max_duration = avg_duration * 1.5
            confidence = 0.3

        # 根据任务描述长度调整
        if task_description:
            complexity_factor = min(len(task_description) / 500, 2.0)
            avg_duration *= complexity_factor
            min_duration *= complexity_factor
            max_duration *= complexity_factor

        return {
            "estimated_hours": round(avg_duration, 1),
            "min_hours": round(min_duration, 1),
            "max_hours": round(max_duration, 1),
            "confidence": round(confidence, 2),
            "confidence_level": self._get_confidence_level(confidence),
            "estimated_completion": self._calculate_completion_time(avg_duration)
        }

    def _get_confidence_level(self, confidence: float) -> str:
        """
        获取置信度级别

        Args:
            confidence: 置信度

        Returns:
            str: 置信度级别
        """
        if confidence >= 0.8:
            return "高"
        elif confidence >= 0.5:
            return "中"
        else:
            return "低"

    def _calculate_completion_time(self, hours: float) -> str:
        """
        计算预计完成时间

        Args:
            hours: 预估小时数

        Returns:
            str: 完成时间
        """
        # 假设每天工作8小时
        days = hours / 8
        completion_time = datetime.utcnow() + timedelta(days=days)
        return completion_time.isoformat()

    def update_estimate(
        self,
        task_id: int,
        current_progress: float,
        elapsed_hours: float,
        initial_estimate: float
    ) -> Dict[str, Any]:
        """
        动态更新预估

        在任务执行过程中，根据实际进度动态调整预估。

        Args:
            task_id: 任务ID
            current_progress: 当前进度（0-1）
            elapsed_hours: 已耗时（小时）
            initial_estimate: 初始预估（小时）

        Returns:
            dict: 更新后的预估
        """
        if current_progress <= 0:
            return {
                "estimated_remaining_hours": initial_estimate,
                "estimated_total_hours": initial_estimate,
                "confidence": 0.3
            }

        # 根据当前进度计算总耗时
        estimated_total = elapsed_hours / current_progress

        # 剩余耗时
        estimated_remaining = estimated_total - elapsed_hours

        # 置信度：进度越高，置信度越高
        confidence = min(current_progress + 0.3, 0.9)

        # 与初始预估对比
        deviation = abs(estimated_total - initial_estimate) / initial_estimate
        if deviation > 0.5:
            # 偏差较大，降低置信度
            confidence *= 0.7

        return {
            "estimated_remaining_hours": round(estimated_remaining, 1),
            "estimated_total_hours": round(estimated_total, 1),
            "elapsed_hours": round(elapsed_hours, 1),
            "current_progress": round(current_progress * 100, 1),
            "confidence": round(confidence, 2),
            "deviation_from_initial": f"{deviation * 100:.1f}%",
            "estimated_completion": self._calculate_completion_time(estimated_remaining)
        }

    def get_milestone_estimates(
        self,
        workflow: List[str],
        total_estimate: float
    ) -> List[Dict[str, Any]]:
        """
        获取里程碑预估

        将总预估分解到每个Agent。

        Args:
            workflow: 工作流
            total_estimate: 总预估（小时）

        Returns:
            List[dict]: 里程碑列表
        """
        milestones = []
        cumulative_hours = 0

        # 计算每个Agent的权重
        weights = []
        for agent_name in workflow:
            if agent_name in self.agent_history and self.agent_history[agent_name]:
                weight = statistics.mean(self.agent_history[agent_name])
            else:
                weight = 1.0
            weights.append(weight)

        total_weight = sum(weights)

        # 分配时间
        for i, agent_name in enumerate(workflow):
            agent_hours = (weights[i] / total_weight) * total_estimate
            cumulative_hours += agent_hours

            milestones.append({
                "agent": agent_name,
                "estimated_hours": round(agent_hours, 1),
                "cumulative_hours": round(cumulative_hours, 1),
                "progress_percentage": round((cumulative_hours / total_estimate) * 100, 1),
                "estimated_completion": self._calculate_completion_time(cumulative_hours)
            })

        return milestones


# 全局预估器实例
progress_estimator = ProgressEstimator()


# 初始化一些示例数据
progress_estimator.record_task_duration("feature", 20.0, ["ProductManager", "Architect", "Developer", "Tester"])
progress_estimator.record_task_duration("feature", 18.0, ["ProductManager", "Architect", "Developer", "Tester"])
progress_estimator.record_task_duration("feature", 22.0, ["ProductManager", "Architect", "Developer", "Tester"])
progress_estimator.record_task_duration("bugfix", 4.0, ["Developer", "Tester"])
progress_estimator.record_task_duration("bugfix", 3.5, ["Developer", "Tester"])
progress_estimator.record_task_duration("bugfix", 5.0, ["Developer", "Tester"])
