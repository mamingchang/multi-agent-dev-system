"""
语言检测模块

提供自动语言检测功能，支持：
- 从HTTP请求头检测语言
- 从文本内容检测语言
- 语言代码标准化
"""

from typing import Optional
import re


class LanguageDetector:
    """
    语言检测器

    功能：
    1. 从Accept-Language请求头检测用户首选语言
    2. 从文本内容检测语言（基于字符集）
    3. 语言代码标准化（如 zh -> zh-CN）

    Why: 自动检测用户语言，提供更好的用户体验，无需手动选择

    How to apply:
    - 在API中间件中检测请求语言
    - 在Agent处理时检测输入文本语言
    - 自动选择合适的翻译语言
    """

    # 语言代码映射（简写 -> 完整代码）
    LANGUAGE_MAP = {
        "zh": "zh-CN",
        "en": "en-US",
        "ja": "ja-JP",
        "ko": "ko-KR",
        "fr": "fr-FR",
        "de": "de-DE",
        "es": "es-ES",
        "ru": "ru-RU",
    }

    # 支持的语言列表
    SUPPORTED_LANGUAGES = [
        "zh-CN", "zh-TW", "en-US", "en-GB",
        "ja-JP", "ko-KR", "fr-FR", "de-DE",
        "es-ES", "ru-RU"
    ]

    @staticmethod
    def detect_from_accept_language(accept_language: Optional[str]) -> str:
        """
        从Accept-Language请求头检测语言

        Args:
            accept_language: HTTP Accept-Language头的值
                例如: "zh-CN,zh;q=0.9,en;q=0.8"

        Returns:
            检测到的语言代码（如 "zh-CN"）

        Why:
        - 遵循HTTP标准，尊重用户浏览器语言设置
        - 支持质量值（q值）排序，选择用户最偏好的语言

        Example:
            detect_from_accept_language("zh-CN,zh;q=0.9,en;q=0.8")
            # 返回: "zh-CN"
        """
        if not accept_language:
            return "en-US"  # 默认英语

        # 解析Accept-Language头
        # 格式: "zh-CN,zh;q=0.9,en;q=0.8"
        languages = []
        for lang_entry in accept_language.split(','):
            lang_entry = lang_entry.strip()

            # 提取语言代码和质量值
            if ';q=' in lang_entry:
                lang_code, quality = lang_entry.split(';q=')
                quality = float(quality)
            else:
                lang_code = lang_entry
                quality = 1.0

            lang_code = lang_code.strip()
            languages.append((lang_code, quality))

        # 按质量值排序（降序）
        languages.sort(key=lambda x: x[1], reverse=True)

        # 查找第一个支持的语言
        for lang_code, _ in languages:
            # 标准化语言代码
            normalized = LanguageDetector.normalize_language_code(lang_code)
            if normalized in LanguageDetector.SUPPORTED_LANGUAGES:
                return normalized

        # 如果没有找到支持的语言，返回默认语言
        return "en-US"

    @staticmethod
    def detect_from_text(text: str) -> str:
        """
        从文本内容检测语言

        Args:
            text: 要检测的文本

        Returns:
            检测到的语言代码

        Why:
        - 基于字符集特征快速判断语言
        - 适用于Agent输入文本的语言检测

        How:
        - 中文：检测中文字符（Unicode范围）
        - 日文：检测平假名、片假名
        - 韩文：检测韩文字符
        - 俄文：检测西里尔字母
        - 默认：英文

        Example:
            detect_from_text("你好世界")  # 返回: "zh-CN"
            detect_from_text("Hello")     # 返回: "en-US"
        """
        if not text:
            return "en-US"

        # 统计各种字符数量
        # 注意：日文优先检测，因为日文可能包含汉字
        japanese_count = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff]', text))  # 平假名+片假名
        korean_count = len(re.findall(r'[\uac00-\ud7af]', text))  # 韩文
        chinese_count = len(re.findall(r'[\u4e00-\u9fff]', text))  # 汉字（中日韩共用）
        cyrillic_count = len(re.findall(r'[\u0400-\u04ff]', text))  # 西里尔字母

        total_chars = len(text)
        if total_chars == 0:
            return "en-US"

        # 计算各语言字符占比
        japanese_ratio = japanese_count / total_chars
        korean_ratio = korean_count / total_chars
        chinese_ratio = chinese_count / total_chars
        cyrillic_ratio = cyrillic_count / total_chars

        # 判断语言（优先级：日文>韩文>中文>俄文，阈值：10%）
        # Why: 日文和韩文有独特字符，优先判断；中文汉字可能出现在日文中，所以最后判断
        if japanese_ratio > 0.1:
            return "ja-JP"
        elif korean_ratio > 0.1:
            return "ko-KR"
        elif chinese_ratio > 0.2:
            return "zh-CN"
        elif cyrillic_ratio > 0.2:
            return "ru-RU"
        else:
            # 默认英语
            return "en-US"

    @staticmethod
    def normalize_language_code(lang_code: str) -> str:
        """
        标准化语言代码

        Args:
            lang_code: 原始语言代码（如 "zh", "en", "zh-CN"）

        Returns:
            标准化后的语言代码（如 "zh-CN", "en-US"）

        Why:
        - 统一语言代码格式，避免不一致
        - 将简写代码映射到完整代码

        Example:
            normalize_language_code("zh")     # 返回: "zh-CN"
            normalize_language_code("en")     # 返回: "en-US"
            normalize_language_code("zh-CN")  # 返回: "zh-CN"
        """
        lang_code = lang_code.lower().strip()

        # 如果已经是完整代码，直接返回
        if lang_code in [lang.lower() for lang in LanguageDetector.SUPPORTED_LANGUAGES]:
            # 找到原始大小写版本
            for supported in LanguageDetector.SUPPORTED_LANGUAGES:
                if supported.lower() == lang_code:
                    return supported

        # 提取主语言代码（如 "zh-CN" -> "zh"）
        main_lang = lang_code.split('-')[0]

        # 查找映射
        if main_lang in LanguageDetector.LANGUAGE_MAP:
            return LanguageDetector.LANGUAGE_MAP[main_lang]

        # 默认返回英语
        return "en-US"

    @staticmethod
    def is_supported(lang_code: str) -> bool:
        """
        检查语言是否支持

        Args:
            lang_code: 语言代码

        Returns:
            是否支持该语言
        """
        lang_code = lang_code.lower().strip()

        # 检查是否在支持列表中
        for supported in LanguageDetector.SUPPORTED_LANGUAGES:
            if supported.lower() == lang_code:
                return True

        # 检查简写形式
        main_lang = lang_code.split('-')[0]
        if main_lang in LanguageDetector.LANGUAGE_MAP:
            return True

        return False


def detect_language(
    accept_language: Optional[str] = None,
    text: Optional[str] = None
) -> str:
    """
    便捷函数：检测语言

    Args:
        accept_language: HTTP Accept-Language头
        text: 文本内容

    Returns:
        检测到的语言代码

    Why: 提供简单的函数接口，优先使用Accept-Language，其次使用文本检测

    Example:
        # 从请求头检测
        lang = detect_language(accept_language="zh-CN,en;q=0.8")

        # 从文本检测
        lang = detect_language(text="你好世界")

        # 两者都提供时，优先使用Accept-Language
        lang = detect_language(accept_language="en-US", text="你好")  # 返回: "en-US"
    """
    # 优先使用Accept-Language
    if accept_language:
        return LanguageDetector.detect_from_accept_language(accept_language)

    # 其次使用文本检测
    if text:
        return LanguageDetector.detect_from_text(text)

    # 默认英语
    return "en-US"
