"""
熔断器（Circuit Breaker）

实现组织级熔断机制，防止故障扩散。

熔断器状态：
- CLOSED（关闭）: 正常状态，允许请求通过
- OPEN（打开）: 熔断状态，拒绝所有请求
- HALF_OPEN（半开）: 尝试恢复，允许少量请求测试

熔断触发条件：
1. 最近10个任务中有5个失败
2. 1小时内失败任务数>20个
3. Token配额耗尽

熔断恢复：
- 自动恢复：条件改善后自动恢复
- 手动恢复：管理员手动恢复
"""

import time
from enum import Enum
from typing import Optional, Dict
from datetime import datetime, timedelta
from collections import deque

from ..exceptions import CircuitOpenException


class CircuitState(str, Enum):
    """熔断器状态"""
    CLOSED = "closed"  # 关闭（正常）
    OPEN = "open"  # 打开（熔断）
    HALF_OPEN = "half_open"  # 半开（测试恢复）


class CircuitBreaker:
    """
    熔断器

    用于组织级别的熔断控制。
    """

    def __init__(
        self,
        organization_id: int,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: int = 60,
        window_size: int = 10
    ):
        """
        初始化熔断器

        Args:
            organization_id: 组织ID
            failure_threshold: 失败阈值（触发熔断的失败次数）
            success_threshold: 成功阈值（半开状态下恢复需要的成功次数）
            timeout: 熔断超时时间（秒），超时后进入半开状态
            window_size: 滑动窗口大小（记录最近N次请求）
        """
        self.organization_id = organization_id
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.window_size = window_size

        # 状态
        self.state = CircuitState.CLOSED
        self.last_failure_time: Optional[float] = None
        self.last_state_change_time = time.time()

        # 统计
        self.recent_results = deque(maxlen=window_size)  # 最近的请求结果
        self.failure_count = 0  # 当前窗口内的失败次数
        self.success_count = 0  # 半开状态下的成功次数

        # 熔断原因
        self.open_reason: Optional[str] = None

    def call(self, func, *args, **kwargs):
        """
        通过熔断器调用函数

        Args:
            func: 要调用的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            函数返回值

        Raises:
            CircuitOpenException: 如果熔断器处于打开状态
        """
        # 检查熔断器状态
        if self.state == CircuitState.OPEN:
            # 检查是否可以进入半开状态
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                # 仍然处于熔断状态，拒绝请求
                retry_after = int(self.timeout - (time.time() - self.last_state_change_time))
                raise CircuitOpenException(
                    organization_id=self.organization_id,
                    reason=self.open_reason or "熔断器打开",
                    retry_after=max(0, retry_after)
                )

        # 执行函数
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure(e)
            raise

    def _on_success(self):
        """处理成功的请求"""
        self.recent_results.append(True)

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            # 半开状态下，连续成功达到阈值则关闭熔断器
            if self.success_count >= self.success_threshold:
                self._transition_to_closed()
        elif self.state == CircuitState.CLOSED:
            # 关闭状态下，成功请求减少失败计数
            if self.failure_count > 0:
                self.failure_count -= 1

    def _on_failure(self, exception: Exception):
        """处理失败的请求"""
        self.recent_results.append(False)
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            # 半开状态下，任何失败都重新打开熔断器
            self._transition_to_open(f"半开状态测试失败: {str(exception)}")
        elif self.state == CircuitState.CLOSED:
            # 关闭状态下，累计失败次数
            self.failure_count += 1

            # 检查是否达到熔断阈值
            if self._should_trip():
                self._transition_to_open(f"失败率过高: {self.failure_count}/{self.window_size}")

    def _should_trip(self) -> bool:
        """
        判断是否应该触发熔断

        Returns:
            bool: 是否应该熔断
        """
        # 条件1: 最近N个请求中失败次数超过阈值
        if self.failure_count >= self.failure_threshold:
            return True

        # 条件2: 可以添加其他熔断条件（如时间窗口内的失败率）
        # 这里暂时只实现条件1

        return False

    def _should_attempt_reset(self) -> bool:
        """
        判断是否应该尝试恢复（进入半开状态）

        Returns:
            bool: 是否应该尝试恢复
        """
        if self.state != CircuitState.OPEN:
            return False

        # 检查是否超过超时时间
        elapsed = time.time() - self.last_state_change_time
        return elapsed >= self.timeout

    def _transition_to_open(self, reason: str):
        """
        转换到打开状态

        Args:
            reason: 熔断原因
        """
        self.state = CircuitState.OPEN
        self.open_reason = reason
        self.last_state_change_time = time.time()
        print(f"熔断器打开 [组织 {self.organization_id}]: {reason}")

    def _transition_to_half_open(self):
        """转换到半开状态"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.last_state_change_time = time.time()
        print(f"熔断器进入半开状态 [组织 {self.organization_id}]")

    def _transition_to_closed(self):
        """转换到关闭状态"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.open_reason = None
        self.last_state_change_time = time.time()
        print(f"熔断器关闭 [组织 {self.organization_id}]")

    def reset(self):
        """手动重置熔断器（管理员操作）"""
        self._transition_to_closed()
        self.recent_results.clear()
        print(f"熔断器手动重置 [组织 {self.organization_id}]")

    def get_state(self) -> Dict:
        """
        获取熔断器状态

        Returns:
            dict: 状态信息
        """
        return {
            "organization_id": self.organization_id,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "open_reason": self.open_reason,
            "last_failure_time": self.last_failure_time,
            "last_state_change_time": self.last_state_change_time,
            "recent_results": list(self.recent_results)
        }


class CircuitBreakerManager:
    """
    熔断器管理器

    管理所有组织的熔断器实例。
    """

    def __init__(self):
        """初始化熔断器管理器"""
        self._breakers: Dict[int, CircuitBreaker] = {}

    def get_breaker(self, organization_id: int) -> CircuitBreaker:
        """
        获取组织的熔断器

        如果不存在则创建新的熔断器。

        Args:
            organization_id: 组织ID

        Returns:
            CircuitBreaker: 熔断器实例
        """
        if organization_id not in self._breakers:
            self._breakers[organization_id] = CircuitBreaker(organization_id)

        return self._breakers[organization_id]

    def reset_breaker(self, organization_id: int):
        """
        重置组织的熔断器

        Args:
            organization_id: 组织ID
        """
        if organization_id in self._breakers:
            self._breakers[organization_id].reset()

    def get_all_states(self) -> Dict[int, Dict]:
        """
        获取所有熔断器的状态

        Returns:
            dict: 组织ID到状态的映射
        """
        return {
            org_id: breaker.get_state()
            for org_id, breaker in self._breakers.items()
        }


# 全局熔断器管理器实例
circuit_breaker_manager = CircuitBreakerManager()
