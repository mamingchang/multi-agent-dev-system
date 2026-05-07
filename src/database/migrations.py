"""
Database initialization and migration utilities
数据库初始化和迁移工具
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path
import json
from datetime import datetime
from typing import Optional

from .models import Base, User, Project, ProjectMember, Session as DBSession
from .models import Task, TaskEvent, PendingDecision, UserRole, SessionStatus, TaskStatus


class Database:
    """数据库管理类"""

    def __init__(self, db_path: str = "multi_agent.db"):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def init_db(self):
        """初始化数据库表"""
        Base.metadata.create_all(bind=self.engine)
        print(f"✓ 数据库表已创建: {self.db_path}")

    def drop_all(self):
        """删除所有表（谨慎使用）"""
        Base.metadata.drop_all(bind=self.engine)
        print(f"✓ 所有表已删除: {self.db_path}")

    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()

    def migrate_from_json(self, json_sessions_dir: str = "./sessions"):
        """
        从JSON文件迁移到SQLite

        Args:
            json_sessions_dir: JSON会话文件目录
        """
        sessions_path = Path(json_sessions_dir)
        if not sessions_path.exists():
            print(f"✗ 目录不存在: {json_sessions_dir}")
            return

        db_session = self.get_session()
        migrated_count = 0

        try:
            # 创建默认用户（用于迁移的历史数据）
            default_user = db_session.query(User).filter_by(username="migrated_user").first()
            if not default_user:
                default_user = User(
                    username="migrated_user",
                    email="migrated@example.com",
                    password_hash="migrated",  # 占位符
                    full_name="Migrated User"
                )
                db_session.add(default_user)
                db_session.commit()

            # 创建默认项目
            default_project = db_session.query(Project).filter_by(name="Migrated Project").first()
            if not default_project:
                default_project = Project(
                    name="Migrated Project",
                    description="从JSON文件迁移的历史数据",
                    created_by=default_user.id
                )
                db_session.add(default_project)
                db_session.commit()

                # 添加成员关系
                member = ProjectMember(
                    project_id=default_project.id,
                    user_id=default_user.id,
                    role=UserRole.OWNER
                )
                db_session.add(member)
                db_session.commit()

            # 遍历JSON文件
            for json_file in sessions_path.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    session_id = data.get('session_id')

                    # 检查是否已迁移
                    existing = db_session.query(DBSession).filter_by(id=session_id).first()
                    if existing:
                        continue

                    # 创建Session
                    session = DBSession(
                        id=session_id,
                        project_id=default_project.id,
                        status=SessionStatus(data.get('status', 'active')),
                        metadata=data.get('metadata', {}),
                        created_at=datetime.fromisoformat(data['created_at']),
                        updated_at=datetime.fromisoformat(data['updated_at'])
                    )
                    db_session.add(session)

                    # 创建Tasks
                    for task_id, task_data in data.get('tasks', {}).items():
                        task = Task(
                            id=task_id,
                            session_id=session_id,
                            title=task_data['title'],
                            description=task_data['description'],
                            status=TaskStatus(task_data['status']),
                            current_agent=task_data.get('current_agent'),
                            artifacts=task_data.get('artifacts', {}),
                            created_at=datetime.fromisoformat(task_data['created_at']),
                            updated_at=datetime.fromisoformat(task_data['updated_at'])
                        )
                        db_session.add(task)

                        # 创建TaskEvents（从feedback转换）
                        for feedback in task_data.get('feedback', []):
                            event = TaskEvent(
                                task_id=task_id,
                                agent_name=feedback['from'],
                                agent_type='ai',  # 历史数据默认为AI
                                event_type='feedback',
                                content=feedback,
                                created_at=datetime.fromisoformat(feedback['timestamp'])
                            )
                            db_session.add(event)

                    db_session.commit()
                    migrated_count += 1
                    print(f"✓ 已迁移: {json_file.name}")

                except Exception as e:
                    print(f"✗ 迁移失败 {json_file.name}: {e}")
                    db_session.rollback()

            print(f"\n✓ 迁移完成: {migrated_count} 个会话")

        except Exception as e:
            print(f"✗ 迁移过程出错: {e}")
            db_session.rollback()
        finally:
            db_session.close()

    def create_demo_data(self):
        """创建演示数据"""
        db_session = self.get_session()

        try:
            # 创建用户
            users = [
                User(username="alice", email="alice@example.com", password_hash="hashed", full_name="Alice Wang"),
                User(username="bob", email="bob@example.com", password_hash="hashed", full_name="Bob Li"),
                User(username="charlie", email="charlie@example.com", password_hash="hashed", full_name="Charlie Chen"),
            ]
            for user in users:
                db_session.add(user)
            db_session.commit()

            # 创建项目
            project = Project(
                name="Demo Project",
                description="演示项目",
                created_by=users[0].id
            )
            db_session.add(project)
            db_session.commit()

            # 添加成员
            members = [
                ProjectMember(project_id=project.id, user_id=users[0].id, role=UserRole.OWNER),
                ProjectMember(project_id=project.id, user_id=users[1].id, role=UserRole.MEMBER),
                ProjectMember(project_id=project.id, user_id=users[2].id, role=UserRole.VIEWER),
            ]
            for member in members:
                db_session.add(member)
            db_session.commit()

            print("✓ 演示数据已创建")
            print(f"  - 用户: {len(users)}个")
            print(f"  - 项目: 1个")
            print(f"  - 成员: {len(members)}个")

        except Exception as e:
            print(f"✗ 创建演示数据失败: {e}")
            db_session.rollback()
        finally:
            db_session.close()


def init_database(db_path: str = "multi_agent.db"):
    """初始化数据库（便捷函数）"""
    db = Database(db_path)
    db.init_db()
    return db


if __name__ == "__main__":
    # 测试数据库初始化
    db = init_database("test.db")
    db.create_demo_data()
    print("\n数据库初始化完成！")
