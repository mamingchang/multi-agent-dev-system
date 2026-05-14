"""
MCP和Skill集成系统

支持外部工具调用和API集成
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
import json


class ToolType(str, Enum):
    """工具类型"""
    MCP_SERVER = "mcp_server"  # MCP服务器
    SKILL = "skill"  # Skill技能
    API = "api"  # 外部API


class MCPIntegration:
    """
    MCP和Skill集成管理器

    为什么: 扩展Agent的能力，调用外部工具
    """

    def __init__(self, db):
        self.db = db
        self.registered_tools = {}

    def register_tool(
        self,
        tool_name: str,
        tool_type: ToolType,
        handler: Callable,
        description: str,
        parameters: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        注册工具

        为什么: 动态注册可用的工具
        """
        from ..database.models import RegisteredTool
        import hashlib

        # 生成工具ID
        tool_id = hashlib.sha256(
            f"{tool_name}_{tool_type}_{datetime.utcnow().timestamp()}".encode()
        ).hexdigest()[:16]

        # 保存到数据库
        tool = RegisteredTool(
            tool_id=tool_id,
            tool_name=tool_name,
            tool_type=tool_type.value,
            description=description,
            parameters=parameters,
            metadata=metadata or {},
            registered_at=datetime.utcnow()
        )

        self.db.add(tool)
        self.db.commit()

        # 保存处理器到内存
        self.registered_tools[tool_id] = handler

        return tool_id

    def call_tool(
        self,
        tool_id: str,
        arguments: Dict[str, Any],
        caller_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        调用工具

        为什么: 执行工具功能
        """
        from ..database.models import RegisteredTool, ToolCall

        # 获取工具信息
        tool = self.db.query(RegisteredTool).filter(
            RegisteredTool.tool_id == tool_id
        ).first()

        if not tool:
            return {"error": "Tool not found"}

        # 验证参数
        validation_result = self._validate_arguments(
            tool.parameters,
            arguments
        )

        if not validation_result["valid"]:
            return {"error": f"Invalid arguments: {validation_result['errors']}"}

        # 执行工具
        try:
            handler = self.registered_tools.get(tool_id)
            if not handler:
                return {"error": "Tool handler not found"}

            result = handler(**arguments)

            # 记录调用
            self._record_call(
                tool_id=tool_id,
                arguments=arguments,
                result=result,
                caller_id=caller_id,
                success=True
            )

            return {
                "success": True,
                "result": result
            }

        except Exception as e:
            # 记录失败
            self._record_call(
                tool_id=tool_id,
                arguments=arguments,
                result={"error": str(e)},
                caller_id=caller_id,
                success=False
            )

            return {
                "success": False,
                "error": str(e)
            }

    def _validate_arguments(
        self,
        parameters: Dict[str, Any],
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        验证参数

        为什么: 确保参数符合工具要求
        """
        errors = []

        # 检查必需参数
        required = parameters.get("required", [])
        for param in required:
            if param not in arguments:
                errors.append(f"Missing required parameter: {param}")

        # 检查参数类型
        properties = parameters.get("properties", {})
        for param, value in arguments.items():
            if param in properties:
                expected_type = properties[param].get("type")
                actual_type = type(value).__name__

                # 简化的类型检查
                type_mapping = {
                    "string": "str",
                    "integer": "int",
                    "number": "float",
                    "boolean": "bool",
                    "array": "list",
                    "object": "dict"
                }

                if type_mapping.get(expected_type) != actual_type:
                    errors.append(
                        f"Parameter {param} should be {expected_type}, got {actual_type}"
                    )

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def _record_call(
        self,
        tool_id: str,
        arguments: Dict[str, Any],
        result: Dict[str, Any],
        caller_id: Optional[int],
        success: bool
    ):
        """
        记录工具调用

        为什么: 跟踪工具使用情况
        """
        from ..database.models import ToolCall

        call = ToolCall(
            tool_id=tool_id,
            arguments=arguments,
            result=result,
            caller_id=caller_id,
            success=success,
            called_at=datetime.utcnow()
        )

        self.db.add(call)
        self.db.commit()

    def list_tools(
        self,
        tool_type: Optional[ToolType] = None
    ) -> List[Dict[str, Any]]:
        """
        列出可用工具

        为什么: 查看所有注册的工具
        """
        from ..database.models import RegisteredTool

        query = self.db.query(RegisteredTool)

        if tool_type:
            query = query.filter(RegisteredTool.tool_type == tool_type.value)

        tools = query.all()

        return [
            {
                "tool_id": t.tool_id,
                "tool_name": t.tool_name,
                "tool_type": t.tool_type,
                "description": t.description,
                "parameters": t.parameters,
                "registered_at": t.registered_at.isoformat()
            }
            for t in tools
        ]

    def get_tool_statistics(
        self,
        tool_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取工具统计

        为什么: 了解工具使用情况
        """
        from ..database.models import ToolCall

        query = self.db.query(ToolCall)

        if tool_id:
            query = query.filter(ToolCall.tool_id == tool_id)

        total_calls = query.count()
        successful_calls = query.filter(ToolCall.success == True).count()
        failed_calls = query.filter(ToolCall.success == False).count()

        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "success_rate": round(
                successful_calls / total_calls * 100, 2
            ) if total_calls > 0 else 0
        }

    def unregister_tool(self, tool_id: str) -> bool:
        """
        注销工具

        为什么: 移除不再需要的工具
        """
        from ..database.models import RegisteredTool

        tool = self.db.query(RegisteredTool).filter(
            RegisteredTool.tool_id == tool_id
        ).first()

        if tool:
            self.db.delete(tool)
            self.db.commit()

            # 从内存中移除
            if tool_id in self.registered_tools:
                del self.registered_tools[tool_id]

            return True

        return False
