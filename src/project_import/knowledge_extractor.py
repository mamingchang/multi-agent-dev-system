"""
知识提取器

从项目中提取关键知识和文档
"""

from typing import Dict, Any, List
from pathlib import Path
import re


class KnowledgeExtractor:
    """知识提取器"""

    def __init__(self):
        pass

    def extract_knowledge(self, project_path: str) -> Dict[str, Any]:
        """
        提取项目知识

        为什么: 自动提取项目的关键信息和文档
        """
        project_path = Path(project_path)

        knowledge = {
            "readme": self._extract_readme(project_path),
            "api_endpoints": self._extract_api_endpoints(project_path),
            "database_models": self._extract_database_models(project_path),
            "configuration": self._extract_configuration(project_path),
            "documentation": self._extract_documentation(project_path),
        }

        return knowledge

    def _extract_readme(self, project_path: Path) -> Dict[str, Any]:
        """
        提取README内容

        为什么: README通常包含项目的核心信息
        """
        readme_files = ["README.md", "README.txt", "README.rst", "README"]

        for filename in readme_files:
            readme_path = project_path / filename
            if readme_path.exists():
                try:
                    with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                        # 提取标题
                        titles = re.findall(r"^#+\s+(.+)$", content, re.MULTILINE)

                        # 提取链接
                        links = re.findall(r"\[([^\]]+)\]\(([^\)]+)\)", content)

                        return {
                            "found": True,
                            "file": filename,
                            "content": content[:2000],  # 只保留前2000字符
                            "length": len(content),
                            "titles": titles[:10],  # 前10个标题
                            "links": [{"text": text, "url": url} for text, url in links[:10]],
                        }
                except:
                    pass

        return {"found": False}

    def _extract_api_endpoints(self, project_path: Path) -> List[Dict[str, Any]]:
        """
        提取API端点

        为什么: 了解项目提供的API接口
        """
        endpoints = []

        # 搜索Python FastAPI/Flask路由
        for py_file in project_path.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                    # FastAPI路由
                    fastapi_routes = re.findall(
                        r'@(?:router|app)\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
                        content
                    )
                    for method, path in fastapi_routes:
                        endpoints.append({
                            "method": method.upper(),
                            "path": path,
                            "file": str(py_file.relative_to(project_path)),
                            "framework": "FastAPI"
                        })

                    # Flask路由
                    flask_routes = re.findall(
                        r'@app\.route\(["\']([^"\']+)["\'].*methods=\[([^\]]+)\]',
                        content
                    )
                    for path, methods in flask_routes:
                        for method in methods.split(","):
                            method = method.strip().strip('"\'')
                            endpoints.append({
                                "method": method,
                                "path": path,
                                "file": str(py_file.relative_to(project_path)),
                                "framework": "Flask"
                            })

            except:
                pass

        # 搜索JavaScript/TypeScript Express路由
        for js_file in project_path.rglob("*.js"):
            try:
                with open(js_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                    # Express路由
                    express_routes = re.findall(
                        r'(?:router|app)\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
                        content
                    )
                    for method, path in express_routes:
                        endpoints.append({
                            "method": method.upper(),
                            "path": path,
                            "file": str(js_file.relative_to(project_path)),
                            "framework": "Express"
                        })

            except:
                pass

        return endpoints[:50]  # 限制返回数量

    def _extract_database_models(self, project_path: Path) -> List[Dict[str, Any]]:
        """
        提取数据库模型

        为什么: 了解项目的数据结构
        """
        models = []

        # 搜索Python SQLAlchemy模型
        for py_file in project_path.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                    # SQLAlchemy模型
                    model_classes = re.findall(
                        r'class\s+(\w+)\(.*Base.*\):',
                        content
                    )

                    for model_name in model_classes:
                        # 尝试提取表名
                        table_match = re.search(
                            rf'class\s+{model_name}.*?__tablename__\s*=\s*["\'](\w+)["\']',
                            content,
                            re.DOTALL
                        )
                        table_name = table_match.group(1) if table_match else model_name.lower()

                        models.append({
                            "name": model_name,
                            "table": table_name,
                            "file": str(py_file.relative_to(project_path)),
                            "orm": "SQLAlchemy"
                        })

            except:
                pass

        return models[:30]  # 限制返回数量

    def _extract_configuration(self, project_path: Path) -> Dict[str, Any]:
        """
        提取配置信息

        为什么: 了解项目的配置方式
        """
        config = {
            "env_variables": [],
            "config_files": [],
        }

        # 提取.env.example或.env文件
        for env_file in [".env.example", ".env.sample", ".env"]:
            env_path = project_path / env_file
            if env_path.exists():
                try:
                    with open(env_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                key = line.split("=")[0].strip()
                                config["env_variables"].append(key)
                except:
                    pass

        # 列出配置文件
        config_patterns = ["config.*", "*.config.*", "settings.*"]
        for pattern in config_patterns:
            for config_file in project_path.rglob(pattern):
                if config_file.is_file():
                    config["config_files"].append(str(config_file.relative_to(project_path)))

        config["config_files"] = config["config_files"][:20]  # 限制数量

        return config

    def _extract_documentation(self, project_path: Path) -> Dict[str, Any]:
        """
        提取文档

        为什么: 收集项目的文档资源
        """
        docs = {
            "markdown_files": [],
            "doc_directories": [],
        }

        # 查找Markdown文件
        for md_file in project_path.rglob("*.md"):
            if md_file.name != "README.md":  # README已单独处理
                docs["markdown_files"].append({
                    "name": md_file.name,
                    "path": str(md_file.relative_to(project_path)),
                    "size_kb": round(md_file.stat().st_size / 1024, 2)
                })

        # 查找文档目录
        doc_dir_names = ["docs", "doc", "documentation", "wiki"]
        for dir_name in doc_dir_names:
            for doc_dir in project_path.rglob(dir_name):
                if doc_dir.is_dir():
                    file_count = sum(1 for _ in doc_dir.rglob("*") if _.is_file())
                    docs["doc_directories"].append({
                        "name": doc_dir.name,
                        "path": str(doc_dir.relative_to(project_path)),
                        "file_count": file_count
                    })

        docs["markdown_files"] = docs["markdown_files"][:20]  # 限制数量

        return docs

    def generate_summary(self, knowledge: Dict[str, Any]) -> str:
        """
        生成项目摘要

        为什么: 提供项目的简洁概述
        """
        summary_parts = []

        # README摘要
        if knowledge["readme"]["found"]:
            summary_parts.append(f"📄 README: {knowledge['readme']['file']} ({knowledge['readme']['length']} chars)")

        # API端点摘要
        if knowledge["api_endpoints"]:
            summary_parts.append(f"🌐 API Endpoints: {len(knowledge['api_endpoints'])} found")

        # 数据库模型摘要
        if knowledge["database_models"]:
            summary_parts.append(f"🗄️ Database Models: {len(knowledge['database_models'])} found")

        # 配置摘要
        if knowledge["configuration"]["env_variables"]:
            summary_parts.append(f"⚙️ Environment Variables: {len(knowledge['configuration']['env_variables'])} found")

        # 文档摘要
        if knowledge["documentation"]["markdown_files"]:
            summary_parts.append(f"📚 Documentation: {len(knowledge['documentation']['markdown_files'])} markdown files")

        return "\n".join(summary_parts) if summary_parts else "No significant knowledge extracted"
