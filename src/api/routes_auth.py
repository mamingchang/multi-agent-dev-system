"""
用户认证相关API路由

端点：
- POST /auth/register - 用户注册
- POST /auth/login - 用户登录
- GET /auth/me - 获取当前用户信息
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.database import Database, UserRepository
from ..database.organization_repository import OrganizationRepository, OrganizationMemberRepository
from ..database.models import OrganizationRole
from .schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from .auth import hash_password, authenticate_user, create_access_token, get_current_active_user
from .dependencies import get_db
from ..database.models import User

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Database = Depends(get_db)):
    """
    用户注册

    创建新用户账号。
    """
    with db.get_session() as session:
        user_repo = UserRepository(session)

        # 检查用户名是否已存在
        existing_user = user_repo.get_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )

        # 检查邮箱是否已存在
        existing_email = user_repo.get_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )

        # 创建用户
        hashed_password = hash_password(user_data.password)
        user = user_repo.create(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            full_name=user_data.full_name
        )

        # 自动为新用户创建默认组织
        org_repo = OrganizationRepository(session)
        member_repo = OrganizationMemberRepository(session)

        default_org = org_repo.create(
            name=f"{user.username}的组织",
            slug=f"{user.username}-org",
            description="默认组织"
        )

        # 将用户添加为组织管理员
        member_repo.add_member(
            organization_id=default_org.id,
            user_id=user.id,
            role=OrganizationRole.ORG_ADMIN
        )

        session.commit()

        # 立即转换为响应模型（在session关闭前）
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at
        )


@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, db: Database = Depends(get_db)):
    """
    用户登录

    验证用户名和密码，返回JWT Token。
    """
    with db.get_session() as session:
        # 认证用户
        user = authenticate_user(session, login_data.username, login_data.password)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 创建Token（sub必须是字符串）
        access_token = create_access_token(data={"sub": str(user.id)})

        # 立即转换为响应模型
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    获取当前用户信息

    需要认证。返回当前登录用户的信息。
    """
    return current_user
