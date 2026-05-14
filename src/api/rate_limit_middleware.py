"""
API限流中间件

基于Redis实现的分布式限流。
"""

from fastapi import Request, HTTPException, status
from typing import Callable, Optional
import time
import hashlib

# 简单的内存限流实现（生产环境应使用Redis）
_rate_limit_cache = {}


def get_rate_limit_key(
    identifier: str,
    endpoint: str,
    period: str
) -> str:
    """
    生成限流键

    Args:
        identifier: 标识符（用户ID或组织ID）
        endpoint: API端点
        period: 时间周期

    Returns:
        str: 限流键
    """
    key_str = f"{identifier}:{endpoint}:{period}"
    return hashlib.md5(key_str.encode()).hexdigest()


def check_rate_limit(
    identifier: str,
    endpoint: str,
    max_requests: int,
    period_seconds: int
) -> bool:
    """
    检查限流

    Args:
        identifier: 标识符
        endpoint: API端点
        max_requests: 最大请求数
        period_seconds: 时间周期（秒）

    Returns:
        bool: 是否允许请求

    Raises:
        HTTPException: 如果超过限流
    """
    current_time = int(time.time())
    period_key = current_time // period_seconds

    key = get_rate_limit_key(identifier, endpoint, str(period_key))

    # 获取当前计数
    if key not in _rate_limit_cache:
        _rate_limit_cache[key] = {
            'count': 0,
            'expires_at': (period_key + 1) * period_seconds
        }

    cache_entry = _rate_limit_cache[key]

    # 检查是否过期
    if current_time >= cache_entry['expires_at']:
        # 重置计数
        cache_entry['count'] = 0
        cache_entry['expires_at'] = (period_key + 1) * period_seconds

    # 检查限流
    if cache_entry['count'] >= max_requests:
        retry_after = cache_entry['expires_at'] - current_time
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"请求过于频繁，请在 {retry_after} 秒后重试",
            headers={"Retry-After": str(retry_after)}
        )

    # 增加计数
    cache_entry['count'] += 1

    return True


def cleanup_expired_cache():
    """清理过期的缓存"""
    current_time = int(time.time())
    expired_keys = [
        key for key, value in _rate_limit_cache.items()
        if current_time >= value['expires_at']
    ]

    for key in expired_keys:
        del _rate_limit_cache[key]


async def rate_limit_middleware(request: Request, call_next: Callable):
    """
    限流中间件

    Args:
        request: FastAPI请求对象
        call_next: 下一个中间件或路由处理器

    Returns:
        Response: 响应对象
    """
    # 清理过期缓存
    cleanup_expired_cache()

    # 获取用户信息
    user_id = None
    organization_id = None

    if hasattr(request.state, "user"):
        user = request.state.user
        user_id = user.id

    # 从请求中提取organization_id（如果有）
    # 这里简化处理，实际应该从路径参数或请求体中提取
    # organization_id = ...

    # 检查限流（这里使用简单的全局限流）
    if user_id:
        try:
            # 用户级限流：每分钟100个请求
            check_rate_limit(
                identifier=f"user:{user_id}",
                endpoint=request.url.path,
                max_requests=100,
                period_seconds=60
            )
        except HTTPException:
            raise

    # 处理请求
    response = await call_next(request)

    return response
