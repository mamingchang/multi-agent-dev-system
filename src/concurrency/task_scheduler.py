"""
任务调度器

实现优先级队列和公平调度策略。

调度策略：
1. 优先级队列：按任务优先级排序
2. 公平调度：同优先级下按组织轮询
3. 并发控制：限制每个组织的并发任务数
"""

import heapq
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import defaultdict, deque

from ..database.models import Task, TaskStatus


class TaskQueueItem:
    """任务队列项"""

    def __init__(
        self,
        task_id: str,
        organization_id: int,
        priority: int,
        created_at: datetime
    ):
        """
        初始化队列项

        Args:
            task_id: 任务ID
            organization_id: 组织ID
            priority: 优先级（0-100）
            created_at: 创建时间
        """
        self.task_id = task_id
        self.organization_id = organization_id
        self.priority = priority
        self.created_at = created_at

    def __lt__(self, other):
        """
        比较运算符（用于优先级队列）

        优先级高的排在前面，优先级相同则按创建时间排序。
        """
        if self.priority != other.priority:
            # 优先级高的排在前面（数值大的优先）
            return self.priority > other.priority
        # 优先级相同，创建时间早的排在前面
        return self.created_at < other.created_at

    def __repr__(self):
        return f"<TaskQueueItem(task_id={self.task_id}, priority={self.priority})>"


class TaskScheduler:
    """
    任务调度器

    管理任务队列和调度策略。
    """

    def __init__(self):
        """初始化调度器"""
        # 优先级队列（最小堆）
        self.queue: List[TaskQueueItem] = []

        # 组织的运行中任务数
        self.running_tasks: Dict[int, int] = defaultdict(int)

        # 组织的并发限制
        self.org_limits: Dict[int, int] = {}

        # 组织的最后调度时间（用于公平调度）
        self.last_scheduled: Dict[int, datetime] = {}

    def add_task(
        self,
        task_id: str,
        organization_id: int,
        priority: int = 50,
        created_at: Optional[datetime] = None
    ):
        """
        添加任务到队列

        Args:
            task_id: 任务ID
            organization_id: 组织ID
            priority: 优先级（0-100），默认50
            created_at: 创建时间
        """
        if created_at is None:
            created_at = datetime.utcnow()

        item = TaskQueueItem(
            task_id=task_id,
            organization_id=organization_id,
            priority=priority,
            created_at=created_at
        )

        heapq.heappush(self.queue, item)
        print(f"任务已加入队列: {task_id}, 优先级: {priority}")

    def get_next_task(self) -> Optional[str]:
        """
        获取下一个要执行的任务

        考虑优先级、并发限制和公平调度。

        Returns:
            Optional[str]: 任务ID，如果没有可执行的任务则返回None
        """
        if not self.queue:
            return None

        # 临时存储跳过的任务
        skipped = []

        while self.queue:
            item = heapq.heappop(self.queue)

            # 检查组织的并发限制
            org_id = item.organization_id
            limit = self.org_limits.get(org_id, 3)  # 默认限制3个并发

            if self.running_tasks[org_id] >= limit:
                # 超过并发限制，跳过
                skipped.append(item)
                continue

            # 找到可执行的任务
            # 将跳过的任务放回队列
            for skipped_item in skipped:
                heapq.heappush(self.queue, skipped_item)

            # 更新运行中任务数
            self.running_tasks[org_id] += 1
            self.last_scheduled[org_id] = datetime.utcnow()

            print(f"调度任务: {item.task_id}, 组织: {org_id}, "
                  f"当前并发: {self.running_tasks[org_id]}/{limit}")

            return item.task_id

        # 所有任务都被跳过（都超过并发限制）
        # 将跳过的任务放回队列
        for skipped_item in skipped:
            heapq.heappush(self.queue, skipped_item)

        return None

    def complete_task(self, task_id: str, organization_id: int):
        """
        标记任务完成

        Args:
            task_id: 任务ID
            organization_id: 组织ID
        """
        if self.running_tasks[organization_id] > 0:
            self.running_tasks[organization_id] -= 1

        print(f"任务完成: {task_id}, 组织: {organization_id}, "
              f"剩余并发: {self.running_tasks[organization_id]}")

    def set_organization_limit(self, organization_id: int, limit: int):
        """
        设置组织的并发限制

        Args:
            organization_id: 组织ID
            limit: 并发限制
        """
        self.org_limits[organization_id] = limit
        print(f"组织 {organization_id} 并发限制设置为: {limit}")

    def get_queue_size(self) -> int:
        """
        获取队列大小

        Returns:
            int: 队列中的任务数
        """
        return len(self.queue)

    def get_organization_stats(self, organization_id: int) -> Dict:
        """
        获取组织的统计信息

        Args:
            organization_id: 组织ID

        Returns:
            dict: 统计信息
        """
        # 统计队列中该组织的任务数
        queued_count = sum(
            1 for item in self.queue
            if item.organization_id == organization_id
        )

        return {
            "organization_id": organization_id,
            "running_tasks": self.running_tasks[organization_id],
            "queued_tasks": queued_count,
            "concurrent_limit": self.org_limits.get(organization_id, 3),
            "last_scheduled": self.last_scheduled.get(organization_id)
        }

    def get_all_stats(self) -> Dict:
        """
        获取所有统计信息

        Returns:
            dict: 统计信息
        """
        # 按组织统计队列中的任务
        queued_by_org = defaultdict(int)
        for item in self.queue:
            queued_by_org[item.organization_id] += 1

        return {
            "total_queued": len(self.queue),
            "total_running": sum(self.running_tasks.values()),
            "by_organization": {
                org_id: {
                    "running": self.running_tasks[org_id],
                    "queued": queued_by_org[org_id],
                    "limit": self.org_limits.get(org_id, 3)
                }
                for org_id in set(list(self.running_tasks.keys()) + list(queued_by_org.keys()))
            }
        }


