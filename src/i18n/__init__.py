"""
多语言支持模块

提供系统级多语言功能，包括：
- 语言检测和切换
- 翻译服务
- Agent输出语言配置
- 错误消息国际化
"""

from .translator import Translator, get_translator
from .language_detector import LanguageDetector, detect_language

__all__ = [
    'Translator',
    'get_translator',
    'LanguageDetector',
    'detect_language',
]
