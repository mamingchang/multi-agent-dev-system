"""
熔断器 - 标准化接口

从distributed_lock模块导出
"""

from src.concurrency.distributed_lock import CircuitBreaker

__all__ = ['CircuitBreaker']
