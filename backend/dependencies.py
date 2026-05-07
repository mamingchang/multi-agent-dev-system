"""
Dependencies
依赖注入 - 提供数据库会话和管理器实例
"""
from typing import Generator
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from src.database.migrations import Database
from src.project_manager import ProjectManager
from src.decision_queue import DecisionQueue
from src.event_logger import EventLogger
from .config import settings

# 初始化数据库
db_instance = Database(settings.DATABASE_URL.replace("sqlite:///", ""))

# OAuth2认证
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话"""
    db = db_instance.get_session()
    try:
        yield db
    finally:
        db.close()


def get_project_manager(db: Session = Depends(get_db)) -> ProjectManager:
    """获取项目管理器"""
    return ProjectManager(db)


def get_decision_queue(db: Session = Depends(get_db)) -> DecisionQueue:
    """获取决策队列"""
    return DecisionQueue(db)


def get_event_logger(db: Session = Depends(get_db)) -> EventLogger:
    """获取事件日志记录器"""
    return EventLogger(db)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> dict:
    """
    获取当前登录用户

    Args:
        token: JWT token
        db: 数据库会话

    Returns:
        用户信息

    Raises:
        HTTPException: 认证失败
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    from src.database.models import User
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name
    }


def check_project_permission(
    project_id: int,
    user_id: int,
    action: str,
    project_manager: ProjectManager
) -> bool:
    """
    检查项目权限

    Args:
        project_id: 项目ID
        user_id: 用户ID
        action: 操作名称
        project_manager: 项目管理器

    Returns:
        是否有权限

    Raises:
        HTTPException: 无权限
    """
    if not project_manager.check_permission(project_id, user_id, action):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No permission to {action} in project {project_id}"
        )
    return True
