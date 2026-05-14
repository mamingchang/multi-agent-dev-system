"""
项目代码管理器

统一管理所有项目的代码存储，无论是导入的还是新建的
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
import subprocess


class ProjectCodeManager:
    """
    项目代码管理器

    设计原则：
    1. 所有项目代码统一存储在 workspace_root 下
    2. 目录结构：workspace_root/org_{org_id}/project_{project_id}/
    3. 支持Git仓库和普通目录
    4. 提供统一的代码操作接口
    """

    def __init__(self, workspace_root: str = None):
        """
        初始化代码管理器

        Args:
            workspace_root: 项目代码根目录，默认为项目根目录下的 projects/
        """
        if workspace_root is None:
            # 默认使用项目根目录下的 projects/ 目录
            import os
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            workspace_root = os.path.join(current_dir, "projects")

        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def get_project_path(self, organization_id: int, project_id: int) -> Path:
        """
        获取项目代码路径

        Args:
            organization_id: 组织ID
            project_id: 项目ID

        Returns:
            Path: 项目代码路径
        """
        org_dir = self.workspace_root / f"org_{organization_id}"
        project_dir = org_dir / f"project_{project_id}"
        return project_dir

    def create_project_directory(
        self,
        organization_id: int,
        project_id: int,
        project_name: str
    ) -> str:
        """
        创建项目目录（用于手动创建的项目）

        Args:
            organization_id: 组织ID
            project_id: 项目ID
            project_name: 项目名称

        Returns:
            str: 项目代码路径
        """
        project_path = self.get_project_path(organization_id, project_id)

        # 创建目录
        project_path.mkdir(parents=True, exist_ok=True)

        # 创建基本的项目结构
        (project_path / "src").mkdir(exist_ok=True)
        (project_path / "docs").mkdir(exist_ok=True)
        (project_path / "tests").mkdir(exist_ok=True)

        # 创建README
        readme_path = project_path / "README.md"
        readme_path.write_text(f"# {project_name}\n\n项目描述\n")

        # 初始化Git仓库（可选）
        try:
            subprocess.run(
                ["git", "init"],
                cwd=project_path,
                capture_output=True,
                check=True
            )
            # 创建.gitignore
            gitignore_path = project_path / ".gitignore"
            gitignore_path.write_text(
                "*.pyc\n__pycache__/\n.env\n.venv/\nnode_modules/\n.DS_Store\n"
            )
        except Exception as e:
            print(f"Warning: Failed to initialize git: {e}")

        return str(project_path)

    def clone_repository(
        self,
        organization_id: int,
        project_id: int,
        repo_url: str,
        branch: Optional[str] = None,
        depth: Optional[int] = 1
    ) -> Dict[str, Any]:
        """
        克隆Git仓库到项目目录

        Args:
            organization_id: 组织ID
            project_id: 项目ID
            repo_url: Git仓库URL
            branch: 分支名称
            depth: 克隆深度

        Returns:
            Dict: 克隆结果
        """
        project_path = self.get_project_path(organization_id, project_id)

        # 如果目录已存在，先删除
        if project_path.exists():
            shutil.rmtree(project_path)

        # 确保父目录存在
        project_path.parent.mkdir(parents=True, exist_ok=True)

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
                "branch": branch or repo_info.get("current_branch", "main"),
                "info": repo_info
            }

        except subprocess.TimeoutExpired:
            raise Exception("Git clone timeout (5 minutes)")
        except Exception as e:
            # 清理失败的克隆
            if project_path.exists():
                shutil.rmtree(project_path)
            raise Exception(f"Failed to clone repository: {str(e)}")

    def _get_repository_info(self, project_path: Path) -> Dict[str, Any]:
        """
        获取Git仓库信息

        Args:
            project_path: 项目路径

        Returns:
            Dict: 仓库信息
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
                ["git", "log", "-1", "--format=%H|%an|%ae|%s"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            if result.stdout:
                parts = result.stdout.strip().split("|")
                if len(parts) == 4:
                    info["latest_commit"] = {
                        "hash": parts[0],
                        "author": parts[1],
                        "email": parts[2],
                        "message": parts[3]
                    }

            # 获取远程URL
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            info["remote_url"] = result.stdout.strip()

        except Exception as e:
            print(f"Warning: Failed to get repository info: {e}")

        return info

    def pull_updates(
        self,
        organization_id: int,
        project_id: int
    ) -> Dict[str, Any]:
        """
        拉取项目更新

        Args:
            organization_id: 组织ID
            project_id: 项目ID

        Returns:
            Dict: 拉取结果
        """
        project_path = self.get_project_path(organization_id, project_id)

        if not project_path.exists():
            raise Exception("Project directory does not exist")

        # 检查是否是Git仓库
        if not (project_path / ".git").exists():
            raise Exception("Not a git repository")

        try:
            # 执行git pull
            result = subprocess.run(
                ["git", "pull"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                raise Exception(f"Git pull failed: {result.stderr}")

            # 获取更新后的信息
            repo_info = self._get_repository_info(project_path)

            return {
                "success": True,
                "message": result.stdout.strip(),
                "info": repo_info
            }

        except subprocess.TimeoutExpired:
            raise Exception("Git pull timeout (5 minutes)")
        except Exception as e:
            raise Exception(f"Failed to pull updates: {str(e)}")

    def delete_project_code(
        self,
        organization_id: int,
        project_id: int
    ) -> bool:
        """
        删除项目代码

        Args:
            organization_id: 组织ID
            project_id: 项目ID

        Returns:
            bool: 是否成功
        """
        project_path = self.get_project_path(organization_id, project_id)

        if project_path.exists():
            try:
                shutil.rmtree(project_path)
                return True
            except Exception as e:
                print(f"Failed to delete project code: {e}")
                return False

        return True

    def get_project_stats(
        self,
        organization_id: int,
        project_id: int
    ) -> Dict[str, Any]:
        """
        获取项目统计信息

        Args:
            organization_id: 组织ID
            project_id: 项目ID

        Returns:
            Dict: 统计信息
        """
        project_path = self.get_project_path(organization_id, project_id)

        if not project_path.exists():
            return {"exists": False}

        stats = {
            "exists": True,
            "path": str(project_path),
            "is_git_repo": (project_path / ".git").exists()
        }

        # 统计文件数量
        try:
            file_count = sum(1 for _ in project_path.rglob("*") if _.is_file())
            stats["file_count"] = file_count

            # 统计代码行数（简单统计）
            code_extensions = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs"}
            code_lines = 0
            for file_path in project_path.rglob("*"):
                if file_path.is_file() and file_path.suffix in code_extensions:
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            code_lines += sum(1 for _ in f)
                    except:
                        pass
            stats["code_lines"] = code_lines

        except Exception as e:
            print(f"Warning: Failed to get project stats: {e}")

        return stats

    def list_files(
        self,
        organization_id: int,
        project_id: int,
        relative_path: str = ""
    ) -> list:
        """
        列出项目文件

        Args:
            organization_id: 组织ID
            project_id: 项目ID
            relative_path: 相对路径

        Returns:
            list: 文件列表
        """
        project_path = self.get_project_path(organization_id, project_id)
        target_path = project_path / relative_path

        if not target_path.exists():
            return []

        files = []
        try:
            for item in target_path.iterdir():
                files.append({
                    "name": item.name,
                    "path": str(item.relative_to(project_path)),
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else 0
                })
        except Exception as e:
            print(f"Failed to list files: {e}")

        return files

    def read_file(
        self,
        organization_id: int,
        project_id: int,
        file_path: str
    ) -> str:
        """
        读取项目文件内容

        Args:
            organization_id: 组织ID
            project_id: 项目ID
            file_path: 文件相对路径

        Returns:
            str: 文件内容
        """
        project_path = self.get_project_path(organization_id, project_id)
        target_file = project_path / file_path

        if not target_file.exists() or not target_file.is_file():
            raise Exception("File not found")

        # 安全检查：确保文件在项目目录内
        if not str(target_file.resolve()).startswith(str(project_path.resolve())):
            raise Exception("Access denied: file outside project directory")

        try:
            with open(target_file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Failed to read file: {str(e)}")

    def write_file(
        self,
        organization_id: int,
        project_id: int,
        file_path: str,
        content: str
    ) -> bool:
        """
        写入项目文件

        Args:
            organization_id: 组织ID
            project_id: 项目ID
            file_path: 文件相对路径
            content: 文件内容

        Returns:
            bool: 是否成功
        """
        project_path = self.get_project_path(organization_id, project_id)
        target_file = project_path / file_path

        # 安全检查：确保文件在项目目录内
        if not str(target_file.resolve()).startswith(str(project_path.resolve())):
            raise Exception("Access denied: file outside project directory")

        try:
            # 确保父目录存在
            target_file.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(content)

            return True
        except Exception as e:
            raise Exception(f"Failed to write file: {str(e)}")
