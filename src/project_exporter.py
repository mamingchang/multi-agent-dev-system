"""
项目导出器 - 导出项目到多种格式

支持：
- 导出为项目包（.mas格式）
- 导出到Git仓库
- 导出进度报告（Markdown/HTML/JSON）
"""
from pathlib import Path
from typing import Dict, Optional
import subprocess
import shutil
import zipfile
import json
from datetime import datetime

from .project_manager import ProjectManager
from .progress_tracker import ProgressTracker


class ProjectExporter:
    """项目导出器"""

    def __init__(self, user_id: str):
        """
        初始化导出器

        Args:
            user_id: 用户ID
        """
        self.user_id = user_id
        self.project_manager = ProjectManager(user_id)

    def export_to_package(self, project_name: str, output_file: str,
                         code_only: bool = False,
                         no_memories: bool = False,
                         no_sessions: bool = False,
                         compress_level: int = 6) -> Dict:
        """
        导出项目为项目包

        Args:
            project_name: 项目名称
            output_file: 输出文件路径
            code_only: 是否只导出代码
            no_memories: 是否排除Agent记忆
            no_sessions: 是否排除会话记录
            compress_level: 压缩级别 (0-9)

        Returns:
            Dict: 导出结果
        """
        print(f"正在导出项目: {project_name}")

        # 检查项目是否存在
        project = self.project_manager.get_project(project_name)
        if not project:
            return {
                'success': False,
                'error': f'项目不存在: {project_name}'
            }

        project_dir = self.project_manager.get_project_dir(project_name)
        output_path = Path(output_file)

        print("\n正在打包项目...")

        # 创建临时目录
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 1. 收集项目配置
            print("✓ 收集项目配置")
            if (project_dir / 'project.yaml').exists():
                shutil.copy(project_dir / 'project.yaml', temp_path / 'project.yaml')

            # 2. 收集进度数据（如果不是code_only）
            if not code_only and (project_dir / 'progress.yaml').exists():
                print("✓ 收集进度数据")
                shutil.copy(project_dir / 'progress.yaml', temp_path / 'progress.yaml')

            # 3. 打包代码
            workspace_path = self.project_manager.get_project_workspace(project_name)
            if workspace_path.exists():
                file_count = sum(1 for _ in workspace_path.rglob('*') if _.is_file())
                print(f"✓ 打包代码 ({file_count} 个文件)")
                shutil.copytree(workspace_path, temp_path / 'workspace')

            # 4. 打包产物
            artifacts_path = self.project_manager.get_project_artifacts_dir(project_name)
            if artifacts_path.exists():
                artifact_count = sum(1 for _ in artifacts_path.rglob('*') if _.is_file())
                if artifact_count > 0:
                    print(f"✓ 打包产物 ({artifact_count} 个文件)")
                    shutil.copytree(artifacts_path, temp_path / 'artifacts')

            # 5. 打包文档
            docs_path = self.project_manager.get_project_docs_dir(project_name)
            if docs_path.exists():
                doc_count = sum(1 for _ in docs_path.rglob('*') if _.is_file())
                if doc_count > 0:
                    print(f"✓ 打包文档 ({doc_count} 个文件)")
                    shutil.copytree(docs_path, temp_path / 'docs')

            # 6. 打包Agent记忆（如果不排除）
            if not code_only and not no_memories:
                memories_path = project_dir / 'agent_memories'
                if memories_path.exists():
                    memory_count = sum(1 for _ in memories_path.iterdir() if _.is_dir())
                    if memory_count > 0:
                        print(f"✓ 打包Agent记忆 ({memory_count} 个Agent)")
                        shutil.copytree(memories_path, temp_path / 'agent_memories')

            # 7. 打包会话记录（如果不排除）
            if not code_only and not no_sessions:
                sessions_path = self.project_manager.get_project_sessions_dir(project_name)
                if sessions_path.exists():
                    session_count = sum(1 for _ in sessions_path.glob('*.json'))
                    if session_count > 0:
                        print(f"✓ 打包会话记录 ({session_count} 个会话)")
                        shutil.copytree(sessions_path, temp_path / 'sessions')

            # 8. 创建manifest
            manifest = {
                'version': '1.0',
                'project_name': project_name,
                'exported_by': self.user_id,
                'exported_at': datetime.now().isoformat(),
                'mas_version': '1.0.0',
                'contents': {
                    'project_config': True,
                    'progress_data': not code_only and (project_dir / 'progress.yaml').exists(),
                    'workspace': workspace_path.exists(),
                    'artifacts': artifacts_path.exists(),
                    'docs': docs_path.exists(),
                    'agent_memories': not code_only and not no_memories and (project_dir / 'agent_memories').exists(),
                    'sessions': not code_only and not no_sessions and sessions_path.exists()
                }
            }

            with open(temp_path / 'manifest.json', 'w') as f:
                json.dump(manifest, f, indent=2)

            # 9. 压缩
            print("\n正在压缩...")
            total_size = sum(f.stat().st_size for f in temp_path.rglob('*') if f.is_file())

            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=compress_level) as zipf:
                for file_path in temp_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_path)
                        zipf.write(file_path, arcname)

            compressed_size = output_path.stat().st_size
            print(f"✓ 压缩完成 ({total_size / 1024 / 1024:.1f} MB → {compressed_size / 1024 / 1024:.1f} MB)")

            return {
                'success': True,
                'output_file': str(output_path),
                'file_size': compressed_size,
                'manifest': manifest
            }

    def export_to_git(self, project_name: str, remote_url: str,
                     branch: str = 'main', code_only: bool = True) -> Dict:
        """
        导出项目到Git仓库

        Args:
            project_name: 项目名称
            remote_url: 远程仓库URL
            branch: 分支名称
            code_only: 是否只推送代码（不推送配置文件）

        Returns:
            Dict: 导出结果
        """
        print(f"正在导出项目到Git: {remote_url}")

        # 检查项目是否存在
        project = self.project_manager.get_project(project_name)
        if not project:
            return {
                'success': False,
                'error': f'项目不存在: {project_name}'
            }

        workspace_path = self.project_manager.get_project_workspace(project_name)

        # 1. 检查是否已初始化Git
        git_dir = workspace_path / '.git'
        if not git_dir.exists():
            print("\n正在初始化Git仓库...")
            try:
                subprocess.run(['git', 'init'], cwd=workspace_path, check=True, capture_output=True)
                print("✓ Git仓库已初始化")
            except subprocess.CalledProcessError as e:
                return {
                    'success': False,
                    'error': f'Git初始化失败: {e.stderr.decode()}'
                }

        # 2. 创建.gitignore（如果不存在）
        gitignore_path = workspace_path / '.gitignore'
        if not gitignore_path.exists():
            print("\n正在创建.gitignore...")
            gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local

