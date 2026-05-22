"""
项目级任务管理系统
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.workflow.task import Task, TaskStatus


class TaskManager:
    """项目级任务管理器"""

    def __init__(self, user_id: str, project_name: str, base_dir: str = "users"):
        self.user_id = user_id
        self.project_name = project_name
        self.base_dir = Path(base_dir)
        self.tasks_dir = self.base_dir / user_id / "projects" / project_name / "tasks"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def create_task(self, title: str, description: str) -> Task:
        """创建新任务"""
        import uuid
        task = Task(
            task_id=str(uuid.uuid4()),
            title=title,
            description=description
        )
        self.save_task(task)
        return task

    def save_task(self, task: Task):
        """保存任务"""
        task_file = self.tasks_dir / f"{task.task_id}.json"
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task.to_dict(), f, indent=2, ensure_ascii=False)

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        task_file = self.tasks_dir / f"{task_id}.json"
        if not task_file.exists():
            return None

        with open(task_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return Task.from_dict(data)

    def list_tasks(self, status: str = None) -> List[Dict[str, Any]]:
        """列出所有任务"""
        tasks = []
        for task_file in self.tasks_dir.glob("*.json"):
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if status is None or data.get('status') == status:
                        tasks.append(data)
            except Exception as e:
                print(f"读取任务失败 {task_file}: {e}")

        tasks.sort(key=lambda t: t.get('created_at', ''), reverse=True)
        return tasks

    def update_task_status(self, task_id: str, status: TaskStatus, agent_name: str = None):
        """更新任务状态"""
        task = self.get_task(task_id)
        if task:
            task.update_status(status, agent_name)
            self.save_task(task)

    def delete_task(self, task_id: str):
        """删除任务"""
        task_file = self.tasks_dir / f"{task_id}.json"
        if task_file.exists():
            task_file.unlink()
