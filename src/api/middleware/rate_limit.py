"""
Rate Limiting中间件

FastAPI中间件，自动对所有API请求进行速率限制。
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

from ..security.rate_limiter import rate_limit_manager, RateLimitExceeded
from ..database.organization_repository import OrganizationMemberRepository
from ..database.database import Database


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件

    对所有API请求进行速率限制检查。
    """

    def __init__(self, app, db: Database):
        """
        初始化中间件

        Args:
            app: FastAPI应用
            db: 数据库实例
        """
        super().__init__(app)
        self.db = db

        # 不需要限流的路径
        self.excluded_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
            "/auth/register"
        ]

    async def dispatch(self, request: Request, call_next: Callable):
        """
        处理请求

        Args:
            request: 请求对象
            call_next: 下一个处理函数

        Returns:
            响应对象
        """
        # 检查是否需要限流
        if self._should_skip(request):
            return await call_next(request)

        # 获取组织ID
        organization_id = await self._get_organization_id(request)

        if not organization_id:
            # 没有组织ID，跳过限流
            return await call_next(request)

        # 检查速率限制
        try:
            rate_limit_manager.check_combined_limit(
                organization_id=organization_id,
                api_path=request.url.path
            )

        except RateLimitExceeded as e:
            # 返回429错误
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "速率限制超出",
                    "detail": str(e),
                    "limit": e.limit,
                    "window": e.window,
                    "retry_after": e.retry_after
                },
                headers={
                    "Retry-After": str(e.retry_after),
                    "X-RateLimit-Limit": str(e.limit),
                    "X-RateLimit-Window": str(e.window)
                }
            )

        # 继续处理请求
        response = await call_next(request)

        # 添加速率限制响应头
        if organization_id:
            stats = rate_limit_manager.get_organization_stats(organization_id)
            response.headers["X-RateLimit-Limit"] = str(stats["max_requests"])
            response.headers["X-RateLimit-Remaining"] = str(stats["remaining"])
            response.headers["X-RateLimit-Reset"] = str(stats["retry_after"])

        return response

    def _should_skip(self, request: Request) -> bool:
        """
        判断是否应该跳过限流

        Args:
            request: 请求对象

        Returns:
            bool: 是否跳过
        """
        # 检查路径是否在排除列表中
        for path in self.excluded_paths:
            if request.url.path.startswith(path):
                return True

        return False

    async def _get_organization_id(self, request: Request) -> int:
        """
        从请求中获取组织ID

        Args:
            request: 请求对象

        Returns:
            int: 组织ID，如果无法获取则返回None
        """
        # 尝试从查询参数获取
        org_id = request.query_params.get("organization_id")
        if org_id:
            try:
                return int(org_id)
            except ValueError:
                pass

        # 尝试从请求体获取（如果是POST/PUT请求）
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
                if isinstance(body, dict) and "organization_id" in body:
                    return int(body["organization_id"])
            except Exception:
                pass

        # 尝试从用户的默认组织获取
        # TODO: 从JWT token中获取用户ID，然后查询用户的默认组织
        # 这里暂时返回None

        return None