# Logs
*.log
logs/
"""
            with open(gitignore_path, 'w') as f:
                f.write(gitignore_content.strip())
            print("✓ .gitignore已创建")

        # 3. 添加所有文件
        print("\n正在添加文件...")
        try:
            subprocess.run(['git', 'add', '.'], cwd=workspace_path, check=True, capture_output=True)
            print("✓ 文件已添加")
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f'添加文件失败: {e.stderr.decode()}'
            }

        # 4. 提交
        print("\n正在提交...")
        try:
            commit_message = f"Export from MAS project: {project_name}"
            subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=workspace_path,
                check=True,
                capture_output=True
            )
            print("✓ 提交成功")
        except subprocess.CalledProcessError as e:
            # 可能没有更改
            stderr = e.stderr.decode()
            if 'nothing to commit' in stderr:
                print("✓ 没有新的更改")
            else:
                return {
                    'success': False,
                    'error': f'提交失败: {stderr}'
                }

        # 5. 添加远程仓库
        print("\n正在配置远程仓库...")
        try:
            # 检查是否已有remote
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=workspace_path,
                capture_output=True
            )

            if result.returncode != 0:
                # 添加remote
                subprocess.run(
                    ['git', 'remote', 'add', 'origin', remote_url],
                    cwd=workspace_path,
                    check=True,
                    capture_output=True
                )
                print("✓ 远程仓库已添加")
            else:
                # 更新remote
                subprocess.run(
                    ['git', 'remote', 'set-url', 'origin', remote_url],
                    cwd=workspace_path,
                    check=True,
                    capture_output=True
                )
                print("✓ 远程仓库已更新")
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f'配置远程仓库失败: {e.stderr.decode()}'
            }

        # 6. 推送
        print(f"\n正在推送到 {branch} 分支...")
        try:
            subprocess.run(
                ['git', 'push', '-u', 'origin', branch],
                cwd=workspace_path,
                check=True,
                capture_output=True
            )
            print("✓ 推送成功")
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f'推送失败: {e.stderr.decode()}'
            }

        return {
            'success': True,
            'remote_url': remote_url,
            'branch': branch
        }

    def export_report(self, project_name: str, format: str = 'markdown') -> str:
        """
        导出进度报告

        Args:
            project_name: 项目名称
            format: 报告格式 (markdown, html, json)

        Returns:
            str: 报告内容
        """
        # 检查项目是否存在
        project = self.project_manager.get_project(project_name)
        if not project:
            return f"错误：项目不存在: {project_name}"

        # 获取进度数据
        tracker = ProgressTracker(project_name, self.user_id)
        statistics = tracker.get_statistics()

        if format == 'markdown':
            return self._generate_markdown_report(project, tracker, statistics)
        elif format == 'html':
            return self._generate_html_report(project, tracker, statistics)
        elif format == 'json':
            return self._generate_json_report(project, tracker, statistics)
        else:
            return f"错误：不支持的格式: {format}"

    def _generate_markdown_report(self, project, tracker, statistics) -> str:
        """生成Markdown格式报告"""
        import yaml

        # 读取项目配置
        project_config_path = self.project_manager.get_project_dir(project.project_name) / 'project.yaml'
        with open(project_config_path, 'r') as f:
            project_config = yaml.safe_load(f)

        report = []
        report.append(f"# 项目进度报告: {project.project_name}")
        report.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 项目信息
        report.append("## 项目信息\n")
        report.append(f"- **项目名称**: {project.project_name}")
        report.append(f"- **描述**: {project.description or 'N/A'}")
        report.append(f"- **语言**: {project_config.get('language', 'N/A')}")
        report.append(f"- **框架**: {project_config.get('framework', 'N/A')}")
        report.append(f"- **创建时间**: {project.created_at}")
        if project_config.get('imported_from'):
            report.append(f"- **导入来源**: {project_config['imported_from']}")
            report.append(f"- **导入源**: {project_config.get('import_source', 'N/A')}")

        # 整体进度
        report.append(f"\n## 整体进度\n")
        overall_progress = statistics['overall_progress']
        progress_bar = '█' * (overall_progress // 5) + '░' * (20 - overall_progress // 5)
        report.append(f"**{overall_progress}%** {progress_bar}\n")

        # 阶段进度
        report.append("## 阶段进度\n")
        report.append("| 阶段 | 状态 | 进度 | 负责Agent |")
        report.append("|------|------|------|-----------|")

        phases = tracker.data['phases']
        for phase in phases:
            status_icon = {
                'completed': '✅',
                'in_progress': '🔄',
                'pending': '⏳'
            }.get(phase['status'], '❓')

            report.append(f"| {phase['display_name']} | {status_icon} {phase['status']} | {phase['progress']}% | {phase['agent']} |")

        # 任务统计
        report.append(f"\n## 任务统计\n")
        tasks_summary = statistics['tasks_summary']
        report.append(f"- **已完成**: {tasks_summary['completed']}")
        report.append(f"- **进行中**: {tasks_summary['in_progress']}")
        report.append(f"- **待处理**: {tasks_summary['pending']}")
        report.append(f"- **已阻塞**: {tasks_summary['blocked']}")
        report.append(f"- **总计**: {tasks_summary['total']}")

        # 任务列表
        if tracker.data['tasks']:
            report.append(f"\n## 任务列表\n")
            for task in tracker.data['tasks']:
                status_icon = {
                    'completed': '✅',
                    'in_progress': '🔄',
                    'pending': '⏳',
                    'blocked': '🚫'
                }.get(task['status'], '❓')

                report.append(f"\n### {status_icon} {task['title']}")
                report.append(f"- **ID**: {task['id']}")
                report.append(f"- **阶段**: {task['phase']}")
                report.append(f"- **状态**: {task['status']}")
                report.append(f"- **进度**: {task['progress']}%")
                report.append(f"- **负责人**: {task['assigned_to']}")
                report.append(f"- **优先级**: {task['priority']}")

                if task.get('description'):
                    report.append(f"- **描述**: {task['description']}")

                if task.get('artifacts'):
                    report.append(f"- **产物**: {', '.join(task['artifacts'])}")

        return '\n'.join(report)

    def _generate_html_report(self, project, tracker, statistics) -> str:
        """生成HTML格式报告"""
        # 先生成Markdown，然后转换为HTML
        markdown_content = self._generate_markdown_report(project, tracker, statistics)

        # 简单的Markdown到HTML转换
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>项目进度报告: {project.project_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f5f5f5; }}
        .progress-bar {{ background: #e0e0e0; height: 20px; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ background: #4caf50; height: 100%; }}
    </style>
</head>
<body>
    <pre>{markdown_content}</pre>
</body>
</html>
"""
        return html

    def _generate_json_report(self, project, tracker, statistics) -> str:
        """生成JSON格式报告"""
        import yaml

        # 读取项目配置
        project_config_path = self.project_manager.get_project_dir(project.project_name) / 'project.yaml'
        with open(project_config_path, 'r') as f:
            project_config = yaml.safe_load(f)

        report = {
            'project': {
                'name': project.project_name,
                'description': project.description,
                'language': project_config.get('language'),
                'framework': project_config.get('framework'),
                'created_at': project.created_at,
                'imported_from': project_config.get('imported_from'),
                'import_source': project_config.get('import_source')
            },
            'progress': {
                'overall': statistics['overall_progress'],
                'phases': tracker.data['phases'],
                'tasks': tracker.data['tasks'],
                'statistics': statistics
            },
            'generated_at': datetime.now().isoformat()
        }

        return json.dumps(report, indent=2, ensure_ascii=False)