class FairScheduler(TaskScheduler):
    """
    公平调度器

    在优先级队列的基础上，增加公平调度策略。
    同优先级下，轮询各个组织的任务。
    """

    def get_next_task(self) -> Optional[str]:
        """
        获取下一个要执行的任务

        使用公平调度策略。

        Returns:
            Optional[str]: 任务ID
        """
        if not self.queue:
            return None

        # 按优先级分组
        priority_groups = defaultdict(list)
        for item in self.queue:
            priority_groups[item.priority].append(item)

        # 从最高优先级开始
        for priority in sorted(priority_groups.keys(), reverse=True):
            items = priority_groups[priority]

            # 按组织分组
            org_groups = defaultdict(list)
            for item in items:
                org_groups[item.organization_id].append(item)

            # 按最后调度时间排序组织（最久未调度的优先）
            sorted_orgs = sorted(
                org_groups.keys(),
                key=lambda org_id: self.last_scheduled.get(org_id, datetime.min)
            )

            # 轮询组织
            for org_id in sorted_orgs:
                # 检查并发限制
                limit = self.org_limits.get(org_id, 3)
                if self.running_tasks[org_id] >= limit:
                    continue

                # 获取该组织最早的任务
                org_items = sorted(org_groups[org_id], key=lambda x: x.created_at)
                selected_item = org_items[0]

                # 从队列中移除
                self.queue.remove(selected_item)
                heapq.heapify(self.queue)

                # 更新状态
                self.running_tasks[org_id] += 1
                self.last_scheduled[org_id] = datetime.utcnow()

                print(f"公平调度任务: {selected_item.task_id}, 组织: {org_id}, "
                      f"优先级: {priority}, 当前并发: {self.running_tasks[org_id]}/{limit}")

                return selected_item.task_id

        # 所有任务都被并发限制阻塞
        return None


# 全局任务调度器实例
task_scheduler = FairScheduler()
