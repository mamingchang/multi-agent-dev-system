"""
项目导入器 - 从多种来源导入项目

支持：
- 从Git仓库导入
- 从本地目录导入
- 从项目包导入
- 从模板导入
"""
from pathlib import Path
from typing import Dict, Optional
import subprocess
import shutil
import tempfile
import zipfile
import json

from .project_analyzer import ProjectAnalyzer
from .progress_tracker import ProgressTracker
from .project_manager import ProjectManager


class ProjectImporter:
    """项目导入器"""

    def __init__(self, user_id: str):
        """
        初始化导入器

        Args:
            user_id: 用户ID
        """
        self.user_id = user_id
        self.project_manager = ProjectManager(user_id)

    def import_from_git(self, git_url: str, project_name: str,
                       branch: str = None, exclude_patterns: list = None) -> Dict:
        """
        从Git仓库导入项目

        Args:
            git_url: Git仓库URL
            project_name: 项目名称
            branch: 分支名称（可选）
            exclude_patterns: 排除的文件模式（可选）

        Returns:
            Dict: 导入结果
        """
        print(f"正在从Git导入项目: {git_url}")

        # 1. 克隆到临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            print("正在克隆仓库...")
            try:
                cmd = ['git', 'clone']
                if branch:
                    cmd.extend(['-b', branch])
                cmd.extend([git_url, str(temp_path / 'repo')])

                subprocess.run(cmd, check=True, capture_output=True)
                print("✓ 仓库克隆成功")
            except subprocess.CalledProcessError as e:
                return {
                    'success': False,
                    'error': f'Git克隆失败: {e.stderr.decode()}'
                }

            repo_path = temp_path / 'repo'

            # 2. 分析项目
            print("\n正在分析项目...")
            analyzer = ProjectAnalyzer(repo_path)
            analysis = analyzer.analyze()

            print(f"✓ 检测到语言: {analysis['language']}")
            if analysis['framework']:
                print(f"✓ 检测到框架: {analysis['framework']}")
            print(f"✓ 检测到依赖: {len(analysis['dependencies'])}个")

            # 3. 创建项目
            print("\n正在创建项目...")
            project = self.project_manager.create_project(
                project_name=project_name,
                description=f"从Git导入: {git_url}"
            )
            print(f"✓ 项目创建成功: {project_name}")

            # 4. 复制代码到workspace
            print("\n正在复制代码...")
            workspace_path = self.project_manager.get_project_workspace(project_name)

            # 排除.git目录和其他不需要的文件
            default_excludes = ['.git', '__pycache__', 'node_modules', '.env', '*.pyc']
            if exclude_patterns:
                default_excludes.extend(exclude_patterns)

            copied_count = self._copy_files(repo_path, workspace_path, default_excludes)
            print(f"✓ 已复制 {copied_count} 个文件")

            # 5. 保存项目配置
            project_config_path = self.project_manager.get_project_dir(project_name) / 'project.yaml'
            import yaml
            with open(project_config_path, 'r') as f:
                project_config = yaml.safe_load(f)

            project_config.update({
                'language': analysis['language'],
                'framework': analysis['framework'],
                'imported_from': 'git',
                'import_source': git_url,
                'import_branch': branch,
                'file_count': analysis['file_count'],
                'code_lines': analysis['code_lines']
            })

            with open(project_config_path, 'w') as f:
                yaml.dump(project_config, f, allow_unicode=True)

            # 6. 初始化进度
            print("\n正在生成初始进度...")
            tracker = ProgressTracker(project_name, self.user_id)
            tracker.initialize_from_analysis(analysis)

            completed_phases = analysis['estimated_progress']['completed_phases']
            if completed_phases:
                print(f"✓ 检测到已完成阶段: {', '.join(completed_phases)}")
            print(f"✓ 估算整体进度: {analysis['estimated_progress']['overall']}%")

            return {
                'success': True,
                'project_name': project_name,
                'workspace_path': str(workspace_path),
                'analysis': analysis,
                'progress': analysis['estimated_progress']['overall']
            }

    def import_from_dir(self, source_dir: str, project_name: str,
                       exclude_patterns: list = None) -> Dict:
        """
        从本地目录导入项目

        Args:
            source_dir: 源目录路径
            project_name: 项目名称
            exclude_patterns: 排除的文件模式（可选）

        Returns:
            Dict: 导入结果
        """
        source_path = Path(source_dir)

        if not source_path.exists():
            return {
                'success': False,
                'error': f'目录不存在: {source_dir}'
            }

        print(f"正在从本地目录导入项目: {source_dir}")

        # 1. 分析项目
        print("\n正在分析项目...")
        analyzer = ProjectAnalyzer(source_path)
        analysis = analyzer.analyze()

        print(f"✓ 检测到语言: {analysis['language']}")
        if analysis['framework']:
            print(f"✓ 检测到框架: {analysis['framework']}")
        print(f"✓ 找到 {analysis['file_count']} 个文件")

        # 2. 创建项目
        print("\n正在创建项目...")
        project = self.project_manager.create_project(
            project_name=project_name,
            description=f"从本地目录导入: {source_dir}"
        )
        print(f"✓ 项目创建成功: {project_name}")

        # 3. 复制文件
        print("\n正在复制文件...")
        workspace_path = self.project_manager.get_project_workspace(project_name)

        default_excludes = ['.git', '__pycache__', 'node_modules', '.env', '*.pyc', '*.log']
        if exclude_patterns:
            default_excludes.extend(exclude_patterns)

        copied_count = self._copy_files(source_path, workspace_path, default_excludes)
        print(f"✓ 已复制 {copied_count} 个文件")

        # 4. 保存项目配置
        project_config_path = self.project_manager.get_project_dir(project_name) / 'project.yaml'
        import yaml
        with open(project_config_path, 'r') as f:
            project_config = yaml.safe_load(f)

        project_config.update({
            'language': analysis['language'],
            'framework': analysis['framework'],
            'imported_from': 'directory',
            'import_source': source_dir,
            'file_count': analysis['file_count'],
            'code_lines': analysis['code_lines']
        })

        with open(project_config_path, 'w') as f:
            yaml.dump(project_config, f, allow_unicode=True)

        # 5. 初始化进度
        print("\n正在生成初始进度...")
        tracker = ProgressTracker(project_name, self.user_id)
        tracker.initialize_from_analysis(analysis)

        print(f"✓ 估算整体进度: {analysis['estimated_progress']['overall']}%")

        return {
            'success': True,
            'project_name': project_name,
            'workspace_path': str(workspace_path),
            'analysis': analysis,
            'progress': analysis['estimated_progress']['overall']
        }

    def import_from_package(self, package_file: str, project_name: str,
                           code_only: bool = False) -> Dict:
        """
        从项目包导入项目

        Args:
            package_file: 项目包文件路径（.mas格式）
            project_name: 项目名称
            code_only: 是否只导入代码（不导入进度和记忆）

        Returns:
            Dict: 导入结果
        """
        package_path = Path(package_file)

        if not package_path.exists():
            return {
                'success': False,
                'error': f'项目包不存在: {package_file}'
            }

        print(f"正在从项目包导入: {package_file}")

        # 1. 解压到临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            print("正在解压项目包...")
            try:
                with zipfile.ZipFile(package_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_path)
                print("✓ 解压完成")
            except Exception as e:
                return {
                    'success': False,
                    'error': f'解压失败: {str(e)}'
                }

            # 2. 读取manifest
            manifest_path = temp_path / 'manifest.json'
            if not manifest_path.exists():
                return {
                    'success': False,
                    'error': '无效的项目包：缺少manifest.json'
                }

            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

            print(f"✓ 项目包版本: {manifest['version']}")
            print(f"✓ 导出者: {manifest['exported_by']}")

            # 3. 创建项目
            print("\n正在创建项目...")
            project = self.project_manager.create_project(
                project_name=project_name,
                description=f"从项目包导入: {manifest['project_name']}"
            )
            print(f"✓ 项目创建成功: {project_name}")

            project_dir = self.project_manager.get_project_dir(project_name)

            # 4. 复制内容
            print("\n正在恢复项目内容...")

            # 复制workspace
            if (temp_path / 'workspace').exists():
                workspace_path = self.project_manager.get_project_workspace(project_name)
                shutil.copytree(temp_path / 'workspace', workspace_path, dirs_exist_ok=True)
                print("✓ 代码已恢复")

            # 复制artifacts
            if (temp_path / 'artifacts').exists():
                shutil.copytree(temp_path / 'artifacts', project_dir / 'artifacts', dirs_exist_ok=True)
                print("✓ 产物已恢复")

            # 复制docs
            if (temp_path / 'docs').exists():
                shutil.copytree(temp_path / 'docs', project_dir / 'docs', dirs_exist_ok=True)
                print("✓ 文档已恢复")

            # 复制项目配置
            if (temp_path / 'project.yaml').exists():
                shutil.copy(temp_path / 'project.yaml', project_dir / 'project.yaml')
                print("✓ 项目配置已恢复")

            # 复制进度数据（如果不是code_only）
            if not code_only and (temp_path / 'progress.yaml').exists():
                shutil.copy(temp_path / 'progress.yaml', project_dir / 'progress.yaml')
                print("✓ 进度数据已恢复")

            # 复制Agent记忆（如果不是code_only）
            if not code_only and (temp_path / 'agent_memories').exists():
                shutil.copytree(temp_path / 'agent_memories', project_dir / 'agent_memories', dirs_exist_ok=True)
                print("✓ Agent记忆已恢复")

            return {
                'success': True,
                'project_name': project_name,
                'workspace_path': str(self.project_manager.get_project_workspace(project_name)),
                'manifest': manifest
            }

    def import_from_template(self, template_name: str, project_name: str,
                            params: Dict = None) -> Dict:
        """
        从模板创建项目

        Args:
            template_name: 模板名称
            project_name: 项目名称
            params: 模板参数（如framework, language等）

        Returns:
            Dict: 导入结果
        """
        print(f"正在从模板创建项目: {template_name}")

        # 模板目录
        template_dir = Path('config') / 'project_templates' / template_name

        if not template_dir.exists():
            return {
                'success': False,
                'error': f'模板不存在: {template_name}'
            }

        # 读取模板配置
        template_config_path = template_dir / 'template.yaml'
        if not template_config_path.exists():
            return {
                'success': False,
                'error': f'模板配置不存在: {template_name}/template.yaml'
            }

        import yaml
        with open(template_config_path, 'r') as f:
            template_config = yaml.safe_load(f)

        print(f"✓ 使用模板: {template_config['name']}")
        print(f"✓ 描述: {template_config['description']}")

        # 应用参数
        if params:
            for key, value in params.items():
                print(f"✓ {key}: {value}")

        # 1. 创建项目
        print("\n正在创建项目...")
        project = self.project_manager.create_project(
            project_name=project_name,
            description=f"从模板创建: {template_name}"
        )
        print(f"✓ 项目创建成功: {project_name}")

        # 2. 复制模板文件
        print("\n正在生成项目结构...")
        workspace_path = self.project_manager.get_project_workspace(project_name)

        template_files_dir = template_dir / 'files'
        if template_files_dir.exists():
            self._copy_files(template_files_dir, workspace_path, [])
            print("✓ 项目结构已生成")

        # 3. 保存项目配置
        project_config_path = self.project_manager.get_project_dir(project_name) / 'project.yaml'
        with open(project_config_path, 'r') as f:
            project_config = yaml.safe_load(f)

        project_config.update({
            'language': params.get('language', template_config.get('default_language')),
            'framework': params.get('framework', template_config.get('default_framework')),
            'imported_from': 'template',
            'import_source': template_name,
            'template_params': params or {}
        })

        with open(project_config_path, 'w') as f:
            yaml.dump(project_config, f, allow_unicode=True)

        # 4. 初始化进度（新项目，所有阶段都是pending）
        print("\n正在初始化进度...")
        tracker = ProgressTracker(project_name, self.user_id)
        print("✓ 进度已初始化")

        return {
            'success': True,
            'project_name': project_name,
            'workspace_path': str(workspace_path),
            'template': template_name
        }

    def list_templates(self) -> list:
        """
        列出可用的项目模板

        Returns:
            list: 模板列表
        """
        templates_dir = Path('config') / 'project_templates'
        templates = []

        if templates_dir.exists():
            import yaml
            for template_dir in templates_dir.iterdir():
                if template_dir.is_dir():
                    config_path = template_dir / 'template.yaml'
                    if config_path.exists():
                        with open(config_path, 'r') as f:
                            config = yaml.safe_load(f)
                        templates.append({
                            'name': template_dir.name,
                            'display_name': config.get('name', template_dir.name),
                            'description': config.get('description', ''),
                            'language': config.get('default_language', ''),
                            'framework': config.get('default_framework', '')
                        })

        return templates

    def _copy_files(self, source: Path, dest: Path, exclude_patterns: list) -> int:
        """
        复制文件（排除指定模式）

        Args:
            source: 源目录
            dest: 目标目录
            exclude_patterns: 排除模式列表

        Returns:
            int: 复制的文件数量
        """
        import fnmatch

        dest.mkdir(parents=True, exist_ok=True)
        copied_count = 0

        for item in source.rglob('*'):
            if item.is_file():
                # 检查是否应该排除
                relative_path = item.relative_to(source)
                should_exclude = False

                for pattern in exclude_patterns:
                    # 检查路径中的任何部分是否匹配模式
                    for part in relative_path.parts:
                        if fnmatch.fnmatch(part, pattern):
                            should_exclude = True
                            break
                    if should_exclude:
                        break

                if not should_exclude:
                    target = dest / relative_path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target)
                    copied_count += 1

        return copied_count
