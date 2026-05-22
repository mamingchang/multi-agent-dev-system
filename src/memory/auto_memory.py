"""
自动记忆触发系统

借鉴Claude Code的自动记忆机制：
1. 检测用户纠正 → 自动保存为feedback记忆
2. 检测重要决策 → 自动保存为long_term记忆
3. 检测用户偏好 → 自动保存为user记忆
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime


class MemoryTrigger:
    """记忆触发器 - 检测何时应该保存记忆"""

    # 纠正模式（用户纠正Agent的错误）
    CORRECTION_PATTERNS = [
        r"不要.*应该",
        r"不是.*而是",
        r"错了",
        r"不对",
        r"别.*要",
        r"不.*改成",
        r"no.*should",
        r"don't.*instead",
        r"not.*but",
        r"wrong",
        r"incorrect",
    ]

    # 确认模式（用户确认非显而易见的选择）
    CONFIRMATION_PATTERNS = [
        r"是的.*可以",
        r"对.*就这样",
        r"好.*继续",
        r"正确",
        r"没错",
        r"yes.*that",
        r"correct",
        r"exactly",
        r"perfect",
        r"right",
    ]

    # 偏好模式（用户表达偏好）
    PREFERENCE_PATTERNS = [
        r"我喜欢",
        r"我倾向于",
        r"我更喜欢",
        r"我习惯",
        r"我通常",
        r"I prefer",
        r"I like",
        r"I usually",
        r"I tend to",
    ]

    # 记住模式（用户明确要求记住）
    REMEMBER_PATTERNS = [
        r"记住",
        r"记下",
        r"别忘了",
        r"要记得",
        r"remember",
        r"don't forget",
        r"keep in mind",
    ]

    @staticmethod
    def detect_correction(user_message: str, agent_response: str = None) -> Optional[Dict[str, Any]]:
        """
        检测用户纠正

        Args:
            user_message: 用户消息
            agent_response: Agent之前的响应（可选）

        Returns:
            Dict: 如果检测到纠正，返回记忆内容
        """
        for pattern in MemoryTrigger.CORRECTION_PATTERNS:
            if re.search(pattern, user_message, re.IGNORECASE):
                return {
                    'type': 'feedback',
                    'category': 'correction',
                    'content': user_message,
                    'context': agent_response,
                    'importance': 'high',
                    'reason': '用户纠正了Agent的行为或输出'
                }
        return None

    @staticmethod
    def detect_confirmation(user_message: str, agent_action: str = None) -> Optional[Dict[str, Any]]:
        """
        检测用户确认

        Args:
            user_message: 用户消息
            agent_action: Agent的行动（可选）

        Returns:
            Dict: 如果检测到确认，返回记忆内容
        """
        for pattern in MemoryTrigger.CONFIRMATION_PATTERNS:
            if re.search(pattern, user_message, re.IGNORECASE):
                return {
                    'type': 'feedback',
                    'category': 'confirmation',
                    'content': user_message,
                    'context': agent_action,
                    'importance': 'medium',
                    'reason': '用户确认了非显而易见的选择'
                }
        return None

    @staticmethod
    def detect_preference(user_message: str) -> Optional[Dict[str, Any]]:
        """
        检测用户偏好

        Args:
            user_message: 用户消息

        Returns:
            Dict: 如果检测到偏好，返回记忆内容
        """
        for pattern in MemoryTrigger.PREFERENCE_PATTERNS:
            if re.search(pattern, user_message, re.IGNORECASE):
                return {
                    'type': 'user',
                    'category': 'preference',
                    'content': user_message,
                    'importance': 'high',
                    'reason': '用户表达了个人偏好'
                }
        return None

    @staticmethod
    def detect_explicit_remember(user_message: str) -> Optional[Dict[str, Any]]:
        """
        检测明确的记忆请求

        Args:
            user_message: 用户消息

        Returns:
            Dict: 如果检测到记忆请求，返回记忆内容
        """
        for pattern in MemoryTrigger.REMEMBER_PATTERNS:
            if re.search(pattern, user_message, re.IGNORECASE):
                # 提取"记住"后面的内容
                match = re.search(r'(记住|记下|remember)[：:,，\s]*(.*)', user_message, re.IGNORECASE)
                if match:
                    content = match.group(2).strip()
                    if content:
                        return {
                            'type': 'long_term',
                            'category': 'explicit',
                            'content': content,
                            'importance': 'critical',
                            'reason': '用户明确要求记住'
                        }
        return None

    @staticmethod
    def analyze_message(user_message: str, agent_context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        分析用户消息，检测所有可能的记忆触发

        Args:
            user_message: 用户消息
            agent_context: Agent上下文（包含之前的响应、行动等）

        Returns:
            List[Dict]: 检测到的所有记忆触发
        """
        triggers = []

        agent_context = agent_context or {}
        agent_response = agent_context.get('response')
        agent_action = agent_context.get('action')

        # 检测明确的记忆请求（优先级最高）
        explicit = MemoryTrigger.detect_explicit_remember(user_message)
        if explicit:
            triggers.append(explicit)

        # 检测纠正
        correction = MemoryTrigger.detect_correction(user_message, agent_response)
        if correction:
            triggers.append(correction)

        # 检测确认
        confirmation = MemoryTrigger.detect_confirmation(user_message, agent_action)
        if confirmation:
            triggers.append(confirmation)

        # 检测偏好
        preference = MemoryTrigger.detect_preference(user_message)
        if preference:
            triggers.append(preference)

        return triggers


