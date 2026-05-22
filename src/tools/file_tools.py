"""
文件操作工具

提供读取、写入、编辑文件的能力
"""

import os
from typing import Dict, Any
from .base import Tool, ToolResult, ToolResultStatus


class ReadTool(Tool):
    """
    读取文件工具

    功能：读取指定路径的文件内容
    """

    def get_name(self) -> str:
        return "read_file"

    def get_description(self) -> str:
        return """读取文件内容。

使用场景：
- 查看现有代码
- 读取配置文件
- 检查文档内容

参数：
- file_path: 文件路径（必需）
- encoding: 文件编码（可选，默认utf-8）
"""

    def get_required_permission(self) -> str:
        """需要读取权限"""
        return "read"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "要读取的文件路径"
                },
                "encoding": {
                    "type": "string",
                    "description": "文件编码",
                    "default": "utf-8"
                }
            },
            "required": ["file_path"]
        }

    def execute(self, file_path: str, encoding: str = "utf-8") -> ToolResult:
        """
        执行文件读取

        Args:
            file_path: 文件路径
            encoding: 文件编码

        Returns:
            ToolResult: 包含文件内容的结果
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    output=None,
                    error=f"文件不存在: {file_path}"
                )

            # 检查是否是文件
            if not os.path.isfile(file_path):
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    output=None,
                    error=f"不是文件: {file_path}"
                )

            # 读取文件
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()

            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                output=content,
                metadata={
                    'file_path': file_path,
                    'size': len(content),
                    'lines': content.count('\n') + 1
                }
            )

        except PermissionError:
            return ToolResult(
                status=ToolResultStatus.PERMISSION_DENIED,
                output=None,
                error=f"没有权限读取文件: {file_path}"
            )

        except Exception as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                output=None,
                error=f"读取文件失败: {str(e)}"
            )


class WriteTool(Tool):
    """
    写入文件工具

    功能：将内容写入指定路径的文件
    """

    def get_name(self) -> str:
        return "write_file"

    def get_description(self) -> str:
        return """写入文件内容。

使用场景：
- 创建新文件
- 完全覆盖现有文件
- 追加内容到文件末尾

参数：
- file_path: 文件路径（必需）
- content: 文件内容（必需）
- encoding: 文件编码（可选，默认utf-8）
- mode: 写入模式（可选，默认'write'，可选'append'）

注意：mode='write'会覆盖现有文件，mode='append'会追加到末尾！
"""

    def get_required_permission(self) -> str:
        """需要写入权限"""
        return "write"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "要写入的文件路径"
                },
                "content": {
                    "type": "string",
                    "description": "文件内容"
                },
                "encoding": {
                    "type": "string",
                    "description": "文件编码",
                    "default": "utf-8"
                },
                "mode": {
                    "type": "string",
                    "description": "写入模式：'write'覆盖，'append'追加",
                    "default": "write",
                    "enum": ["write", "append"]
                }
            },
            "required": ["file_path", "content"]
        }

    def execute(self, file_path: str, content: str, encoding: str = "utf-8", mode: str = "write") -> ToolResult:
        """
        执行文件写入

        Args:
            file_path: 文件路径
            content: 文件内容
            encoding: 文件编码
            mode: 写入模式（'write'覆盖，'append'追加）

        Returns:
            ToolResult: 写入结果
        """
        try:
            # 确保目录存在
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            # 根据模式写入文件
            file_mode = 'a' if mode == 'append' else 'w'
            with open(file_path, file_mode, encoding=encoding) as f:
                f.write(content)

            action = "追加" if mode == 'append' else "写入"
            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                output=f"文件已{action}: {file_path}",
                metadata={
                    'file_path': file_path,
                    'size': len(content),
                    'lines': content.count('\n') + 1,
                    'mode': mode
                }
            )

        except PermissionError:
            return ToolResult(
                status=ToolResultStatus.PERMISSION_DENIED,
                output=None,
                error=f"没有权限写入文件: {file_path}"
            )

        except Exception as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                output=None,
                error=f"写入文件失败: {str(e)}"
            )


class EditTool(Tool):
    """
    编辑文件工具

    功能：替换文件中的指定内容
    """

    def get_name(self) -> str:
        return "edit_file"

    def get_description(self) -> str:
        return """编辑文件内容（字符串替换）。

使用场景：
- 修改现有代码
- 替换配置项
- 更新文档

参数：
- file_path: 文件路径（必需）
- old_string: 要替换的旧字符串（必需）
- new_string: 替换后的新字符串（必需）
- replace_all: 是否替换所有匹配（可选，默认False）

注意：old_string必须在文件中唯一，否则会失败！
"""

    def get_required_permission(self) -> str:
        """需要写入权限"""
        return "write"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "要编辑的文件路径"
                },
                "old_string": {
                    "type": "string",
                    "description": "要替换的旧字符串"
                },
                "new_string": {
                    "type": "string",
                    "description": "替换后的新字符串"
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "是否替换所有匹配",
                    "default": False
                }
            },
            "required": ["file_path", "old_string", "new_string"]
        }

    def execute(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False
    ) -> ToolResult:
        """
        执行文件编辑

        Args:
            file_path: 文件路径
            old_string: 要替换的旧字符串
            new_string: 替换后的新字符串
            replace_all: 是否替换所有匹配

        Returns:
            ToolResult: 编辑结果
        """
        try:
            # 读取文件
            if not os.path.exists(file_path):
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    output=None,
                    error=f"文件不存在: {file_path}"
                )

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查old_string是否存在
            if old_string not in content:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    output=None,
                    error=f"未找到要替换的字符串"
                )

            # 检查是否唯一（如果不是replace_all）
            if not replace_all and content.count(old_string) > 1:
                return ToolResult(
                    status=ToolResultStatus.ERROR,
                    output=None,
                    error=f"字符串不唯一，出现{content.count(old_string)}次。请使用replace_all=True或提供更具体的字符串"
                )

            # 替换
            if replace_all:
                new_content = content.replace(old_string, new_string)
                count = content.count(old_string)
            else:
                new_content = content.replace(old_string, new_string, 1)
                count = 1

            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                output=f"文件已编辑: {file_path}",
                metadata={
                    'file_path': file_path,
                    'replacements': count
                }
            )

        except PermissionError:
            return ToolResult(
                status=ToolResultStatus.PERMISSION_DENIED,
                output=None,
                error=f"没有权限编辑文件: {file_path}"
            )

        except Exception as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                output=None,
                error=f"编辑文件失败: {str(e)}"
            )
