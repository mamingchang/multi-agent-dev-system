"""
Shell命令执行工具

提供执行系统命令的能力
"""

import subprocess
from typing import Dict, Any
from .base import Tool, ToolResult, ToolResultStatus


class BashTool(Tool):
    """
    Bash命令执行工具

    功能：执行Shell命令
    """

    def get_name(self) -> str:
        return "run_command"

    def get_description(self) -> str:
        return """执行Shell命令。

使用场景：
- 运行测试
- 安装依赖
- 编译代码
- 执行脚本

参数：
- command: 要执行的命令（必需）
- cwd: 工作目录（可选）
- timeout: 超时时间（秒，可选，默认60）

注意：危险命令需要人工批准！
"""

    def get_required_permission(self) -> str:
        """需要执行权限"""
        return "execute"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的Shell命令"
                },
                "cwd": {
                    "type": "string",
                    "description": "工作目录（可选）"
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时时间（秒）",
                    "default": 60
                }
            },
            "required": ["command"]
        }

    def execute(
        self,
        command: str,
        cwd: str = None,
        timeout: int = 60
    ) -> ToolResult:
        """
        执行Shell命令

        Args:
            command: 要执行的命令
            cwd: 工作目录
            timeout: 超时时间（秒）

        Returns:
            ToolResult: 执行结果
        """
        try:
            # 检查危险命令
            dangerous_patterns = ['rm -rf', 'dd if=', 'mkfs', '> /dev/', 'format']
            if any(pattern in command for pattern in dangerous_patterns):
                return ToolResult(
                    status=ToolResultStatus.PERMISSION_DENIED,
                    output=None,
                    error=f"危险命令需要人工批准: {command}"
                )

            # 执行命令
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # 组合stdout和stderr
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += "\n" + result.stderr

            # 判断是否成功
            if result.returncode == 0:
                return ToolResult(
                    status=ToolResultStatus.SUCCESS,
                    output=output.strip(),
                    metadata={
                        'command': command,
                        'returncode': result.returncode,
                        'cwd': cwd
                    }
                )
            else:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    output=output.strip(),
                    error=f"命令执行失败，返回码: {result.returncode}",
                    metadata={
                        'command': command,
                        'returncode': result.returncode,
                        'cwd': cwd
                    }
                )

        except subprocess.TimeoutExpired:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                output=None,
                error=f"命令执行超时（{timeout}秒）"
            )

        except Exception as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                output=None,
                error=f"命令执行失败: {str(e)}"
            )
