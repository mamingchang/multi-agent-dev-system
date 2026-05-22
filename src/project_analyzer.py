"""
项目分析器 - 分析项目结构、语言、框架等

用于导入项目时自动分析项目特征
"""
from pathlib import Path
from typing import Dict, List, Optional
import json


class ProjectAnalyzer:
    """项目分析器"""

    def __init__(self, project_path: Path):
        """
        初始化分析器

        Args:
            project_path: 项目路径
        """
        self.project_path = Path(project_path)

    def analyze(self) -> Dict:
        """
        分析项目

        Returns:
            Dict: 分析结果
                - language: 主要编程语言
                - framework: 使用的框架
                - dependencies: 依赖列表
                - structure: 目录结构分析
                - file_count: 文件数量
                - code_lines: 代码行数
                - has_tests: 是否有测试
                - has_docs: 是否有文档
                - has_deployment_config: 是否有部署配置
                - estimated_progress: 估算的进度
        """
        return {
            'language': self._detect_language(),
            'framework': self._detect_framework(),
            'dependencies': self._detect_dependencies(),
            'structure': self._analyze_structure(),
            'file_count': self._count_files(),
            'code_lines': self._count_code_lines(),
            'has_tests': self._has_tests(),
            'has_docs': self._has_docs(),
            'has_deployment_config': self._has_deployment_config(),
            'has_code': self._has_code(),
            'estimated_progress': self._estimate_progress()
        }

    def _detect_language(self) -> str:
        """
        检测主要编程语言

        Returns:
            str: 语言名称
        """
        # 统计各种语言的文件数量
        language_counts = {}

        language_extensions = {
            'Python': ['.py'],
            'JavaScript': ['.js', '.jsx'],
            'TypeScript': ['.ts', '.tsx'],
            'Java': ['.java'],
            'Go': ['.go'],
            'Rust': ['.rs'],
            'C++': ['.cpp', '.cc', '.cxx', '.hpp', '.h'],
            'C': ['.c', '.h'],
            'Ruby': ['.rb'],
            'PHP': ['.php'],
            'Swift': ['.swift'],
            'Kotlin': ['.kt'],
            'C#': ['.cs'],
        }

        for file_path in self.project_path.rglob('*'):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                for lang, exts in language_extensions.items():
                    if ext in exts:
                        language_counts[lang] = language_counts.get(lang, 0) + 1

        if not language_counts:
            return 'Unknown'

        # 返回文件数最多的语言
        return max(language_counts.items(), key=lambda x: x[1])[0]

    def _detect_framework(self) -> Optional[str]:
        """
        检测使用的框架

        Returns:
            Optional[str]: 框架名称
        """
        # 检查常见的配置文件
        framework_indicators = {
            'package.json': self._detect_js_framework,
            'requirements.txt': self._detect_python_framework,
            'Gemfile': self._detect_ruby_framework,
            'pom.xml': lambda: 'Maven',
            'build.gradle': lambda: 'Gradle',
            'Cargo.toml': lambda: 'Cargo',
            'go.mod': lambda: 'Go Modules',
        }

        for file_name, detector in framework_indicators.items():
            file_path = self.project_path / file_name
            if file_path.exists():
                result = detector() if callable(detector) else detector
                if result:
                    return result

        return None

    def _detect_js_framework(self) -> Optional[str]:
        """检测JavaScript/TypeScript框架"""
        package_json = self.project_path / 'package.json'
        if not package_json.exists():
            return None

        try:
            with open(package_json, 'r') as f:
                data = json.load(f)

            dependencies = {**data.get('dependencies', {}), **data.get('devDependencies', {})}

            # 检测框架
            if 'next' in dependencies:
                return 'Next.js'
            elif 'react' in dependencies:
                return 'React'
            elif 'vue' in dependencies:
                return 'Vue.js'
            elif 'angular' in dependencies or '@angular/core' in dependencies:
                return 'Angular'
            elif 'express' in dependencies:
                return 'Express.js'
            elif 'nestjs' in dependencies or '@nestjs/core' in dependencies:
                return 'NestJS'

        except Exception:
            pass

        return None

    def _detect_python_framework(self) -> Optional[str]:
        """检测Python框架"""
        requirements = self.project_path / 'requirements.txt'
        if not requirements.exists():
            return None

        try:
            with open(requirements, 'r') as f:
                content = f.read().lower()

            if 'django' in content:
                return 'Django'
            elif 'flask' in content:
                return 'Flask'
            elif 'fastapi' in content:
                return 'FastAPI'
            elif 'tornado' in content:
                return 'Tornado'

        except Exception:
            pass

        return None

    def _detect_ruby_framework(self) -> Optional[str]:
        """检测Ruby框架"""
        gemfile = self.project_path / 'Gemfile'
        if not gemfile.exists():
            return None

        try:
            with open(gemfile, 'r') as f:
                content = f.read().lower()

            if 'rails' in content:
                return 'Ruby on Rails'
            elif 'sinatra' in content:
                return 'Sinatra'

        except Exception:
            pass

        return None

    def _detect_dependencies(self) -> List[str]:
        """
        检测项目依赖

        Returns:
            List[str]: 依赖列表
        """
        dependencies = []

        # Python
        requirements = self.project_path / 'requirements.txt'
        if requirements.exists():
            try:
                with open(requirements, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # 提取包名（去掉版本号）
                            pkg = line.split('==')[0].split('>=')[0].split('<=')[0].strip()
                            dependencies.append(pkg)
            except Exception:
                pass

        # JavaScript/TypeScript
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                dependencies.extend(deps.keys())
            except Exception:
                pass

        return dependencies

    def _analyze_structure(self) -> Dict:
        """
        分析目录结构

        Returns:
            Dict: 结构分析
        """
        structure = {
            'has_src': (self.project_path / 'src').exists(),
            'has_tests': (self.project_path / 'tests').exists() or (self.project_path / 'test').exists(),
            'has_docs': (self.project_path / 'docs').exists() or (self.project_path / 'doc').exists(),
            'has_config': any([
                (self.project_path / 'config').exists(),
                (self.project_path / '.env').exists(),
                (self.project_path / 'config.yaml').exists(),
            ]),
            'has_scripts': (self.project_path / 'scripts').exists(),
            'has_docker': (self.project_path / 'Dockerfile').exists() or (self.project_path / 'docker-compose.yml').exists(),
            'has_ci': any([
                (self.project_path / '.github' / 'workflows').exists(),
                (self.project_path / '.gitlab-ci.yml').exists(),
                (self.project_path / '.travis.yml').exists(),
            ])
        }

        return structure

    def _count_files(self) -> int:
        """统计文件数量"""
        count = 0
        for file_path in self.project_path.rglob('*'):
            if file_path.is_file():
                # 排除常见的忽略目录
                if not any(part.startswith('.') or part in ['node_modules', '__pycache__', 'venv', 'env']
                          for part in file_path.parts):
                    count += 1
        return count

    def _count_code_lines(self) -> int:
        """统计代码行数"""
        total_lines = 0
        code_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rs',
                          '.cpp', '.c', '.rb', '.php', '.swift', '.kt', '.cs'}

        for file_path in self.project_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in code_extensions:
                # 排除常见的忽略目录
                if not any(part.startswith('.') or part in ['node_modules', '__pycache__', 'venv', 'env']
                          for part in file_path.parts):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            total_lines += sum(1 for line in f if line.strip())
                    except Exception:
                        pass

        return total_lines

    def _has_tests(self) -> bool:
        """检查是否有测试"""
        test_indicators = [
            (self.project_path / 'tests').exists(),
            (self.project_path / 'test').exists(),
            any(self.project_path.rglob('*test*.py')),
            any(self.project_path.rglob('*.test.js')),
            any(self.project_path.rglob('*.spec.js')),
        ]
        return any(test_indicators)

    def _has_docs(self) -> bool:
        """检查是否有文档"""
        doc_indicators = [
            (self.project_path / 'docs').exists(),
            (self.project_path / 'doc').exists(),
            (self.project_path / 'README.md').exists(),
            (self.project_path / 'README.rst').exists(),
        ]
        return any(doc_indicators)

    def _has_deployment_config(self) -> bool:
        """检查是否有部署配置"""
        deployment_indicators = [
            (self.project_path / 'Dockerfile').exists(),
            (self.project_path / 'docker-compose.yml').exists(),
            (self.project_path / 'kubernetes').exists(),
            (self.project_path / 'k8s').exists(),
            (self.project_path / 'deploy').exists(),
            (self.project_path / '.github' / 'workflows').exists(),
        ]
        return any(deployment_indicators)

    def _has_code(self) -> bool:
        """检查是否有代码"""
        return self._count_code_lines() > 0

    def _estimate_progress(self) -> Dict:
        """
        估算项目进度

        Returns:
            Dict: 进度估算
                - overall: 整体进度 (0-100)
                - completed_phases: 已完成的阶段列表
        """
        completed_phases = []

        # 如果有代码，说明需求分析、产品规划、架构设计已完成
        if self._has_code():
            completed_phases.extend([
                'requirement_analysis',
                'product_planning',
                'architecture_design'
            ])

        # 如果代码行数较多，说明开发已进行
        code_lines = self._count_code_lines()
        if code_lines > 1000:
            completed_phases.append('development')

        # 如果有测试，说明测试已开始
        if self._has_tests():
            if 'development' not in completed_phases:
                completed_phases.append('development')
            completed_phases.append('testing')

        # 如果有部署配置，说明部署已配置
        if self._has_deployment_config():
            if 'testing' not in completed_phases:
                completed_phases.extend(['development', 'testing'])
            completed_phases.append('code_review')

        # 计算整体进度
        total_phases = 7  # 总共7个阶段
        overall_progress = int((len(completed_phases) / total_phases) * 100)

        return {
            'overall': overall_progress,
            'completed_phases': completed_phases
        }
