"""
审计日志中间件

自动记录API请求到审计日志。
"""

from fastapi import Request
from typing import Callable, Optional
import json

from ..database.database import Database
from ..database.audit_repository import AuditLogRepository
from ..database.models import AuditAction


# 定义需要审计的路由和对应的操作类型
AUDIT_ROUTES = {
    # 用户操作
    ("POST", "/auth/register"): (AuditAction.USER_REGISTER, "user"),
    ("POST", "/auth/login"): (AuditAction.USER_LOGIN, "user"),

    # 组织操作
    ("POST", "/organizations"): (AuditAction.ORG_CREATE, "organization"),
    ("PUT", "/organizations/{org_id}"): (AuditAction.ORG_UPDATE, "organization"),
    ("DELETE", "/organizations/{org_id}"): (AuditAction.ORG_DELETE, "organization"),
    ("POST", "/organizations/{org_id}/members"): (AuditAction.ORG_MEMBER_ADD, "organization"),
    ("DELETE", "/organizations/{org_id}/members/{user_id}"): (AuditAction.ORG_MEMBER_REMOVE, "organization"),
    ("PUT", "/organizations/{org_id}/members/{user_id}"): (AuditAction.ORG_MEMBER_ROLE_UPDATE, "organization"),

    # 项目操作
    ("POST", "/projects"): (AuditAction.PROJECT_CREATE, "project"),
    ("PUT", "/projects/{project_id}"): (AuditAction.PROJECT_UPDATE, "project"),
    ("DELETE", "/projects/{project_id}"): (AuditAction.PROJECT_DELETE, "project"),
    ("POST", "/projects/{project_id}/members"): (AuditAction.PROJECT_MEMBER_ADD, "project"),
    ("DELETE", "/projects/{project_id}/members/{user_id}"): (AuditAction.PROJECT_MEMBER_REMOVE, "project"),

    # 工作流操作
    ("POST", "/workflow/sessions"): (AuditAction.SESSION_CREATE, "session"),
    ("POST", "/workflow/tasks"): (AuditAction.TASK_CREATE, "task"),
    ("POST", "/workflow/tasks/{task_id}/execute"): (AuditAction.TASK_EXECUTE, "task"),
}


def extract_resource_id(path: str, path_params: dict) -> Optional[str]:
    """
    从路径参数中提取资源ID

    Args:
        path: 请求路径
        path_params: 路径参数

    Returns:
        str: 资源ID
    """
    # 优先级：org_id > project_id > task_id > session_id > user_id
    for key in ["org_id", "project_id", "task_id", "session_id", "user_id"]:
        if key in path_params:
            return str(path_params[key])

    return None


def should_audit(method: str, path: str) -> bool:
    """
    判断是否需要审计该请求

    Args:
        method: HTTP方法
        path: 请求路径

    Returns:
        bool: 是否需要审计
    """
    # 检查精确匹配
    if (method, path) in AUDIT_ROUTES:
        return True

    # 检查模式匹配（带路径参数）
    for (route_method, route_path) in AUDIT_ROUTES.keys():
        if method == route_method:
            # 简单的路径模式匹配
            route_parts = route_path.split("/")
            path_parts = path.split("/")

            if len(route_parts) == len(path_parts):
                match = True
                for route_part, path_part in zip(route_parts, path_parts):
                    if route_part.startswith("{") and route_part.endswith("}"):
                        # 路径参数，跳过
                        continue
                    elif route_part != path_part:
                        match = False
                        break

                if match:
                    return True

    return False


def get_audit_info(method: str, path: str) -> Optional[tuple]:
    """
    获取审计信息

    Args:
        method: HTTP方法
        path: 请求路径

    Returns:
        tuple: (AuditAction, resource_type) 或 None
    """
    # 检查精确匹配
    if (method, path) in AUDIT_ROUTES:
        return AUDIT_ROUTES[(method, path)]

    # 检查模式匹配
    for (route_method, route_path), audit_info in AUDIT_ROUTES.items():
        if method == route_method:
            route_parts = route_path.split("/")
            path_parts = path.split("/")

            if len(route_parts) == len(path_parts):
                match = True
                for route_part, path_part in zip(route_parts, path_parts):
                    if route_part.startswith("{") and route_part.endswith("}"):
                        continue
                    elif route_part != path_part:
                        match = False
                        break

                if match:
                    return audit_info

    return None


async def audit_middleware(request: Request, call_next: Callable):
    """
    审计日志中间件

    自动记录需要审计的API请求。

    Args:
        request: FastAPI请求对象
        call_next: 下一个中间件或路由处理器

    Returns:
        Response: 响应对象
    """
    method = request.method
    path = request.url.path

    # 检查是否需要审计
    if not should_audit(method, path):
        # 不需要审计，直接处理请求
        return await call_next(request)

    # 获取审计信息
    audit_info = get_audit_info(method, path)
    if not audit_info:
        return await call_next(request)

    action, resource_type = audit_info

    # 提取用户信息（如果已认证）
    user_id = None
    username = None
    organization_id = None

    if hasattr(request.state, "user"):
        user = request.state.user
        user_id = user.id
        username = user.username

    # 提取IP地址
    ip_address = request.client.host if request.client else None

    # 提取User-Agent
    user_agent = request.headers.get("user-agent")

    # 提取资源ID（从路径参数）
    path_params = request.path_params
    resource_id = extract_resource_id(path, path_params)

    # 如果是创建操作，资源ID在响应中
    if not resource_id and method == "POST":
        resource_id = "pending"

    # 提取请求详情
    details = {
        "method": method,
        "path": path,
        "path_params": path_params,
        "query_params": dict(request.query_params)
    }

    # 尝试提取请求体（仅对POST/PUT）
    if method in ["POST", "PUT"]:
        try:
            # 读取请求体（注意：这会消耗请求体，需要重新设置）
            body = await request.body()
            if body:
                try:
                    details["body"] = json.loads(body.decode())
                    # 移除敏感信息
                    if "password" in details["body"]:
                        details["body"]["password"] = "***"
                except:
                    pass
        except:
            pass

    # 处理请求
    response = await call_next(request)

    # 确定状态
    status = "success" if response.status_code < 400 else "failed"
    error_message = None

    # 如果是创建操作，从响应中提取资源ID
    if method == "POST" and resource_id == "pending" and response.status_code == 201:
        # TODO: 从响应体中提取ID（需要读取响应体）
        resource_id = "created"

    # 从请求体中提取organization_id（如果有）
    if "body" in details and isinstance(details["body"], dict):
        if "organization_id" in details["body"]:
            organization_id = details["body"]["organization_id"]

    # 记录审计日志
    try:
        db = Database()  # 创建新的数据库连接
        with db.get_session() as session:
            audit_repo = AuditLogRepository(session)
            audit_repo.create(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id or "unknown",
                user_id=user_id,
                username=username,
                organization_id=organization_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details,
                status=status,
                error_message=error_message
            )
    except Exception as e:
        # 审计日志记录失败不应该影响正常请求
        print(f"审计日志记录失败: {e}")

    return response
