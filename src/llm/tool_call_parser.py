"""
工具调用解析器

从LLM输出中解析工具调用请求
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ToolCall:
    """
    工具调用

    表示一个工具调用请求
    """
    tool_name: str
    parameters: Dict[str, Any]
    call_id: Optional[str] = None  # 用于追踪多个工具调用


@dataclass
class ToolCallParseResult:
    """
    工具调用解析结果

    包含解析成功的工具调用列表和错误信息
    """
    success: bool
    tool_calls: List[ToolCall]
    errors: List[str]


class ToolCallParser:
    """
    工具调用解析器

    功能：
    1. 从LLM输出中提取tool_calls字段
    2. 验证工具调用格式
    3. 验证参数格式
    4. 处理解析错误
    """

    def parse_tool_calls(self, llm_output: Dict) -> ToolCallParseResult:
        """
        解析工具调用

        Args:
            llm_output: LLM的JSON输出

        Returns:
            ToolCallParseResult: 解析结果
        """
        errors = []
        tool_calls = []

        # 检查是否有tool_calls字段
        if 'tool_calls' not in llm_output:
            return ToolCallParseResult(
                success=True,
                tool_calls=[],
                errors=[]
            )

        raw_tool_calls = llm_output['tool_calls']

        # 验证tool_calls是列表
        if not isinstance(raw_tool_calls, list):
            errors.append("tool_calls必须是数组")
            return ToolCallParseResult(
                success=False,
                tool_calls=[],
                errors=errors
            )

        # 解析每个工具调用
        for i, raw_call in enumerate(raw_tool_calls):
            try:
                tool_call = self._parse_single_tool_call(raw_call, i)
                tool_calls.append(tool_call)
            except Exception as e:
                errors.append(f"工具调用 {i+1} 解析失败: {str(e)}")

        # 判断是否成功
        success = len(errors) == 0

        return ToolCallParseResult(
            success=success,
            tool_calls=tool_calls,
            errors=errors
        )

    def _parse_single_tool_call(self, raw_call: Dict, index: int) -> ToolCall:
        """
        解析单个工具调用

        Args:
            raw_call: 原始工具调用数据
            index: 工具调用索引

        Returns:
            ToolCall: 工具调用对象

        Raises:
            ValueError: 如果格式不正确
        """
        # 验证是字典
        if not isinstance(raw_call, dict):
            raise ValueError(f"工具调用必须是对象，实际类型: {type(raw_call)}")

        # 验证tool字段
        if 'tool' not in raw_call:
            raise ValueError("缺少必需字段: tool")

        tool_name = raw_call['tool']

        if not isinstance(tool_name, str):
            raise ValueError(f"tool字段必须是字符串，实际类型: {type(tool_name)}")

        # 验证parameters字段
        if 'parameters' not in raw_call:
            raise ValueError("缺少必需字段: parameters")

        parameters = raw_call['parameters']

        if not isinstance(parameters, dict):
            raise ValueError(f"parameters字段必须是对象，实际类型: {type(parameters)}")

        # 创建ToolCall对象
        call_id = raw_call.get('call_id', f"call_{index}")

        return ToolCall(
            tool_name=tool_name,
            parameters=parameters,
            call_id=call_id
        )

    def validate_tool_call(
        self,
        tool_call: ToolCall,
        tool_schema: Dict
    ) -> tuple[bool, Optional[str]]:
        """
        验证工具调用是否符合工具的JSON Schema

        Args:
            tool_call: 工具调用
            tool_schema: 工具的参数JSON Schema

        Returns:
            tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        # 检查必需参数
        required = tool_schema.get('required', [])

        for param_name in required:
            if param_name not in tool_call.parameters:
                return False, f"缺少必需参数: {param_name}"

        # 检查参数类型
        properties = tool_schema.get('properties', {})

        for param_name, param_value in tool_call.parameters.items():
            if param_name not in properties:
                # 未定义的参数，警告但不阻止
                continue

            param_schema = properties[param_name]
            expected_type = param_schema.get('type')

            if expected_type:
                actual_type = self._get_json_type(param_value)

                if actual_type != expected_type:
                    return False, f"参数 {param_name} 类型错误: 期望 {expected_type}，实际 {actual_type}"

        return True, None

    def _get_json_type(self, value: Any) -> str:
        """
        获取值的JSON类型

        Args:
            value: 值

        Returns:
            str: JSON类型（string/number/boolean/array/object/null）
        """
        if value is None:
            return 'null'
        elif isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int) or isinstance(value, float):
            return 'number'
        elif isinstance(value, str):
            return 'string'
        elif isinstance(value, list):
            return 'array'
        elif isinstance(value, dict):
            return 'object'
        else:
            return 'unknown'
