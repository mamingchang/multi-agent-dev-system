"""
Git导入器

提供Git仓库克隆和管理功能
"""

import os
import shutil
from typing import Optional, Dict, Any
from pathlib import Path
import subprocess


class GitImporter:
    """Git仓库导入器"""

    def __init__(self, workspace_dir: str = "/tmp/imported_projects"):
        """
        初始化Git导入器

        为什么: 需要一个统一的工作空间管理导入的项目
        """
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def clone_repository(
        self,
        repo_url: str,
        project_name: str,
        branch: Optional[str] = None,
        depth: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        克隆Git仓库

        为什么: 导入外部项目的第一步是克隆代码
        """
        # 创建项目目录
        project_path = self.workspace_dir / project_name

        # 如果目录已存在，先删除
        if project_path.exists():
            shutil.rmtree(project_path)

        # 构建git clone命令
        cmd = ["git", "clone"]

        if branch:
            cmd.extend(["--branch", branch])

        if depth:
            cmd.extend(["--depth", str(depth)])

        cmd.extend([repo_url, str(project_path)])

        try:
            # 执行克隆
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")

            # 获取仓库信息
            repo_info = self._get_repository_info(project_path)

            return {
                "success": True,
                "project_path": str(project_path),
                "repo_url": repo_url,
                "branch": branch or "main",
                "info": repo_info
            }

        except subprocess.TimeoutExpired:
            raise Exception("Git clone timeout (5 minutes)")
        except Exception as e:
            raise Exception(f"Failed to clone repository: {str(e)}")

    def _get_repository_info(self, project_path: Path) -> Dict[str, Any]:
        """
        获取仓库信息

        为什么: 收集仓库的基本信息用于分析
        """
        info = {}

        try:
            # 获取当前分支
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            info["current_branch"] = result.stdout.strip()

            # 获取最新提交
            result = subprocess.run(
                ["git", "log", "-1", "--format=%H|%an|%ae|%at|%s"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            if result.stdout:
                parts = result.stdout.strip().split("|")
                info["latest_commit"] = {
                    "hash": parts[0],
                    "author": parts[1],
                    "email": parts[2],
                    "timestamp": int(parts[3]),
                    "message": parts[4]
                }

            # 获取远程URL
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            info["remote_url"] = result.stdout.strip()

            # 统计文件数量
            file_count = sum(1 for _ in project_path.rglob("*") if _.is_file())
            info["file_count"] = file_count

            # 获取项目大小
            total_size = sum(f.stat().st_size for f in project_path.rglob("*") if f.is_file())
            info["size_bytes"] = total_size
            info["size_mb"] = round(total_size / 1024 / 1024, 2)

        except Exception as e:
            info["error"] = str(e)

        return info

    def pull_updates(self, project_path: str) -> Dict[str, Any]:
        """
        拉取最新更新

        为什么: 保持导入的项目与远程同步
        """
        try:
            result = subprocess.run(
                ["git", "pull"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                raise Exception(f"Git pull failed: {result.stderr}")

            return {
                "success": True,
                "output": result.stdout
            }

        except Exception as e:
            raise Exception(f"Failed to pull updates: {str(e)}")

    def get_file_tree(self, project_path: str, max_depth: int = 3) -> Dict[str, Any]:
        """
        获取文件树结构

        为什么: 提供项目结构概览
        """
        project_path = Path(project_path)

        def build_tree(path: Path, current_depth: int = 0) -> Dict[str, Any]:
            if current_depth >= max_depth:
                return {"truncated": True}

            tree = {
                "name": path.name,
                "type": "directory" if path.is_dir() else "file",
                "path": str(path.relative_to(project_path))
            }

            if path.is_dir():
                children = []
                try:
                    for item in sorted(path.iterdir()):
                        # 跳过.git目录
                        if item.name == ".git":
                            continue
                        children.append(build_tree(item, current_depth + 1))
                    tree["children"] = children
                except PermissionError:
                    tree["error"] = "Permission denied"

            return tree

        return build_tree(project_path)

    def delete_project(self, project_name: str) -> bool:
        """
        删除导入的项目

        为什么: 清理不需要的项目释放空间
        """
        project_path = self.workspace_dir / project_name

        if project_path.exists():
            shutil.rmtree(project_path)
            return True

        return False

    def list_projects(self) -> list:
        """
        列出所有导入的项目

        为什么: 查看已导入的项目列表
        """
        projects = []

        for item in self.workspace_dir.iterdir():
            if item.is_dir() and (item / ".git").exists():
                projects.append({
                    "name": item.name,
                    "path": str(item),
                    "size_mb": round(
                        sum(f.stat().st_size for f in item.rglob("*") if f.is_file()) / 1024 / 1024,
                        2
                    )
                })

        return projects
