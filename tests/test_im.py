"""
IM群聊系统简单测试

验证IM模块可以正常导入和基本功能
"""

import pytest


def test_im_imports():
    """测试IM模块导入"""
    from src.im import GroupManager, MessageRouter, MentionHandler, InterventionManager
    from src.im.group_manager import GroupType, MemberRole
    from src.im.message_router import MessageType
    from src.im.intervention_manager import InterventionLevel

    assert GroupManager is not None
    assert MessageRouter is not None
    assert MentionHandler is not None
    assert InterventionManager is not None
    assert GroupType.PROJECT == "project"
    assert MemberRole.OWNER == "owner"
    assert MessageType.TEXT == "text"
    assert InterventionLevel.LEVEL_1 == "level_1"


def test_mention_extraction():
    """测试@提及提取功能"""
    from src.im.mention_handler import MentionHandler
    from unittest.mock import Mock

    mock_db = Mock()
    handler = MentionHandler(mock_db)

    content = "Hey @user1 and @user2, please check this!"
    mentions = handler.extract_mentions(content)

    assert "user1" in mentions
    assert "user2" in mentions
    assert len(mentions) == 2


def test_intervention_levels():
    """测试人工介入级别"""
    from src.im.intervention_manager import InterventionLevel

    assert InterventionLevel.LEVEL_1.value == "level_1"
    assert InterventionLevel.LEVEL_2.value == "level_2"
    assert InterventionLevel.LEVEL_3.value == "level_3"
