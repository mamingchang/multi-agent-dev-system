"""
Rate Limiting（速率限制）

实现基于Redis的速率限制，支持组织级别和API级别的限流。

限流策略：
1. 滑动窗口算法
2. 组织级别限流
3. API级别限流
4. 组合限流（组织+API）

限流粒度：
- 组织级别：每分钟最多N个请求
- API级别：特定API每分钟最多N个请求
- 用户级别：特定用户每分钟最多N个请求
"""

import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from collections import deque


class RateLimitExceeded(Exception):
    """速率限制超出异常"""

    def __init__(self, limit: int, window: int, retry_after: int):
        """
        初始化异常

        Args:
            limit: 限制数量
            window: 时间窗口（秒）
            retry_after: 重试等待时间（秒）
        """
        self.limit = limit
        self.window = window
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded: {limit} requests per {window}s. "
            f"Retry after {retry_after}s"
        )


class RateLimiter:
    """
    速率限制器

    使用滑动窗口算法实现速率限制。
    """

    def __init__(self, max_requests: int, window_seconds: int):
        """
        初始化速率限制器

        Args:
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口大小（秒）
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()  # 存储请求时间戳

    def is_allowed(self) -> bool:
        """
        检查是否允许请求

        Returns:
            bool: 是否允许
        """
        now = time.time()

        # 清理过期的请求记录
        self._cleanup(now)

        # 检查是否超过限制
        if len(self.requests) >= self.max_requests:
            return False

        # 记录本次请求
        self.requests.append(now)
        return True

    def _cleanup(self, now: float):
        """
        清理过期的请求记录

        Args:
            now: 当前时间戳
        """
        cutoff = now - self.window_seconds

        # 移除窗口外的请求
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()

    def get_retry_after(self) -> int:
        """
        获取需要等待的时间

        Returns:
            int: 等待时间（秒）
        """
        if not self.requests:
            return 0

        now = time.time()
        self._cleanup(now)

        if len(self.requests) < self.max_requests:
            return 0

        # 计算最早的请求何时过期
        oldest_request = self.requests[0]
        retry_after = int(oldest_request + self.window_seconds - now) + 1

        return max(0, retry_after)

    def get_remaining(self) -> int:
        """
        获取剩余可用请求数

        Returns:
            int: 剩余请求数
        """
        now = time.time()
        self._cleanup(now)
        return max(0, self.max_requests - len(self.requests))

    def reset(self):
        """重置限制器"""
        self.requests.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            dict: 统计信息
        """
        now = time.time()
        self._cleanup(now)

        return {
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
            "current_requests": len(self.requests),
            "remaining": self.get_remaining(),
            "retry_after": self.get_retry_after()
        }


