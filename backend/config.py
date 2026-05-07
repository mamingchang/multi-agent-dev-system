"""
Backend Configuration
后端配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""

    # 应用基本信息
    APP_NAME: str = "Multi-Agent Dev System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./multi_agent.db"

    # JWT认证配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时

    # CORS配置
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    # WebSocket配置
    WS_HEARTBEAT_INTERVAL: int = 30  # 秒

    class Config:
        env_file = ".env"


settings = Settings()
