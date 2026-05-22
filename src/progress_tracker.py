"""
进度跟踪器 - 管理项目进度、阶段、任务、里程碑

支持：
- 阶段管理（7个标准阶段）
- 任务管理（创建、更新、完成）
- 里程碑管理
- 统计分析
- 自动进度计算
"""
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import yaml


@dataclass
class Task:
    """任务"""
    id: str
    title: str
    phase: str
    status: str  # pending, in_progress, completed, blocked
    priority: str  # low, medium, high, critical
    assigned_to: str  # Agent名称
    progress: int  # 0-100
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    dependencies: List[str] = None
    artifacts: List[str] = None
    description: str = ""
    notes: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.artifacts is None:
            self.artifacts = []
        if self.notes is None:
            self.notes = []


@dataclass
class Phase:
    """阶段"""
    name: str
    display_name: str
    status: str  # pending, in_progress, completed
    progress: int  # 0-100
    agent: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    artifacts: List[str] = None
    tasks: List[str] = None  # 任务ID列表

    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []
        if self.tasks is None:
            self.tasks = []


@dataclass
class Milestone:
    """里程碑"""
    id: str
    title: str
    description: str
    target_date: str
    status: str  # pending, in_progress, completed
    progress: int  # 0-100
    tasks: List[str] = None  # 任务ID列表

    def __post_init__(self):
        if self.tasks is None:
            self.tasks = []


