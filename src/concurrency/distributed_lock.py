"""
分布式锁 - 标准化接口

提供分布式锁功能
"""

import asyncio
from typing import Optional
from datetime import datetime, timedelta


class DistributedLock:
    """分布式锁实现"""

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self._locks = {}  # 内存锁（如果没有Redis）

    async def acquire(self, key: str, timeout: int = 30) -> bool:
        """获取锁"""
        if self.redis_client:
            # 使用Redis实现
            return await self._acquire_redis(key, timeout)
        else:
            # 使用内存实现
            return await self._acquire_memory(key, timeout)

    async def release(self, key: str) -> bool:
        """释放锁"""
        if self.redis_client:
            return await self._release_redis(key)
        else:
            return await self._release_memory(key)

    async def _acquire_redis(self, key: str, timeout: int) -> bool:
        """Redis锁获取"""
        try:
            result = await self.redis_client.set(
                f"lock:{key}",
                "1",
                ex=timeout,
                nx=True
            )
            return result is not None
        except Exception:
            return False

    async def _release_redis(self, key: str) -> bool:
        """Redis锁释放"""
        try:
            await self.redis_client.delete(f"lock:{key}")
            return True
        except Exception:
            return False

    async def _acquire_memory(self, key: str, timeout: int) -> bool:
        """内存锁获取"""
        now = datetime.now()

        if key in self._locks:
            lock_time, lock_timeout = self._locks[key]
            if now < lock_time + timedelta(seconds=lock_timeout):
                return False  # 锁仍然有效

        self._locks[key] = (now, timeout)
        return True

    async def _release_memory(self, key: str) -> bool:
        """内存锁释放"""
        if key in self._locks:
            del self._locks[key]
            return True
        return False


class CircuitBreaker:
    """熔断器实现"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = {}
        self.open_until = {}

    async def call(self, key: str, func, *args, **kwargs):
        """通过熔断器调用函数"""
        now = datetime.now()

        # 检查熔断器是否打开
        if key in self.open_until:
            if now < self.open_until[key]:
                raise Exception(f"Circuit breaker is open for {key}")
            else:
                # 超时后重置
                del self.open_until[key]
                self.failures[key] = 0

        try:
            result = await func(*args, **kwargs)
            # 成功，重置失败计数
            self.failures[key] = 0
            return result
        except Exception as e:
            # 失败，增加计数
            self.failures[key] = self.failures.get(key, 0) + 1

            if self.failures[key] >= self.failure_threshold:
                # 打开熔断器
                self.open_until[key] = now + timedelta(seconds=self.timeout)

            raise e


__all__ = ['DistributedLock', 'CircuitBreaker']
