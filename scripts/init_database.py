"""
Database initialization script
初始化数据库并创建演示数据
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.migrations import Database


def main():
    """主函数"""
    print("=" * 80)
    print("Multi-Agent System - 数据库初始化")
    print("=" * 80)

    # 创建数据库
    db_path = project_root / "multi_agent.db"
    db = Database(str(db_path))

    # 初始化表结构
    print("\n1. 创建数据库表...")
    db.init_db()

    # 创建演示数据
    print("\n2. 创建演示数据...")
    db.create_demo_data()

    # 迁移JSON数据（如果存在）
    sessions_dir = project_root / "sessions"
    if sessions_dir.exists():
        print("\n3. 迁移JSON会话数据...")
        db.migrate_from_json(str(sessions_dir))
    else:
        print("\n3. 跳过JSON迁移（sessions目录不存在）")

    print("\n" + "=" * 80)
    print("✓ 数据库初始化完成！")
    print(f"数据库文件: {db_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
