"""
数据库依赖注入

为FastAPI提供数据库实例的依赖注入。
使用单例模式确保所有请求共享同一个数据库实例。
"""

from ..database.database import Database, create_database

# 全局数据库实例（单例）
_db_instance: Database = None


def get_database_instance() -> Database:
    """
    获取全局数据库实例

    使用单例模式，确保所有请求共享同一个数据库。
    对于SQLite内存数据库特别重要。

    Returns:
        Database: 数据库实例
    """
    global _db_instance

    if _db_instance is None:
        # 创建数据库实例
        # 生产环境应该从环境变量读取DATABASE_URL
        _db_instance = create_database()
        _db_instance.init_db()

    return _db_instance


def get_db() -> Database:
    """
    FastAPI依赖注入函数

    Returns:
        Database: 数据库实例
    """
    return get_database_instance()
