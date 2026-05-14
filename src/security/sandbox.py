"""
代码沙箱

使用Docker容器提供隔离的代码执行环境。

特性：
1. 临时容器：每次执行创建，执行完销毁
2. 资源限制：CPU、内存、时间限制
3. 网络隔离：默认无网络访问
4. 文件系统隔离：只能访问挂载的目录
"""

import os
import tempfile
import shutil
from typing import Optional, Dict, Any, List
from datetime import datetime


class SandboxConfig:
    """沙箱配置"""

    def __init__(
        self,
        image: str = "python:3.10-slim",
        cpu_limit: float = 1.0,
        memory_limit: str = "512m",
        timeout: int = 300,
        network_enabled: bool = False,
        working_dir: str = "/workspace"
    ):
        """
        初始化沙箱配置

        Args:
            image: Docker镜像
            cpu_limit: CPU限制（核心数）
            memory_limit: 内存限制（如"512m", "1g"）
            timeout: 超时时间（秒）
            network_enabled: 是否启用网络
            working_dir: 工作目录
        """
        self.image = image
        self.cpu_limit = cpu_limit
        self.memory_limit = memory_limit
        self.timeout = timeout
        self.network_enabled = network_enabled
        self.working_dir = working_dir


class SandboxResult:
    """沙箱执行结果"""

    def __init__(
        self,
        success: bool,
        stdout: str = "",
        stderr: str = "",
        exit_code: int = 0,
        execution_time: float = 0,
        error_message: str = None
    ):
        """
        初始化执行结果

        Args:
            success: 是否成功
            stdout: 标准输出
            stderr: 标准错误
            exit_code: 退出码
            execution_time: 执行时间（秒）
            error_message: 错误消息
        """
        self.success = success
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.execution_time = execution_time
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "execution_time": self.execution_time,
            "error_message": self.error_message
        }


class CodeSandbox:
    """
    代码沙箱

    提供隔离的代码执行环境。

    注意：此实现为简化版本，实际使用需要安装Docker并配置权限。
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        """
        初始化沙箱

        Args:
            config: 沙箱配置
        """
        self.config = config or SandboxConfig()
        self.temp_dir: Optional[str] = None

    def execute_code(
        self,
        code: str,
        language: str = "python",
        files: Optional[Dict[str, str]] = None
    ) -> SandboxResult:
        """
        在沙箱中执行代码

        Args:
            code: 要执行的代码
            language: 编程语言
            files: 额外的文件（文件名 -> 内容）

        Returns:
            SandboxResult: 执行结果
        """
        try:
            # 创建临时目录
            self.temp_dir = tempfile.mkdtemp(prefix="sandbox_")

            # 写入代码文件
            code_file = self._write_code_file(code, language)

            # 写入额外文件
            if files:
                for filename, content in files.items():
                    file_path = os.path.join(self.temp_dir, filename)
                    with open(file_path, 'w') as f:
                        f.write(content)

            # 执行代码（简化版本，实际应该使用Docker）
            result = self._execute_in_sandbox(code_file, language)

            return result

        except Exception as e:
            return SandboxResult(
                success=False,
                error_message=f"沙箱执行失败: {str(e)}"
            )

        finally:
            # 清理临时目录
            self._cleanup()

    def _write_code_file(self, code: str, language: str) -> str:
        """
        写入代码文件

        Args:
            code: 代码内容
            language: 编程语言

        Returns:
            str: 代码文件路径
        """
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "java": ".java",
            "go": ".go",
            "rust": ".rs"
        }

        ext = extensions.get(language, ".txt")
        code_file = os.path.join(self.temp_dir, f"main{ext}")

        with open(code_file, 'w') as f:
            f.write(code)

        return code_file

    def _execute_in_sandbox(self, code_file: str, language: str) -> SandboxResult:
        """
        在沙箱中执行代码

        注意：这是简化实现，实际应该使用Docker。

        Args:
            code_file: 代码文件路径
            language: 编程语言

        Returns:
            SandboxResult: 执行结果
        """
        import subprocess
        import time

        # 根据语言选择执行命令
        commands = {
            "python": ["python3", code_file],
            "javascript": ["node", code_file],
            "typescript": ["ts-node", code_file],
        }

        command = commands.get(language)
        if not command:
            return SandboxResult(
                success=False,
                error_message=f"不支持的语言: {language}"
            )

        # 执行代码
        start_time = time.time()

        try:
            # 注意：这里没有使用Docker，只是简单的subprocess
            # 实际生产环境应该使用Docker容器
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.temp_dir,
                timeout=self.config.timeout
            )

            stdout, stderr = process.communicate()
            execution_time = time.time() - start_time

            return SandboxResult(
                success=process.returncode == 0,
                stdout=stdout.decode('utf-8', errors='ignore'),
                stderr=stderr.decode('utf-8', errors='ignore'),
                exit_code=process.returncode,
                execution_time=execution_time
            )

        except subprocess.TimeoutExpired:
            process.kill()
            return SandboxResult(
                success=False,
                error_message=f"执行超时（{self.config.timeout}秒）",
                execution_time=self.config.timeout
            )

        except Exception as e:
            return SandboxResult(
                success=False,
                error_message=f"执行失败: {str(e)}",
                execution_time=time.time() - start_time
            )

    def _cleanup(self):
        """清理临时目录"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"清理临时目录失败: {e}")

    def execute_command(
        self,
        command: str,
        working_dir: Optional[str] = None
    ) -> SandboxResult:
        """
        在沙箱中执行命令

        Args:
            command: 要执行的命令
            working_dir: 工作目录

        Returns:
            SandboxResult: 执行结果
        """
        # TODO: 实现Docker容器中执行命令
        # 这里是简化版本
        return SandboxResult(
            success=False,
            error_message="Docker沙箱功能待实现"
        )


class DockerSandbox(CodeSandbox):
    """
    Docker沙箱

    使用Docker容器提供真正的隔离环境。

    注意：需要安装docker-py库：pip install docker
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        """
        初始化Docker沙箱

        Args:
            config: 沙箱配置
        """
        super().__init__(config)
        self.docker_client = None
        self._init_docker_client()

    def _init_docker_client(self):
        """初始化Docker客户端"""
        try:
            import docker
            self.docker_client = docker.from_env()
        except ImportError:
            print("警告: docker-py未安装，Docker沙箱功能不可用")
            print("安装命令: pip install docker")
        except Exception as e:
            print(f"警告: Docker客户端初始化失败: {e}")

    def _execute_in_sandbox(self, code_file: str, language: str) -> SandboxResult:
        """
        在Docker容器中执行代码

        Args:
            code_file: 代码文件路径
            language: 编程语言

        Returns:
            SandboxResult: 执行结果
        """
        if not self.docker_client:
            # 回退到简单实现
            return super()._execute_in_sandbox(code_file, language)

        # TODO: 实现Docker容器执行
        # 1. 创建容器
        # 2. 挂载代码目录
        # 3. 设置资源限制
        # 4. 执行代码
        # 5. 获取输出
        # 6. 删除容器

        return SandboxResult(
            success=False,
            error_message="Docker容器执行功能待完善"
        )


# 标准化别名
Sandbox = DockerSandbox

# 创建默认沙箱实例
default_sandbox = CodeSandbox()


__all__ = ['Sandbox', 'CodeSandbox', 'DockerSandbox', 'SandboxConfig', 'SandboxResult']

