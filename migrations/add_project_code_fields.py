"""
数据库迁移脚本：为Project表添加代码管理字段

添加字段：
- code_path: 项目代码存储路径
- repo_url: Git仓库URL
- repo_branch: Git分支
- project_type: 项目类型（manual/imported）
"""

import sqlite3
import sys

def migrate():
    """执行迁移"""
    db_path = "multi_agent_dev.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("开始迁移...")

        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(projects)")
        columns = [col[1] for col in cursor.fetchall()]

        # 添加code_path字段
        if 'code_path' not in columns:
            print("添加 code_path 字段...")
            cursor.execute("ALTER TABLE projects ADD COLUMN code_path VARCHAR(500)")

        # 添加repo_url字段
        if 'repo_url' not in columns:
            print("添加 repo_url 字段...")
            cursor.execute("ALTER TABLE projects ADD COLUMN repo_url VARCHAR(500)")

        # 添加repo_branch字段
        if 'repo_branch' not in columns:
            print("添加 repo_branch 字段...")
            cursor.execute("ALTER TABLE projects ADD COLUMN repo_branch VARCHAR(100)")

        # 添加project_type字段
        if 'project_type' not in columns:
            print("添加 project_type 字段...")
            cursor.execute("ALTER TABLE projects ADD COLUMN project_type VARCHAR(50) DEFAULT 'manual'")

        conn.commit()
        print("✅ 迁移完成！")

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