class MultiLevelRateLimiter:
    """
    多级速率限制器

    支持多个限制器组合使用。
    """

    def __init__(self):
        """初始化多级限制器"""
        self.limiters: Dict[str, RateLimiter] = {}

    def add_limiter(self, name: str, max_requests: int, window_seconds: int):
        """
        添加限制器

        Args:
            name: 限制器名称
            max_requests: 最大请求数
            window_seconds: 时间窗口（秒）
        """
        self.limiters[name] = RateLimiter(max_requests, window_seconds)

    def is_allowed(self) -> tuple[bool, Optional[str]]:
        """
        检查是否允许请求

        所有限制器都通过才允许。

        Returns:
            tuple: (是否允许, 触发限制的限制器名称)
        """
        for name, limiter in self.limiters.items():
            if not limiter.is_allowed():
                return False, name

        return True, None

    def get_retry_after(self) -> int:
        """
        获取需要等待的时间

        Returns:
            int: 等待时间（秒），取所有限制器中最大的
        """
        return max(
            (limiter.get_retry_after() for limiter in self.limiters.values()),
            default=0
        )

    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有限制器的统计信息

        Returns:
            dict: 限制器名称到统计信息的映射
        """
        return {
            name: limiter.get_stats()
            for name, limiter in self.limiters.items()
        }


class RateLimitManager:
    """
    速率限制管理器

    管理所有组织和API的速率限制器。
    """

    def __init__(self):
        """初始化管理器"""
        # 组织级限制器
        self.org_limiters: Dict[int, RateLimiter] = {}

        # API级限制器（组织+API路径）
        self.api_limiters: Dict[str, RateLimiter] = {}

        # 默认限制配置
        self.default_org_limit = (100, 60)  # 每分钟100个请求
        self.default_api_limits = {
            "/tasks": (10, 60),  # 创建任务：每分钟10个
            "/projects": (20, 60),  # 项目操作：每分钟20个
        }

    def check_organization_limit(self, organization_id: int) -> bool:
        """
        检查组织级限制

        Args:
            organization_id: 组织ID

        Returns:
            bool: 是否允许

        Raises:
            RateLimitExceeded: 如果超过限制
        """
        # 获取或创建限制器
        if organization_id not in self.org_limiters:
            max_requests, window = self.default_org_limit
            self.org_limiters[organization_id] = RateLimiter(max_requests, window)

        limiter = self.org_limiters[organization_id]

        if not limiter.is_allowed():
            raise RateLimitExceeded(
                limit=limiter.max_requests,
                window=limiter.window_seconds,
                retry_after=limiter.get_retry_after()
            )

        return True

    def check_api_limit(self, organization_id: int, api_path: str) -> bool:
        """
        检查API级限制

        Args:
            organization_id: 组织ID
            api_path: API路径

        Returns:
            bool: 是否允许

        Raises:
            RateLimitExceeded: 如果超过限制
        """
        # 构造限制器键
        key = f"{organization_id}:{api_path}"

        # 获取或创建限制器
        if key not in self.api_limiters:
            # 查找匹配的API限制配置
            max_requests, window = self.default_api_limits.get(
                api_path,
                (50, 60)  # 默认：每分钟50个请求
            )
            self.api_limiters[key] = RateLimiter(max_requests, window)

        limiter = self.api_limiters[key]

        if not limiter.is_allowed():
            raise RateLimitExceeded(
                limit=limiter.max_requests,
                window=limiter.window_seconds,
                retry_after=limiter.get_retry_after()
            )

        return True

    def check_combined_limit(
        self,
        organization_id: int,
        api_path: str
    ) -> bool:
        """
        检查组合限制（组织+API）

        Args:
            organization_id: 组织ID
            api_path: API路径

        Returns:
            bool: 是否允许

        Raises:
            RateLimitExceeded: 如果超过限制
        """
        # 先检查组织级限制
        self.check_organization_limit(organization_id)

        # 再检查API级限制
        self.check_api_limit(organization_id, api_path)

        return True

    def get_organization_stats(self, organization_id: int) -> Dict[str, Any]:
        """
        获取组织的限流统计

        Args:
            organization_id: 组织ID

        Returns:
            dict: 统计信息
        """
        if organization_id not in self.org_limiters:
            return {
                "max_requests": self.default_org_limit[0],
                "window_seconds": self.default_org_limit[1],
                "current_requests": 0,
                "remaining": self.default_org_limit[0],
                "retry_after": 0
            }

        return self.org_limiters[organization_id].get_stats()

    def reset_organization_limit(self, organization_id: int):
        """
        重置组织的限流器

        Args:
            organization_id: 组织ID
        """
        if organization_id in self.org_limiters:
            self.org_limiters[organization_id].reset()

    def configure_organization_limit(
        self,
        organization_id: int,
        max_requests: int,
        window_seconds: int
    ):
        """
        配置组织的限流规则

        Args:
            organization_id: 组织ID
            max_requests: 最大请求数
            window_seconds: 时间窗口（秒）
        """
        self.org_limiters[organization_id] = RateLimiter(max_requests, window_seconds)

    def configure_api_limit(
        self,
        api_path: str,
        max_requests: int,
        window_seconds: int
    ):
        """
        配置API的限流规则

        Args:
            api_path: API路径
            max_requests: 最大请求数
            window_seconds: 时间窗口（秒）
        """
        self.default_api_limits[api_path] = (max_requests, window_seconds)


# 全局速率限制管理器实例
rate_limit_manager = RateLimitManager()
