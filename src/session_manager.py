"""
Session Manager
会话管理器：管理多个工作流会话，支持持久化和恢复
"""
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from .workflow.task import Task, TaskStatus


class Session:
    """会话对象"""

    def __init__(self, session_id: str = None, user_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.user_id = user_id or "default_user"
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.tasks: Dict[str, Task] = {}
        self.metadata: Dict[str, Any] = {}
        self.status = "active"  # active, paused, completed, failed

    def add_task(self, task: Task) -> None:
        """添加任务到会话"""
        self.tasks[task.task_id] = task
        self.updated_at = datetime.now()

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)

    def list_tasks(self) -> List[str]:
        """列出所有任务ID"""
        return list(self.tasks.keys())

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'status': self.status,
            'metadata': self.metadata,
            'tasks': {
                task_id: task.to_dict()
                for task_id, task in self.tasks.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """从字典反序列化"""
        session = cls(
            session_id=data['session_id'],
            user_id=data['user_id']
        )
        session.created_at = datetime.fromisoformat(data['created_at'])
        session.updated_at = datetime.fromisoformat(data['updated_at'])
        session.status = data['status']
        session.metadata = data['metadata']

        # 重建Task对象
        for task_id, task_data in data['tasks'].items():
            task = Task(
                task_id=task_data['task_id'],
                title=task_data['title'],
                description=task_data['description']
            )
            task.status = TaskStatus(task_data['status'])
            task.created_at = datetime.fromisoformat(task_data['created_at'])
            task.updated_at = datetime.fromisoformat(task_data['updated_at'])
            task.current_agent = task_data['current_agent']
            task.artifacts = task_data['artifacts']
            task.feedback = task_data['feedback']
            session.tasks[task_id] = task

        return session


class SessionManager:
    """会话管理器"""

    def __init__(self, storage_path: str = "./sessions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.active_sessions: Dict[str, Session] = {}

    def create_session(self, user_id: str = None) -> Session:
        """创建新会话"""
        session = Session(user_id=user_id)
        self.active_sessions[session.session_id] = session
        print(f"✓ 创建会话: {session.session_id} (用户: {session.user_id})")
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话（优先从内存，然后从磁盘加载）"""
        # 先查内存
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]

        # 再查磁盘
        session = self.load_session(session_id)
        if session:
            self.active_sessions[session_id] = session
        return session

    def save_session(self, session: Session) -> bool:
        """保存会话到磁盘"""
        try:
            file_path = self.storage_path / f"{session.session_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"✓ 会话已保存: {session.session_id}")
            return True
        except Exception as e:
            print(f"✗ 保存会话失败: {e}")
            return False

    def load_session(self, session_id: str) -> Optional[Session]:
        """从磁盘加载会话"""
        try:
            file_path = self.storage_path / f"{session_id}.json"
            if not file_path.exists():
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            session = Session.from_dict(data)
            print(f"✓ 会话已加载: {session_id}")
            return session
        except Exception as e:
            print(f"✗ 加载会话失败: {e}")
            return None

    def list_sessions(self, user_id: str = None) -> List[Dict[str, Any]]:
        """列出所有会话"""
        sessions = []

        # 扫描磁盘上的会话文件
        for file_path in self.storage_path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if user_id is None or data['user_id'] == user_id:
                    sessions.append({
                        'session_id': data['session_id'],
                        'user_id': data['user_id'],
                        'status': data['status'],
                        'created_at': data['created_at'],
                        'updated_at': data['updated_at'],
                        'task_count': len(data['tasks'])
                    })
            except Exception as e:
                print(f"✗ 读取会话文件失败 {file_path}: {e}")

        return sorted(sessions, key=lambda x: x['updated_at'], reverse=True)

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            # 从内存删除
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]

            # 从磁盘删除
            file_path = self.storage_path / f"{session_id}.json"
            if file_path.exists():
                file_path.unlink()

            print(f"✓ 会话已删除: {session_id}")
            return True
        except Exception as e:
            print(f"✗ 删除会话失败: {e}")
            return False

    def pause_session(self, session_id: str) -> bool:
        """暂停会话"""
        session = self.get_session(session_id)
        if session:
            session.status = "paused"
            session.updated_at = datetime.now()
            return self.save_session(session)
        return False

    def resume_session(self, session_id: str) -> Optional[Session]:
        """恢复会话"""
        session = self.get_session(session_id)
        if session:
            session.status = "active"
            session.updated_at = datetime.now()
            self.save_session(session)
            print(f"✓ 会话已恢复: {session_id}")
            return session
        return None

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """清理旧会话"""
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0

        for file_path in self.storage_path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                updated_at = datetime.fromisoformat(data['updated_at'])
                if updated_at < cutoff_date:
                    file_path.unlink()
                    deleted_count += 1
            except Exception:
                pass

        print(f"✓ 清理了 {deleted_count} 个旧会话")
        return deleted_count