class ProgressTracker:
    """进度跟踪器"""

    # 标准阶段定义
    STANDARD_PHASES = [
        {'name': 'requirement_analysis', 'display_name': '需求分析', 'agent': 'Requester'},
        {'name': 'product_planning', 'display_name': '产品规划', 'agent': 'Product Manager'},
        {'name': 'architecture_design', 'display_name': '架构设计', 'agent': 'Architect'},
        {'name': 'development', 'display_name': '开发', 'agent': 'Developer'},
        {'name': 'code_review', 'display_name': '代码审查', 'agent': 'Code Reviewer'},
        {'name': 'testing', 'display_name': '测试', 'agent': 'Tester'},
        {'name': 'deployment', 'display_name': '部署', 'agent': 'DevOps'}
    ]

    def __init__(self, project_name: str, user_id: str):
        """
        初始化进度跟踪器

        Args:
            project_name: 项目名称
            user_id: 用户ID
        """
        self.project_name = project_name
        self.user_id = user_id
        self.progress_file = self._get_progress_file()
        self.data = self._load_progress()

    def _get_progress_file(self) -> Path:
        """获取进度文件路径"""
        return Path('users') / self.user_id / 'projects' / self.project_name / 'progress.yaml'

    def _load_progress(self) -> Dict:
        """加载进度数据"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        else:
            # 初始化默认进度数据
            return self._initialize_progress()

    def _initialize_progress(self) -> Dict:
        """初始化进度数据"""
        phases = []
        for phase_def in self.STANDARD_PHASES:
            phase = Phase(
                name=phase_def['name'],
                display_name=phase_def['display_name'],
                status='pending',
                progress=0,
                agent=phase_def['agent']
            )
            phases.append(asdict(phase))

        return {
            'phases': phases,
            'tasks': [],
            'milestones': [],
            'statistics': {
                'overall_progress': 0,
                'phases_summary': {
                    'completed': 0,
                    'in_progress': 0,
                    'pending': len(self.STANDARD_PHASES),
                    'total': len(self.STANDARD_PHASES)
                },
                'tasks_summary': {
                    'completed': 0,
                    'in_progress': 0,
                    'pending': 0,
                    'blocked': 0,
                    'total': 0
                }
            }
        }

    def _save_progress(self):
        """保存进度数据"""
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.data, f, allow_unicode=True, sort_keys=False)

    def start_phase(self, phase_name: str, agent_name: str = None):
        """
        开始一个阶段

        Args:
            phase_name: 阶段名称
            agent_name: Agent名称（可选，使用默认Agent）
        """
        for phase in self.data['phases']:
            if phase['name'] == phase_name:
                phase['status'] = 'in_progress'
                phase['start_time'] = datetime.now().isoformat()
                if agent_name:
                    phase['agent'] = agent_name
                break

        self._update_statistics()
        self._save_progress()

    def update_phase_progress(self, phase_name: str, progress: int):
        """
        更新阶段进度

        Args:
            phase_name: 阶段名称
            progress: 进度 (0-100)
        """
        for phase in self.data['phases']:
            if phase['name'] == phase_name:
                phase['progress'] = min(100, max(0, progress))
                break

        self._update_statistics()
        self._save_progress()

    def complete_phase(self, phase_name: str):
        """
        完成一个阶段

        Args:
            phase_name: 阶段名称
        """
        for phase in self.data['phases']:
            if phase['name'] == phase_name:
                phase['status'] = 'completed'
                phase['progress'] = 100
                phase['end_time'] = datetime.now().isoformat()
                break

        self._update_statistics()
        self._save_progress()

    def create_task(self, task: Task) -> str:
        """
        创建任务

        Args:
            task: 任务对象

        Returns:
            str: 任务ID
        """
        task_dict = asdict(task)
        self.data['tasks'].append(task_dict)

        # 将任务添加到对应阶段
        for phase in self.data['phases']:
            if phase['name'] == task.phase:
                if task.id not in phase['tasks']:
                    phase['tasks'].append(task.id)
                break

        self._update_statistics()
        self._save_progress()

        return task.id

    def update_task(self, task_id: str, updates: Dict):
        """
        更新任务

        Args:
            task_id: 任务ID
            updates: 更新内容
        """
        for task in self.data['tasks']:
            if task['id'] == task_id:
                task.update(updates)

                # 如果状态变为in_progress，记录开始时间
                if updates.get('status') == 'in_progress' and not task.get('started_at'):
                    task['started_at'] = datetime.now().isoformat()

                # 如果状态变为completed，记录完成时间
                if updates.get('status') == 'completed':
                    task['completed_at'] = datetime.now().isoformat()
                    task['progress'] = 100

                break

        self._update_statistics()
        self._save_progress()

    def add_artifact(self, task_id: str, artifact_path: str):
        """
        添加产物到任务

        Args:
            task_id: 任务ID
            artifact_path: 产物路径
        """
        for task in self.data['tasks']:
            if task['id'] == task_id:
                if artifact_path not in task['artifacts']:
                    task['artifacts'].append(artifact_path)
                break

        self._save_progress()

    def get_overall_progress(self) -> int:
        """
        获取整体进度

        Returns:
            int: 整体进度 (0-100)
        """
        return self.data['statistics']['overall_progress']

    def get_phase_progress(self, phase_name: str) -> Optional[Dict]:
        """
        获取阶段进度

        Args:
            phase_name: 阶段名称

        Returns:
            Optional[Dict]: 阶段信息
        """
        for phase in self.data['phases']:
            if phase['name'] == phase_name:
                return phase
        return None

    def get_statistics(self) -> Dict:
        """
        获取统计信息

        Returns:
            Dict: 统计信息
        """
        return self.data['statistics']

    def get_all_tasks(self, phase: str = None, status: str = None, agent: str = None) -> List[Dict]:
        """
        获取任务列表

        Args:
            phase: 过滤阶段
            status: 过滤状态
            agent: 过滤Agent

        Returns:
            List[Dict]: 任务列表
        """
        tasks = self.data['tasks']

        if phase:
            tasks = [t for t in tasks if t['phase'] == phase]
        if status:
            tasks = [t for t in tasks if t['status'] == status]
        if agent:
            tasks = [t for t in tasks if t['assigned_to'] == agent]

        return tasks

    def _update_statistics(self):
        """更新统计信息"""
        # 阶段统计
        phases = self.data['phases']
        phases_summary = {
            'completed': sum(1 for p in phases if p['status'] == 'completed'),
            'in_progress': sum(1 for p in phases if p['status'] == 'in_progress'),
            'pending': sum(1 for p in phases if p['status'] == 'pending'),
            'total': len(phases)
        }

        # 任务统计
        tasks = self.data['tasks']
        tasks_summary = {
            'completed': sum(1 for t in tasks if t['status'] == 'completed'),
            'in_progress': sum(1 for t in tasks if t['status'] == 'in_progress'),
            'pending': sum(1 for t in tasks if t['status'] == 'pending'),
            'blocked': sum(1 for t in tasks if t['status'] == 'blocked'),
            'total': len(tasks)
        }

        # 计算整体进度（基于阶段进度的加权平均）
        if phases:
            total_progress = sum(p['progress'] for p in phases)
            overall_progress = int(total_progress / len(phases))
        else:
            overall_progress = 0

        self.data['statistics'] = {
            'overall_progress': overall_progress,
            'phases_summary': phases_summary,
            'tasks_summary': tasks_summary
        }

    def initialize_from_analysis(self, analysis: Dict):
        """
        根据项目分析初始化进度

        Args:
            analysis: 项目分析结果
        """
        estimated_progress = analysis.get('estimated_progress', {})
        completed_phases = estimated_progress.get('completed_phases', [])

        # 标记已完成的阶段
        for phase_name in completed_phases:
            self.complete_phase(phase_name)

        # 如果有进行中的阶段，标记为in_progress
        if completed_phases:
            # 下一个阶段设为in_progress
            phase_order = [p['name'] for p in self.STANDARD_PHASES]
            for i, phase_name in enumerate(phase_order):
                if phase_name not in completed_phases:
                    self.start_phase(phase_name)
                    # 根据代码量估算进度
                    code_lines = analysis.get('code_lines', 0)
                    if code_lines > 0:
                        # 简单估算：每1000行代码约10%进度
                        progress = min(80, int(code_lines / 1000 * 10))
                        self.update_phase_progress(phase_name, progress)
                    break

        self._save_progress()
