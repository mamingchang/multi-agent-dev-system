"""
工具格式化器

将工具定义转换为LLM可理解的提示词
"""

from typing import List, Dict
from .tool_loader import AgentToolRegistry
from .base import Tool


class ToolFormatter:
    """
    工具格式化器

    功能：
    1. 将工具格式化为LLM提示词
    2. 生成工具使用说明
    3. 生成工具调用示例
    """

    def format_tools_for_llm(self, tool_registry: AgentToolRegistry) -> str:
        """
        将工具格式化为LLM提示词

        生成内容：
        1. 工具列表
        2. 每个工具的参数说明
        3. 工具调用格式
        4. 示例

        Args:
            tool_registry: Agent工具注册表

        Returns:
            str: 格式化后的工具说明
        """
        tools = tool_registry.list_tools()

        if not tools:
            return ""

        sections = []

        # 标题
        sections.append("## 可用工具\n")
        sections.append("你可以使用以下工具来完成任务：\n")

        # 工具列表
        for i, tool in enumerate(tools, 1):
            sections.append(self._format_single_tool(i, tool))

        # 调用格式
        sections.append(self._format_call_template())

        # 示例
        sections.append(self._format_examples(tools))

        return '\n'.join(sections)

    def _format_single_tool(self, index: int, tool: Tool) -> str:
        """
        格式化单个工具

        Args:
            index: 工具序号
            tool: 工具实例

        Returns:
            str: 格式化后的工具说明
        """
        lines = []

        lines.append(f"### {index}. {tool.get_name()}")
        lines.append(tool.get_description())
        lines.append("")

        # 参数
        params = tool.get_parameters()
        if params and 'properties' in params:
            lines.append("**参数：**")

            required = params.get('required', [])

            for param_name, param_info in params['properties'].items():
                param_type = param_info.get('type', 'any')
                param_desc = param_info.get('description', '')
                is_required = '必需' if param_name in required else '可选'
                default = param_info.get('default', '')

                param_line = f"- `{param_name}` ({param_type}, {is_required}): {param_desc}"
                if default:
                    param_line += f"，默认: {default}"

                lines.append(param_line)

            lines.append("")

        # 权限和危险标记
        permission = tool.get_required_permission()
        dangerous = tool.is_dangerous()

        if dangerous:
            lines.append("⚠️  **危险工具**：使用时需谨慎")

        lines.append(f"*权限级别: {permission}*")
        lines.append("")

        return '\n'.join(lines)

    def _format_call_template(self) -> str:
        """
        格式化调用模板

        Returns:
            str: 调用模板说明
        """
        return """## 工具调用格式

在你的JSON输出中添加 `tool_calls` 字段：

```json
{
    "analysis": "你的分析",
    "tool_calls": [
        {
            "tool": "工具名称",
            "parameters": {
                "参数名": "参数值"
            }
        }
    ],
    "output": "你的输出",
    "next_agent": "下一个Agent或null"
}
```

**重要说明：**
- `tool_calls` 是一个数组，可以包含多个工具调用
- 工具会按顺序执行
- 工具执行结果会自动添加到你的输出中的 `tool_results` 字段
- 你可以在后续处理中使用工具结果

"""

    def _format_examples(self, tools: List[Tool]) -> str:
        """
        格式化示例

        Args:
            tools: 工具列表

        Returns:
            str: 示例说明
        """
        examples = []

        examples.append("## 使用示例\n")

        tool_names = {tool.get_name() for tool in tools}

        # 示例1：读取文件
        if 'read_file' in tool_names:
            examples.append("""### 示例1：读取文件

```json
{
    "analysis": "需要读取配置文件",
    "tool_calls": [
        {
            "tool": "read_file",
            "parameters": {
                "file_path": "/path/to/config.yaml"
            }
        }
    ],
    "output": "正在读取配置文件..."
}
```
""")

        # 示例2：搜索+读取
        if 'search_files' in tool_names and 'read_file' in tool_names:
            examples.append("""### 示例2：搜索并读取文件

```json
{
    "analysis": "需要找到所有Python文件并读取",
    "tool_calls": [
        {
            "tool": "search_files",
            "parameters": {
                "pattern": "**/*.py"
            }
        },
        {
            "tool": "read_file",
            "parameters": {
                "file_path": "src/main.py"
            }
        }
    ],
    "output": "正在搜索和读取文件..."
}
```
""")

        # 示例3：写入文件
        if 'write_file' in tool_names:
            examples.append("""### 示例3：写入文件

```json
{
    "analysis": "生成代码并保存",
    "tool_calls": [
        {
            "tool": "write_file",
            "parameters": {
                "file_path": "/path/to/output.py",
                "content": "def hello():\\n    print('Hello')"
            }
        }
    ],
    "output": "代码已生成并保存"
}
```
""")

        return '\n'.join(examples)
