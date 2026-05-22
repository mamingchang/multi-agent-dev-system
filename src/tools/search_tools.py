"""
代码搜索工具

提供搜索文件和代码的能力
"""

import os
import glob
import re
from typing import Dict, Any, List
from .base import Tool, ToolResult, ToolResultStatus


class GlobTool(Tool):
    """
    文件搜索工具（通配符匹配）

    功能：根据通配符模式搜索文件
    """

    def get_name(self) -> str:
        return "search_files"

    def get_description(self) -> str:
        return """搜索文件（通配符匹配）。

使用场景：
- 查找特定类型的文件
- 查找特定目录下的文件

参数：
- pattern: 通配符模式（必需），如"*.py"、"src/**/*.js"
- path: 搜索路径（可选，默认当前目录）

示例：
- "*.py" - 当前目录下所有Python文件
- "src/**/*.js" - src目录下所有JavaScript文件（递归）
"""

    def get_required_permission(self) -> str:
        """需要搜索权限"""
        return "search"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "通配符模式"
                },
                "path": {
                    "type": "string",
                    "description": "搜索路径",
                    "default": "."
                }
            },
            "required": ["pattern"]
        }

    def execute(self, pattern: str, path: str = ".") -> ToolResult:
        """
        执行文件搜索

        Args:
            pattern: 通配符模式
            path: 搜索路径

        Returns:
            ToolResult: 搜索结果
        """
        try:
            # 构建完整路径
            full_pattern = os.path.join(path, pattern)

            # 搜索文件
            files = glob.glob(full_pattern, recursive=True)

            # 过滤掉目录，只保留文件
            files = [f for f in files if os.path.isfile(f)]

            # 排序
            files.sort()

            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                output=files,
                metadata={
                    'pattern': pattern,
                    'path': path,
                    'count': len(files)
                }
            )

        except Exception as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                output=None,
                error=f"搜索文件失败: {str(e)}"
            )


class GrepTool(Tool):
    """
    代码搜索工具（正则表达式）

    功能：在文件中搜索匹配的内容
    """

    def get_name(self) -> str:
        return "search_code"

    def get_description(self) -> str:
        return """搜索代码（正则表达式）。

使用场景：
- 查找函数定义
- 查找变量使用
- 查找特定字符串

参数：
- pattern: 正则表达式模式（必需）
- path: 搜索路径（可选，默认当前目录）
- file_pattern: 文件过滤（可选，如"*.py"）
- max_results: 最大结果数（可选，默认100）

示例：
- pattern="def login" - 查找login函数定义
- pattern="TODO" - 查找所有TODO注释
"""

    def get_required_permission(self) -> str:
        """需要搜索权限"""
        return "search"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "正则表达式模式"
                },
                "path": {
                    "type": "string",
                    "description": "搜索路径",
                    "default": "."
                },
                "file_pattern": {
                    "type": "string",
                    "description": "文件过滤（通配符）",
                    "default": "*"
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大结果数",
                    "default": 100
                }
            },
            "required": ["pattern"]
        }

    def execute(
        self,
        pattern: str,
        path: str = ".",
        file_pattern: str = "*",
        max_results: int = 100
    ) -> ToolResult:
        """
        执行代码搜索

        Args:
            pattern: 正则表达式模式
            path: 搜索路径
            file_pattern: 文件过滤
            max_results: 最大结果数

        Returns:
            ToolResult: 搜索结果
        """
        try:
            # 编译正则表达式
            regex = re.compile(pattern)

            # 搜索文件
            files = glob.glob(
                os.path.join(path, "**", file_pattern),
                recursive=True
            )

            # 只保留文件
            files = [f for f in files if os.path.isfile(f)]

            # 搜索结果
            results = []

            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            if regex.search(line):
                                results.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'content': line.strip()
                                })

                                # 达到最大结果数
                                if len(results) >= max_results:
                                    break

                except Exception:
                    # 跳过无法读取的文件
                    continue

                # 达到最大结果数
                if len(results) >= max_results:
                    break

            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                output=results,
                metadata={
                    'pattern': pattern,
                    'path': path,
                    'file_pattern': file_pattern,
                    'count': len(results),
                    'truncated': len(results) >= max_results
                }
            )

        except re.error as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                output=None,
                error=f"正则表达式错误: {str(e)}"
            )

        except Exception as e:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                output=None,
                error=f"搜索代码失败: {str(e)}"
            )
