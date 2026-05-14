"""
剩余功能测试
"""

import pytest


def test_archive_imports():
    """测试对话归档导入"""
    from src.archive import ConversationArchive
    assert ConversationArchive is not None


def test_requirement_anchor_imports():
    """测试需求锚点导入"""
    from src.requirement_anchor.anchor_checker import RequirementAnchor, RequirementLevel
    assert RequirementAnchor is not None
    assert RequirementLevel.BUSINESS == "business"


def test_memory_conflict_imports():
    """测试记忆冲突导入"""
    from src.memory_conflict.conflict_detector import MemoryConflictDetector, ConflictType
    assert MemoryConflictDetector is not None
    assert ConflictType.CONTRADICTION == "contradiction"


def test_cross_project_imports():
    """测试跨项目协作导入"""
    from src.cross_project.collaboration import CrossProjectCollaboration, ShareStatus
    assert CrossProjectCollaboration is not None
    assert ShareStatus.PENDING == "pending"


def test_mcp_integration_imports():
    """测试MCP集成导入"""
    from src.mcp_integration.mcp_manager import MCPIntegration, ToolType
    assert MCPIntegration is not None
    assert ToolType.MCP_SERVER == "mcp_server"