class AutoMemoryManager:
    """
    自动记忆管理器

    负责：
    1. 监听用户消息
    2. 触发记忆保存
    3. 管理记忆生命周期
    """

    def __init__(self, agent):
        """
        初始化自动记忆管理器

        Args:
            agent: Agent实例
        """
        self.agent = agent
        self.trigger = MemoryTrigger()

    def process_user_message(self, user_message: str, agent_context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        处理用户消息，自动保存记忆

        Args:
            user_message: 用户消息
            agent_context: Agent上下文

        Returns:
            List[Dict]: 保存的记忆列表
        """
        # 分析消息
        triggers = self.trigger.analyze_message(user_message, agent_context)

        saved_memories = []

        for trigger_info in triggers:
            # 保存记忆
            memory = self._save_triggered_memory(trigger_info)
            if memory:
                saved_memories.append(memory)
                print(f"[AutoMemory] 自动保存记忆: {trigger_info['category']} - {trigger_info['reason']}")

        return saved_memories

    def _save_triggered_memory(self, trigger_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        保存触发的记忆

        Args:
            trigger_info: 触发信息

        Returns:
            Dict: 保存的记忆
        """
        memory_type = trigger_info['type']
        category = trigger_info['category']
        content = trigger_info['content']
        importance = trigger_info['importance']
        reason = trigger_info['reason']

        # 构建记忆内容
        memory_content = {
            'content': content,
            'category': category,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'context': trigger_info.get('context')
        }

        # 根据类型保存到不同位置
        if memory_type == 'feedback':
            # 保存为反馈记忆（文件）
            return self.agent.save_memory(
                memory_type=f"feedback_{category}",
                content=memory_content
            )

        elif memory_type == 'user':
            # 保存为用户偏好（文件）
            return self.agent.save_memory(
                memory_type=f"user_{category}",
                content=memory_content
            )

        elif memory_type == 'long_term':
            # 保存为长期记忆（内存+文件）
            # 内存记忆
            self.agent.remember(
                content=content,
                memory_type_str="long_term",
                importance=importance,
                tags=[category, 'auto']
            )

            # 文件记忆
            return self.agent.save_memory(
                memory_type=f"explicit_{category}",
                content=memory_content
            )

        return None
