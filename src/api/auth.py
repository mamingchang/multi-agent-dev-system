"""
认证和授权模块

实现：
1. JWT Token生成和验证
2. 密码哈希和验证
3. 用户认证依赖
4. 权限检查

为什么使用JWT：
- 无状态：不需要服务器存储session
- 可扩展：可以在token中存储用户信息
- 跨域友好：适合前后端分离架构

安全考虑：
- 使用bcrypt哈希密码
- Token设置过期时间
- 敏感操作需要验证权限
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database.database import Database, UserRepository
from ..database.models import User

# JWT配置
SECRET_KEY = "your-secret-key-change-in-production"  # 生产环境应该从环境变量读取
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

# 密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer认证
security = HTTPBearer()


def hash_password(password: str) -> str:
    """
    哈希密码

    Args:
        password: 明文密码

    Returns:
        str: 哈希后的密码
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        bool: 是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT Token

    Args:
        data: 要编码的数据（通常包含user_id）
        expires_delta: 过期时间

    Returns:
        str: JWT Token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    解码JWT Token

    Args:
        token: JWT Token

    Returns:
        dict: 解码后的数据，如果失败返回None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def authenticate_user(db_session: Session, username: str, password: str) -> Optional[User]:
    """
    认证用户

    Args:
        db_session: 数据库Session
        username: 用户名
        password: 密码

    Returns:
        User: 用户对象，如果认证失败返回None
    """
    user_repo = UserRepository(db_session)
    user = user_repo.get_by_username(username)

    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    获取当前用户（依赖注入）

    从HTTP Authorization Header中提取Token，验证并返回用户对象。
    用于需要认证的API端点。

    Args:
        credentials: HTTP Bearer Token

    Returns:
        User: 当前用户

    Raises:
        HTTPException: 如果Token无效或用户不存在
    """
    from .dependencies import get_db

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    user_id_str = payload.get("sub")

    # sub是字符串，需要转换为int
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    if user_id is None:
        raise credentials_exception

    # 从数据库获取用户
    db = get_db()
    with db.get_session() as session:
        user_repo = UserRepository(session)
        user = user_repo.get_by_id(user_id)

        if user is None:
            raise credentials_exception

        # 访问所有需要的属性（触发加载）
        _ = user.id
        _ = user.username
        _ = user.email

        # 从session中分离对象
        session.expunge(user)

        return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前活跃用户

    可以在这里添加额外的检查，比如用户是否被禁用。

    Args:
        current_user: 当前用户

    Returns:
        User: 当前活跃用户
    """
    # 这里可以添加用户状态检查
    # if current_user.disabled:
    #     raise HTTPException(status_code=400, detail="用户已被禁用")

    return current_user


def check_project_permission(
    user: User,
    project_id: int,
    db: Database,
    required_role: Optional[str] = None
) -> bool:
    """
    检查用户对项目的权限

    Args:
        user: 用户对象
        project_id: 项目ID
        db: 数据库实例
        required_role: 需要的角色（owner/admin/member/viewer）

    Returns:
        bool: 是否有权限

    Raises:
        HTTPException: 如果没有权限
    """
    from ..database.models import ProjectMember, UserRole

    with db.get_session() as session:
        # 查询用户在项目中的角色
        member = session.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id
        ).first()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您不是该项目的成员"
            )

        # 如果指定了required_role，检查角色
        if required_role:
            role_hierarchy = {
                "viewer": 0,
                "member": 1,
                "admin": 2,
                "owner": 3
            }

            user_role_level = role_hierarchy.get(member.role.value, 0)
            required_role_level = role_hierarchy.get(required_role, 0)

            if user_role_level < required_role_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要{required_role}权限"
                )

        return True
