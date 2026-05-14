"""
FastAPI主应用

集成所有路由，配置中间件和文档。

特性：
1. 自动生成OpenAPI文档
2. CORS支持
3. 异常处理
4. 请求日志
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import time

from .routes_auth import router as auth_router
from .routes_projects import router as projects_router
from .routes_workflow import router as workflow_router
from .routes_websocket import router as websocket_router
from .routes_celery import router as celery_router
from .routes_organizations import router as organizations_router
from .routes_audit import router as audit_router
from .routes_quota import router as quota_router
from .routes_notifications import router as notifications_router
from .routes_circuit_breaker import router as circuit_breaker_router
from .routes_concurrency import router as concurrency_router
from .routes_artifacts import router as artifacts_router
from .routes_monitoring import router as monitoring_router
from .routes_backup import router as backup_router
from .routes_cost import router as cost_router
from .routes_agents import router as agents_router
from .routes_ux import router as ux_router
from .routes_i18n import router as i18n_router
from .routes_collaboration import router as collaboration_router
from .routes_im import router as im_router
from .routes_import import router as import_router

# 创建FastAPI应用
app = FastAPI(
    title="Multi-Agent Dev System API",
    description="AI驱动的多Agent协作开发系统",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有HTTP请求"""
    start_time = time.time()

    # 处理请求
    response = await call_next(request)

    # 计算耗时
    process_time = time.time() - start_time

    # 打印日志
    print(f"[{request.method}] {request.url.path} - {response.status_code} - {process_time:.3f}s")

    return response


# 全局异常处理
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "请求参数验证失败",
            "detail": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理未捕获的异常"""
    print(f"未处理的异常: {str(exc)}")
    import traceback
    traceback.print_exc()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "服务器内部错误",
            "detail": str(exc)
        }
    )


# 注册路由
app.include_router(auth_router)
app.include_router(organizations_router)
app.include_router(projects_router)
app.include_router(workflow_router)
app.include_router(websocket_router)
app.include_router(celery_router)
app.include_router(audit_router)
app.include_router(quota_router)
app.include_router(notifications_router)
app.include_router(circuit_breaker_router)
app.include_router(concurrency_router)
app.include_router(artifacts_router)
app.include_router(monitoring_router)
app.include_router(backup_router)
app.include_router(cost_router)
app.include_router(agents_router)
app.include_router(ux_router)
app.include_router(i18n_router)
app.include_router(collaboration_router)
app.include_router(im_router)
app.include_router(import_router)


# 健康检查端点
@app.get("/health", tags=["系统"])
def health_check():
    """
    健康检查

    返回服务状态。
    """
    return {
        "status": "healthy",
        "version": "0.1.0"
    }


# 根路径
@app.get("/", tags=["系统"])
def root():
    """
    API根路径

    返回API信息和文档链接。
    """
    return {
        "message": "Multi-Agent Dev System API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


if __name__ == "__main__":
    import uvicorn

    # 启动服务器
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式：代码变更自动重载
        log_level="info"
    )
