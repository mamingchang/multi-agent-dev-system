"""
项目管理系统

负责：
1. 项目创建和配置
2. 项目工作空间管理
3. 项目会话管理
4. 项目文件隔离
"""
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class Project:
    """项目对象"""

    def __init__(
        self,
        project_id: str,
        project_name: str,
        owner: str,
        description: str = "",
        agents: List[str] = None,
        settings: Dict = None,
        status: str = "active"
    ):
        self.project_id = project_id
        self.project_name = project_name
        self.owner = owner
        self.description = description
        self.agents = agents or []
        self.settings = settings or {}
        self.status = status
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.tags = []

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'project_id': self.project_id,
            'project_name': self.project_name,
            'owner': self.owner,
            'description': self.description,
            'agents': self.agents,
            'settings': self.settings,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'tags': self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """从字典创建"""
        project = cls(
            project_id=data['project_id'],
            project_name=data['project_name'],
            owner=data['owner'],
            description=data.get('description', ''),
            agents=data.get('agents', []),
            settings=data.get('settings', {}),
            status=data.get('status', 'active')
        )
        project.created_at = data.get('created_at', datetime.now().isoformat())
        project.updated_at = data.get('updated_at', project.created_at)
        project.tags = data.get('tags', [])
        return project


class ProjectManager:
    """项目管理器"""

    def __init__(self, user_id: str, base_dir: str = "users"):
        self.user_id = user_id
        self.base_dir = Path(base_dir)
        self.projects_dir = self.base_dir / user_id / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.current_project_file = self.base_dir / user_id / ".current_project"

    def create_project(
        self,
        project_name: str,
        description: str = "",
        agents: List[str] = None,
        settings: Dict = None
    ):
        """创建新项目"""
        if self.project_exists(project_name):
            raise ValueError(f"项目已存在: {project_name}")

        project_id = project_name
        project = Project(
            project_id=project_id,
            project_name=project_name,
            owner=self.user_id,
            description=description,
            agents=agents or [],
            settings=settings or {}
        )

        project_dir = self.projects_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "sessions").mkdir(exist_ok=True)
        (project_dir / "workspace").mkdir(exist_ok=True)
        (project_dir / "artifacts").mkdir(exist_ok=True)
        (project_dir / "docs").mkdir(exist_ok=True)

        artifacts_dir = project_dir / "artifacts"
        (artifacts_dir / "requirements").mkdir(exist_ok=True)
        (artifacts_dir / "designs").mkdir(exist_ok=True)
        (artifacts_dir / "code").mkdir(exist_ok=True)
        (artifacts_dir / "tests").mkdir(exist_ok=True)
        (artifacts_dir / "reviews").mkdir(exist_ok=True)
        (artifacts_dir / "deployments").mkdir(exist_ok=True)

        self._save_project(project)

        readme_path = project_dir / "workspace" / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(f"# {project_name}\n\n{description}\n\n创建时间: {project.created_at}\n")

        return project

    def get_project(self, project_name: str):
        """获取项目信息"""
        config_path = self.projects_dir / project_name / "project.yaml"
        if not config_path.exists():
            return None
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return Project.from_dict(data)

    def project_exists(self, project_name: str) -> bool:
        """检查项目是否存在"""
        return (self.projects_dir / project_name / "project.yaml").exists()

    def list_projects(self, status: str = None):
        """列出所有项目"""
        projects = []
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir():
                config_path = project_dir / "project.yaml"
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    project = Project.from_dict(data)
                    if status is None or project.status == status:
                        projects.append(project)
        projects.sort(key=lambda p: p.created_at, reverse=True)
        return projects

    def update_project(self, project_name: str, updates: Dict[str, Any]):
        """更新项目信息"""
        project = self.get_project(project_name)
        if not project:
            raise ValueError(f"项目不存在: {project_name}")
        if 'description' in updates:
            project.description = updates['description']
        if 'agents' in updates:
            project.agents = updates['agents']
        if 'settings' in updates:
            project.settings.update(updates['settings'])
        if 'status' in updates:
            project.status = updates['status']
        if 'tags' in updates:
            project.tags = updates['tags']
        project.updated_at = datetime.now().isoformat()
        self._save_project(project)
        return project

    def archive_project(self, project_name: str):
        """归档项目"""
        return self.update_project(project_name, {'status': 'archived'})

    def activate_project(self, project_name: str):
        """激活项目"""
        return self.update_project(project_name, {'status': 'active'})

    def delete_project(self, project_name: str):
        """删除项目"""
        if not self.project_exists(project_name):
            raise ValueError(f"项目不存在: {project_name}")
        import shutil
        project_dir = self.projects_dir / project_name
        shutil.rmtree(project_dir)

    def set_current_project(self, project_name: str):
        """设置当前项目"""
        if not self.project_exists(project_name):
            raise ValueError(f"项目不存在: {project_name}")
        with open(self.current_project_file, 'w', encoding='utf-8') as f:
            f.write(project_name)

    def get_current_project(self):
        """获取当前项目"""
        if not self.current_project_file.exists():
            return None
        with open(self.current_project_file, 'r', encoding='utf-8') as f:
            project_name = f.read().strip()
        return self.get_project(project_name)

    def get_current_project_name(self):
        """获取当前项目名称"""
        project = self.get_current_project()
        return project.project_name if project else None

    def get_project_dir(self, project_name: str) -> Path:
        """获取项目根目录"""
        return self.projects_dir / project_name

    def get_project_workspace(self, project_name: str) -> Path:
        """获取项目工作空间路径"""
        return self.projects_dir / project_name / "workspace"

    def get_project_sessions_dir(self, project_name: str) -> Path:
        """获取项目会话目录"""
        return self.projects_dir / project_name / "sessions"

    def get_project_artifacts_dir(self, project_name: str) -> Path:
        """获取项目产物目录"""
        return self.projects_dir / project_name / "artifacts"

    def get_project_docs_dir(self, project_name: str) -> Path:
        """获取项目文档目录"""
        return self.projects_dir / project_name / "docs"

    def list_project_sessions(self, project_name: str):
        """列出项目的所有会话"""
        sessions_dir = self.get_project_sessions_dir(project_name)
        if not sessions_dir.exists():
            return []
        sessions = []
        for session_file in sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session = json.load(f)
                sessions.append(session)
            except Exception as e:
                print(f"读取会话失败 {session_file}: {e}")
        sessions.sort(key=lambda s: s.get('created_at', ''), reverse=True)
        return sessions

    def _save_project(self, project):
        """保存项目配置"""
        config_path = self.projects_dir / project.project_id / "project.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(project.to_dict(), f, allow_unicode=True)

    def add_agent_to_project(self, project_name: str, agent_name: str, agent_source: str = None):
        """
        添加Agent到项目

        Args:
            project_name: 项目名称
            agent_name: Agent名称
            agent_source: Agent来源（格式：user_id:agent_name，表示使用其他用户的公开Agent）

        Returns:
            bool: 是否成功
        """
        project = self.get_project(project_name)
        if not project:
            raise ValueError(f"项目不存在: {project_name}")

        # 构建Agent标识
        if agent_source:
            agent_id = agent_source  # 使用完整的agent_id
        else:
            agent_id = agent_name  # 使用当前用户的Agent

        # 检查是否已存在
        if agent_id in project.agents:
            return False

        project.agents.append(agent_id)
        project.updated_at = datetime.now().isoformat()
        self._save_project(project)
        return True

    def remove_agent_from_project(self, project_name: str, agent_name: str):
        """
        从项目移除Agent

        Args:
            project_name: 项目名称
            agent_name: Agent名称

        Returns:
            bool: 是否成功
        """
        project = self.get_project(project_name)
        if not project:
            raise ValueError(f"项目不存在: {project_name}")

        if agent_name in project.agents:
            project.agents.remove(agent_name)
            project.updated_at = datetime.now().isoformat()
            self._save_project(project)
            return True
        return False

    def list_project_agents(self, project_name: str) -> List[str]:
        """
        列出项目的Agent

        Args:
            project_name: 项目名称

        Returns:
            List[str]: Agent列表
        """
        project = self.get_project(project_name)
        if not project:
            return []
        return project.agents or []

