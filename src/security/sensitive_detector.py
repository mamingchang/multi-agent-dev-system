"""
敏感信息检测

检测文本中的敏感信息，如API密钥、密码、Token等。

检测范围：
1. API密钥（AWS, Azure, Google Cloud等）
2. 密码和凭证
3. Token和会话ID
4. 私钥和证书
5. 数据库连接串
6. 邮箱和手机号
"""

import re
from typing import List, Dict, Any, Optional
from enum import Enum


class SensitiveType(str, Enum):
    """敏感信息类型"""
    API_KEY = "api_key"
    PASSWORD = "password"
    TOKEN = "token"
    PRIVATE_KEY = "private_key"
    DATABASE_URL = "database_url"
    EMAIL = "email"
    PHONE = "phone"
    CREDIT_CARD = "credit_card"
    AWS_KEY = "aws_key"
    GITHUB_TOKEN = "github_token"
    SLACK_TOKEN = "slack_token"


class SensitiveMatch:
    """敏感信息匹配结果"""

    def __init__(
        self,
        type: SensitiveType,
        value: str,
        start: int,
        end: int,
        confidence: float = 1.0,
        context: str = None
    ):
        """
        初始化匹配结果

        Args:
            type: 敏感信息类型
            value: 匹配的值
            start: 起始位置
            end: 结束位置
            confidence: 置信度（0-1）
            context: 上下文（匹配值周围的文本）
        """
        self.type = type
        self.value = value
        self.start = start
        self.end = end
        self.confidence = confidence
        self.context = context

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type.value,
            "value": self.mask_value(),
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
            "context": self.context
        }

    def mask_value(self) -> str:
        """
        掩码显示敏感值

        Returns:
            str: 掩码后的值
        """
        if len(self.value) <= 8:
            return "*" * len(self.value)

        # 显示前4位和后4位，中间用*代替
        return f"{self.value[:4]}{'*' * (len(self.value) - 8)}{self.value[-4:]}"


