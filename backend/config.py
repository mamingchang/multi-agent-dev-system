"""
Backend Configuration
后端配置
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional, List, Union


class Settings(BaseSettings):
    """应用配置"""

    # 应用基本信息
    APP_NAME: str = "Multi-Agent Dev System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./multi_agent_dev.db"

    # JWT认证配置
    SECRET_KEY: str = "dev-secret-key-change-in-production-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时

    # CORS配置
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    # WebSocket配置
    WS_HEARTBEAT_INTERVAL: int = 30  # 秒

    # API Keys
    ANTHROPIC_API_KEY: Optional[str] = None

    # Server配置
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 忽略额外字段


settings = Settings()
