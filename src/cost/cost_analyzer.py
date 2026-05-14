"""
成本统计和分析

实现多维度的成本统计和分析。

统计维度：
1. 组织级别：每个组织的总消耗
2. 项目级别：每个项目的总消耗
3. 任务级别：每个任务的详细消耗
4. Agent级别：每个Agent的平均消耗
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class CostRecord:
    """成本记录"""
    organization_id: int
    project_id: Optional[int]
    task_id: Optional[int]
    agent_name: Optional[str]
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    timestamp: datetime


class CostAnalyzer:
    """成本分析器"""

    # 模型价格（每1000 tokens的价格，单位：美元）
    MODEL_PRICES = {
        "claude-opus-4": {"input": 0.015, "output": 0.075},
        "claude-sonnet-4": {"input": 0.003, "output": 0.015},
        "claude-haiku-4": {"input": 0.00025, "output": 0.00125},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        "ollama": {"input": 0.0, "output": 0.0},  # 本地模型免费
    }

    def __init__(self):
        """初始化成本分析器"""
        self.records: List[CostRecord] = []

    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        计算成本

        Args:
            model: 模型名称
            input_tokens: 输入Token数
            output_tokens: 输出Token数

        Returns:
            float: 成本（美元）
        """
        # 获取模型价格
        prices = self.MODEL_PRICES.get(model)
        if not prices:
            # 未知模型，使用默认价格（GPT-4）
            prices = self.MODEL_PRICES["gpt-4"]

        # 计算成本
        input_cost = (input_tokens / 1000) * prices["input"]
        output_cost = (output_tokens / 1000) * prices["output"]

        return input_cost + output_cost

    def record_usage(
        self,
        organization_id: int,
        model: str,
        input_tokens: int,
        output_tokens: int,
        project_id: Optional[int] = None,
        task_id: Optional[int] = None,
        agent_name: Optional[str] = None
    ):
        """
        记录使用情况

        Args:
            organization_id: 组织ID
            model: 模型名称
            input_tokens: 输入Token数
            output_tokens: 输出Token数
            project_id: 项目ID
            task_id: 任务ID
            agent_name: Agent名称
        """
        total_tokens = input_tokens + output_tokens
        cost_usd = self.calculate_cost(model, input_tokens, output_tokens)

        record = CostRecord(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
            agent_name=agent_name,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            timestamp=datetime.utcnow()
        )

        self.records.append(record)

    def get_organization_cost(
        self,
        organization_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取组织成本统计

        Args:
            organization_id: 组织ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            dict: 成本统计
        """
        # 过滤记录
        records = self._filter_records(
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date
        )

        if not records:
            return {
                "organization_id": organization_id,
                "total_cost": 0.0,
                "total_tokens": 0,
                "record_count": 0
            }

        # 统计
        total_cost = sum(r.cost_usd for r in records)
        total_tokens = sum(r.total_tokens for r in records)

        # 按模型统计
        by_model = defaultdict(lambda: {"tokens": 0, "cost": 0.0, "count": 0})
        for r in records:
            by_model[r.model]["tokens"] += r.total_tokens
            by_model[r.model]["cost"] += r.cost_usd
            by_model[r.model]["count"] += 1

        return {
            "organization_id": organization_id,
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "record_count": len(records),
            "by_model": dict(by_model),
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            }
        }

    def get_project_cost(
        self,
        project_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取项目成本统计

        Args:
            project_id: 项目ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            dict: 成本统计
        """
        records = self._filter_records(
            project_id=project_id,
            start_date=start_date,
            end_date=end_date
        )

        if not records:
            return {
                "project_id": project_id,
                "total_cost": 0.0,
                "total_tokens": 0,
                "record_count": 0
            }

        total_cost = sum(r.cost_usd for r in records)
        total_tokens = sum(r.total_tokens for r in records)

        # 按Agent统计
        by_agent = defaultdict(lambda: {"tokens": 0, "cost": 0.0, "count": 0})
        for r in records:
            if r.agent_name:
                by_agent[r.agent_name]["tokens"] += r.total_tokens
                by_agent[r.agent_name]["cost"] += r.cost_usd
                by_agent[r.agent_name]["count"] += 1

        return {
            "project_id": project_id,
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "record_count": len(records),
            "by_agent": dict(by_agent),
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            }
        }

    def get_task_cost(self, task_id: int) -> Dict[str, Any]:
        """
        获取任务成本统计

        Args:
            task_id: 任务ID

        Returns:
            dict: 成本统计
        """
        records = self._filter_records(task_id=task_id)

        if not records:
            return {
                "task_id": task_id,
                "total_cost": 0.0,
                "total_tokens": 0,
                "record_count": 0
            }

        total_cost = sum(r.cost_usd for r in records)
        total_tokens = sum(r.total_tokens for r in records)

        # 按Agent详细统计
        agent_details = []
        by_agent = defaultdict(list)
        for r in records:
            if r.agent_name:
                by_agent[r.agent_name].append(r)

        for agent_name, agent_records in by_agent.items():
            agent_cost = sum(r.cost_usd for r in agent_records)
            agent_tokens = sum(r.total_tokens for r in agent_records)

            agent_details.append({
                "agent_name": agent_name,
                "cost": round(agent_cost, 4),
                "tokens": agent_tokens,
                "calls": len(agent_records)
            })

        return {
            "task_id": task_id,
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "record_count": len(records),
            "agent_details": agent_details
        }

    def get_agent_average_cost(
        self,
        agent_name: str,
        organization_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取Agent平均成本

        Args:
            agent_name: Agent名称
            organization_id: 组织ID（可选）

        Returns:
            dict: 平均成本统计
        """
        records = [
            r for r in self.records
            if r.agent_name == agent_name
            and (organization_id is None or r.organization_id == organization_id)
        ]

        if not records:
            return {
                "agent_name": agent_name,
                "average_cost": 0.0,
                "average_tokens": 0,
                "total_calls": 0
            }

        total_cost = sum(r.cost_usd for r in records)
        total_tokens = sum(r.total_tokens for r in records)
        call_count = len(records)

        return {
            "agent_name": agent_name,
            "average_cost": round(total_cost / call_count, 4),
            "average_tokens": total_tokens // call_count,
            "total_calls": call_count,
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens
        }

    def get_cost_trend(
        self,
        organization_id: int,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        获取成本趋势

        Args:
            organization_id: 组织ID
            days: 天数

        Returns:
            List[dict]: 每日成本统计
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        records = self._filter_records(
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date
        )

        # 按日期分组
        by_date = defaultdict(lambda: {"cost": 0.0, "tokens": 0, "count": 0})

        for r in records:
            date_key = r.timestamp.date().isoformat()
            by_date[date_key]["cost"] += r.cost_usd
            by_date[date_key]["tokens"] += r.total_tokens
            by_date[date_key]["count"] += 1

        # 转换为列表
        trend = []
        for i in range(days):
            date = (start_date + timedelta(days=i)).date()
            date_key = date.isoformat()

            trend.append({
                "date": date_key,
                "cost": round(by_date[date_key]["cost"], 4),
                "tokens": by_date[date_key]["tokens"],
                "count": by_date[date_key]["count"]
            })

        return trend

    def _filter_records(
        self,
        organization_id: Optional[int] = None,
        project_id: Optional[int] = None,
        task_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CostRecord]:
        """
        过滤记录

        Args:
            organization_id: 组织ID
            project_id: 项目ID
            task_id: 任务ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            List[CostRecord]: 过滤后的记录
        """
        filtered = self.records

        if organization_id is not None:
            filtered = [r for r in filtered if r.organization_id == organization_id]

        if project_id is not None:
            filtered = [r for r in filtered if r.project_id == project_id]

        if task_id is not None:
            filtered = [r for r in filtered if r.task_id == task_id]

        if start_date is not None:
            filtered = [r for r in filtered if r.timestamp >= start_date]

        if end_date is not None:
            filtered = [r for r in filtered if r.timestamp <= end_date]

        return filtered


# 全局成本分析器实例
cost_analyzer = CostAnalyzer()