class SensitiveDetector:
    """
    敏感信息检测器

    使用正则表达式检测文本中的敏感信息。
    """

    # 正则表达式模式
    PATTERNS = {
        # AWS访问密钥
        SensitiveType.AWS_KEY: [
            (r'AKIA[0-9A-Z]{16}', 1.0),  # AWS Access Key ID
            (r'aws_access_key_id\s*=\s*["\']?([A-Za-z0-9/+=]{40})["\']?', 0.9),
            (r'aws_secret_access_key\s*=\s*["\']?([A-Za-z0-9/+=]{40})["\']?', 0.9),
        ],

        # GitHub Token
        SensitiveType.GITHUB_TOKEN: [
            (r'ghp_[a-zA-Z0-9]{36}', 1.0),  # GitHub Personal Access Token
            (r'gho_[a-zA-Z0-9]{36}', 1.0),  # GitHub OAuth Token
            (r'ghu_[a-zA-Z0-9]{36}', 1.0),  # GitHub User Token
            (r'ghs_[a-zA-Z0-9]{36}', 1.0),  # GitHub Server Token
            (r'ghr_[a-zA-Z0-9]{36}', 1.0),  # GitHub Refresh Token
        ],

        # Slack Token
        SensitiveType.SLACK_TOKEN: [
            (r'xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,32}', 1.0),
        ],

        # 通用API密钥
        SensitiveType.API_KEY: [
            (r'api[_-]?key\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', 0.8),
            (r'apikey\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', 0.8),
            (r'api[_-]?secret\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', 0.8),
        ],

        # 密码
        SensitiveType.PASSWORD: [
            (r'password\s*[=:]\s*["\']([^"\']{8,})["\']', 0.7),
            (r'passwd\s*[=:]\s*["\']([^"\']{8,})["\']', 0.7),
            (r'pwd\s*[=:]\s*["\']([^"\']{8,})["\']', 0.7),
        ],

        # Token
        SensitiveType.TOKEN: [
            (r'token\s*[=:]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?', 0.7),
            (r'access[_-]?token\s*[=:]\s*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?', 0.8),
            (r'bearer\s+([a-zA-Z0-9_\-\.]{20,})', 0.8),
        ],

        # 私钥
        SensitiveType.PRIVATE_KEY: [
            (r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', 1.0),
            (r'-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----', 1.0),
            (r'private[_-]?key\s*[=:]\s*["\']([^"\']+)["\']', 0.8),
        ],

        # 数据库连接串
        SensitiveType.DATABASE_URL: [
            (r'(?:postgres|mysql|mongodb|redis)://[^:]+:[^@]+@[^/]+', 0.9),
            (r'(?:postgresql|mysql)://[^\s]+', 0.8),
            (r'mongodb\+srv://[^\s]+', 0.9),
        ],

        # 邮箱
        SensitiveType.EMAIL: [
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 0.6),
        ],

        # 手机号（中国）
        SensitiveType.PHONE: [
            (r'1[3-9]\d{9}', 0.6),
            (r'\+86\s*1[3-9]\d{9}', 0.7),
        ],

        # 信用卡号
        SensitiveType.CREDIT_CARD: [
            (r'\b(?:\d{4}[-\s]?){3}\d{4}\b', 0.7),
        ],
    }

    def __init__(self, min_confidence: float = 0.6):
        """
        初始化检测器

        Args:
            min_confidence: 最小置信度阈值，低于此值的匹配将被忽略
        """
        self.min_confidence = min_confidence
        self._compiled_patterns = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """编译所有正则表达式"""
        for sensitive_type, patterns in self.PATTERNS.items():
            self._compiled_patterns[sensitive_type] = [
                (re.compile(pattern, re.IGNORECASE), confidence)
                for pattern, confidence in patterns
            ]

    def detect(self, text: str, context_length: int = 50) -> List[SensitiveMatch]:
        """
        检测文本中的敏感信息

        Args:
            text: 要检测的文本
            context_length: 上下文长度（匹配值前后各取多少字符）

        Returns:
            List[SensitiveMatch]: 匹配结果列表
        """
        matches = []

        for sensitive_type, patterns in self._compiled_patterns.items():
            for pattern, confidence in patterns:
                # 跳过低置信度的模式
                if confidence < self.min_confidence:
                    continue

                for match in pattern.finditer(text):
                    # 提取匹配值和位置
                    if match.groups():
                        # 如果有捕获组，使用捕获组的值和位置
                        value = match.group(1)
                        # 找到捕获组在整个匹配中的位置
                        value_start = match.start(1)
                        value_end = match.end(1)
                    else:
                        # 没有捕获组，使用整个匹配
                        value = match.group(0)
                        value_start = match.start()
                        value_end = match.end()

                    # 提取上下文
                    start = max(0, value_start - context_length)
                    end = min(len(text), value_end + context_length)
                    context = text[start:end]

                    matches.append(SensitiveMatch(
                        type=sensitive_type,
                        value=value,
                        start=value_start,
                        end=value_end,
                        confidence=confidence,
                        context=context
                    ))

        # 按位置排序
        matches.sort(key=lambda m: m.start)

        return matches

    def scan_dict(self, data: Dict[str, Any]) -> List[SensitiveMatch]:
        """
        扫描字典中的敏感信息

        Args:
            data: 要扫描的字典

        Returns:
            List[SensitiveMatch]: 匹配结果列表
        """
        matches = []

        def scan_value(value, path=""):
            """递归扫描值"""
            if isinstance(value, str):
                # 检测字符串值
                text_matches = self.detect(value)
                for match in text_matches:
                    match.context = f"{path}: {match.context}"
                    matches.extend(text_matches)
            elif isinstance(value, dict):
                # 递归扫描字典
                for key, val in value.items():
                    scan_value(val, f"{path}.{key}" if path else key)
            elif isinstance(value, list):
                # 递归扫描列表
                for i, val in enumerate(value):
                    scan_value(val, f"{path}[{i}]")

        scan_value(data)
        return matches

    def mask_text(self, text: str, matches: List[SensitiveMatch] = None) -> str:
        """
        掩码文本中的敏感信息

        Args:
            text: 原始文本
            matches: 匹配结果列表（如果为None则重新检测）

        Returns:
            str: 掩码后的文本
        """
        if matches is None:
            matches = self.detect(text)

        # 按位置倒序排序，从后往前替换，避免位置偏移
        matches.sort(key=lambda m: m.start, reverse=True)

        masked_text = text
        for match in matches:
            masked_value = match.mask_value()
            masked_text = (
                masked_text[:match.start] +
                masked_value +
                masked_text[match.end:]
            )

        return masked_text

    def get_summary(self, matches: List[SensitiveMatch]) -> Dict[str, Any]:
        """
        获取检测结果摘要

        Args:
            matches: 匹配结果列表

        Returns:
            dict: 摘要信息
        """
        summary = {
            "total_count": len(matches),
            "by_type": {},
            "high_confidence_count": 0
        }

        for match in matches:
            # 按类型统计
            type_name = match.type.value
            if type_name not in summary["by_type"]:
                summary["by_type"][type_name] = 0
            summary["by_type"][type_name] += 1

            # 高置信度统计
            if match.confidence >= 0.8:
                summary["high_confidence_count"] += 1

        return summary


# 标准化别名
SensitiveDataDetector = SensitiveDetector

# 全局检测器实例
sensitive_detector = SensitiveDetector()


__all__ = ['SensitiveDataDetector', 'SensitiveDetector', 'SensitiveType', 'SensitiveMatch']
