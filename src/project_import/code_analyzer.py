"""
代码分析器

分析项目代码结构、依赖、技术栈
"""

import os
import json
from typing import Dict, Any, List, Set
from pathlib import Path
from collections import Counter


class CodeAnalyzer:
    """代码分析器"""

    # 编程语言文件扩展名映射
    LANGUAGE_EXTENSIONS = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".jsx": "React",
        ".tsx": "React TypeScript",
        ".java": "Java",
        ".go": "Go",
        ".rs": "Rust",
        ".cpp": "C++",
        ".c": "C",
        ".cs": "C#",
        ".rb": "Ruby",
        ".php": "PHP",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".vue": "Vue",
        ".sql": "SQL",
        ".sh": "Shell",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".json": "JSON",
        ".xml": "XML",
        ".md": "Markdown",
    }

    # 配置文件识别
    CONFIG_FILES = {
        "package.json": "Node.js",
        "requirements.txt": "Python",
        "Pipfile": "Python",
        "pyproject.toml": "Python",
        "pom.xml": "Java Maven",
        "build.gradle": "Java Gradle",
        "Cargo.toml": "Rust",
        "go.mod": "Go",
        "Gemfile": "Ruby",
        "composer.json": "PHP",
        "Dockerfile": "Docker",
        "docker-compose.yml": "Docker Compose",
        ".gitignore": "Git",
        "README.md": "Documentation",
    }

    def __init__(self):
        pass

    def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """
        分析项目

        为什么: 全面了解项目的技术栈和结构
        """
        project_path = Path(project_path)

        analysis = {
            "project_path": str(project_path),
            "languages": self._analyze_languages(project_path),
            "tech_stack": self._detect_tech_stack(project_path),
            "structure": self._analyze_structure(project_path),
            "dependencies": self._analyze_dependencies(project_path),
            "statistics": self._calculate_statistics(project_path),
        }

        return analysis

    def _analyze_languages(self, project_path: Path) -> Dict[str, Any]:
        """
        分析编程语言使用情况

        为什么: 了解项目主要使用的编程语言
        """
        language_counter = Counter()
        language_lines = Counter()

        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext in self.LANGUAGE_EXTENSIONS:
                    language = self.LANGUAGE_EXTENSIONS[ext]
                    language_counter[language] += 1

                    # 统计代码行数
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            lines = len(f.readlines())
                            language_lines[language] += lines
                    except:
                        pass

        # 计算百分比
        total_files = sum(language_counter.values())
        total_lines = sum(language_lines.values())

        languages = []
        for lang, count in language_counter.most_common():
            languages.append({
                "language": lang,
                "file_count": count,
                "file_percentage": round(count / total_files * 100, 2) if total_files > 0 else 0,
                "line_count": language_lines[lang],
                "line_percentage": round(language_lines[lang] / total_lines * 100, 2) if total_lines > 0 else 0,
            })

        return {
            "languages": languages,
            "primary_language": languages[0]["language"] if languages else "Unknown",
            "total_files": total_files,
            "total_lines": total_lines,
        }

    def _detect_tech_stack(self, project_path: Path) -> Dict[str, Any]:
        """
        检测技术栈

        为什么: 识别项目使用的框架和工具
        """
        tech_stack = {
            "frameworks": [],
            "tools": [],
            "config_files": [],
        }

        # 检查配置文件
        for file_name, tech in self.CONFIG_FILES.items():
            if (project_path / file_name).exists():
                tech_stack["config_files"].append({
                    "file": file_name,
                    "technology": tech
                })

        # 检查package.json（Node.js项目）
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, "r") as f:
                    data = json.load(f)
                    deps = list(data.get("dependencies", {}).keys())
                    dev_deps = list(data.get("devDependencies", {}).keys())

                    # 识别常见框架
                    if "react" in deps:
                        tech_stack["frameworks"].append("React")
                    if "vue" in deps:
                        tech_stack["frameworks"].append("Vue")
                    if "angular" in deps or "@angular/core" in deps:
                        tech_stack["frameworks"].append("Angular")
                    if "express" in deps:
                        tech_stack["frameworks"].append("Express")
                    if "next" in deps:
                        tech_stack["frameworks"].append("Next.js")

                    # 识别工具
                    if "webpack" in dev_deps:
                        tech_stack["tools"].append("Webpack")
                    if "vite" in dev_deps:
                        tech_stack["tools"].append("Vite")
                    if "typescript" in dev_deps:
                        tech_stack["tools"].append("TypeScript")

            except:
                pass

        # 检查requirements.txt（Python项目）
        requirements = project_path / "requirements.txt"
        if requirements.exists():
            try:
                with open(requirements, "r") as f:
                    deps = [line.split("==")[0].strip() for line in f if line.strip() and not line.startswith("#")]

                    # 识别常见框架
                    if "django" in deps:
                        tech_stack["frameworks"].append("Django")
                    if "flask" in deps:
                        tech_stack["frameworks"].append("Flask")
                    if "fastapi" in deps:
                        tech_stack["frameworks"].append("FastAPI")
                    if "sqlalchemy" in deps:
                        tech_stack["frameworks"].append("SQLAlchemy")

            except:
                pass

        return tech_stack

    def _analyze_structure(self, project_path: Path) -> Dict[str, Any]:
        """
        分析项目结构

        为什么: 了解项目的目录组织方式
        """
        structure = {
            "directories": [],
            "total_directories": 0,
            "total_files": 0,
            "max_depth": 0,
        }

        def analyze_dir(path: Path, depth: int = 0):
            structure["max_depth"] = max(structure["max_depth"], depth)

            try:
                for item in path.iterdir():
                    if item.name.startswith("."):
                        continue

                    if item.is_dir():
                        structure["total_directories"] += 1
                        file_count = sum(1 for _ in item.rglob("*") if _.is_file())

                        structure["directories"].append({
                            "name": item.name,
                            "path": str(item.relative_to(project_path)),
                            "depth": depth,
                            "file_count": file_count,
                        })

                        if depth < 2:  # 只分析前2层
                            analyze_dir(item, depth + 1)

                    elif item.is_file():
                        structure["total_files"] += 1

            except PermissionError:
                pass

        analyze_dir(project_path)

        # 按文件数量排序
        structure["directories"].sort(key=lambda x: x["file_count"], reverse=True)
        structure["directories"] = structure["directories"][:20]  # 只保留前20个

        return structure

    def _analyze_dependencies(self, project_path: Path) -> Dict[str, Any]:
        """
        分析项目依赖

        为什么: 了解项目的外部依赖
        """
        dependencies = {
            "python": [],
            "nodejs": [],
            "total_count": 0,
        }

        # Python依赖
        requirements = project_path / "requirements.txt"
        if requirements.exists():
            try:
                with open(requirements, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            dependencies["python"].append(line)
            except:
                pass

        # Node.js依赖
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, "r") as f:
                    data = json.load(f)
                    deps = data.get("dependencies", {})
                    dev_deps = data.get("devDependencies", {})

                    for name, version in deps.items():
                        dependencies["nodejs"].append(f"{name}@{version}")

                    for name, version in dev_deps.items():
                        dependencies["nodejs"].append(f"{name}@{version} (dev)")
            except:
                pass

        dependencies["total_count"] = len(dependencies["python"]) + len(dependencies["nodejs"])

        return dependencies

    def _calculate_statistics(self, project_path: Path) -> Dict[str, Any]:
        """
        计算项目统计信息

        为什么: 提供项目规模的量化指标
        """
        stats = {
            "total_files": 0,
            "total_directories": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0,
            "code_files": 0,
            "config_files": 0,
            "doc_files": 0,
        }

        for item in project_path.rglob("*"):
            if item.is_file():
                stats["total_files"] += 1
                stats["total_size_bytes"] += item.stat().st_size

                ext = item.suffix.lower()
                if ext in self.LANGUAGE_EXTENSIONS:
                    stats["code_files"] += 1
                elif ext in [".json", ".yaml", ".yml", ".toml", ".ini", ".conf"]:
                    stats["config_files"] += 1
                elif ext in [".md", ".txt", ".rst"]:
                    stats["doc_files"] += 1

            elif item.is_dir():
                stats["total_directories"] += 1

        stats["total_size_mb"] = round(stats["total_size_bytes"] / 1024 / 1024, 2)

        return stats
