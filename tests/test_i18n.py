"""
多语言支持测试

测试场景：
1. 翻译器基本功能
2. 语言检测
3. 批量翻译
4. 变量替换
5. API端点
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.i18n import Translator, LanguageDetector, detect_language


class TestTranslator:
    """翻译器测试"""

    def test_basic_translation(self):
        """测试基本翻译功能"""
        translator = Translator()

        # 英文翻译
        text_en = translator.translate("auth.login_success", "en-US")
        assert text_en == "Login successful"

        # 中文翻译
        text_zh = translator.translate("auth.login_success", "zh-CN")
        assert text_zh == "登录成功"

        print("✅ 基本翻译测试通过")

    def test_variable_replacement(self):
        """测试变量替换"""
        translator = Translator()

        # 带变量的翻译
        text = translator.translate(
            "task.failed",
            "zh-CN",
            variables={"error": "网络超时"}
        )
        assert "网络超时" in text

        print("✅ 变量替换测试通过")

    def test_fallback(self):
        """测试后备机制"""
        translator = Translator()

        # 不存在的key，使用fallback
        text = translator.translate(
            "nonexistent.key",
            "zh-CN",
            fallback="默认文本"
        )
        assert text == "默认文本"

        # 不存在的key，无fallback，返回key本身
        text = translator.translate("another.nonexistent.key", "zh-CN")
        assert text == "another.nonexistent.key"

        print("✅ 后备机制测试通过")

    def test_batch_translation(self):
        """测试批量翻译"""
        translator = Translator()

        keys = ["auth.login_success", "auth.login_failed", "common.success"]
        translations = translator.translate_batch(keys, "zh-CN")

        assert len(translations) == 3
        assert translations["auth.login_success"] == "登录成功"
        assert translations["auth.login_failed"] == "登录失败"
        assert translations["common.success"] == "成功"

        print("✅ 批量翻译测试通过")

    def test_dynamic_translation(self):
        """测试动态添加翻译"""
        translator = Translator()

        # 添加新翻译
        translator.add_translation("zh-CN", "test.key", "测试文本")

        # 验证
        text = translator.translate("test.key", "zh-CN")
        assert text == "测试文本"

        print("✅ 动态翻译测试通过")

    def test_supported_languages(self):
        """测试获取支持的语言"""
        translator = Translator()

        languages = translator.get_supported_languages()
        assert "zh-CN" in languages
        assert "en-US" in languages

        print("✅ 支持语言列表测试通过")


class TestLanguageDetector:
    """语言检测器测试"""

    def test_detect_from_accept_language(self):
        """测试从Accept-Language检测"""
        # 中文优先
        lang = LanguageDetector.detect_from_accept_language("zh-CN,zh;q=0.9,en;q=0.8")
        assert lang == "zh-CN"

        # 英文优先
        lang = LanguageDetector.detect_from_accept_language("en-US,en;q=0.9")
        assert lang == "en-US"

        # 空值，返回默认
        lang = LanguageDetector.detect_from_accept_language(None)
        assert lang == "en-US"

        print("✅ Accept-Language检测测试通过")

    def test_detect_from_text(self):
        """测试从文本检测语言"""
        # 中文文本
        lang = LanguageDetector.detect_from_text("你好世界，这是一个测试")
        assert lang == "zh-CN"

        # 英文文本
        lang = LanguageDetector.detect_from_text("Hello world, this is a test")
        assert lang == "en-US"

        # 日文文本
        lang = LanguageDetector.detect_from_text("こんにちは世界")
        assert lang == "ja-JP"

        # 韩文文本
        lang = LanguageDetector.detect_from_text("안녕하세요 세계")
        assert lang == "ko-KR"

        # 空文本
        lang = LanguageDetector.detect_from_text("")
        assert lang == "en-US"

        print("✅ 文本语言检测测试通过")

    def test_normalize_language_code(self):
        """测试语言代码标准化"""
        # 简写转完整
        assert LanguageDetector.normalize_language_code("zh") == "zh-CN"
        assert LanguageDetector.normalize_language_code("en") == "en-US"
        assert LanguageDetector.normalize_language_code("ja") == "ja-JP"

        # 完整代码保持不变
        assert LanguageDetector.normalize_language_code("zh-CN") == "zh-CN"
        assert LanguageDetector.normalize_language_code("en-US") == "en-US"

        # 不支持的语言返回默认
        assert LanguageDetector.normalize_language_code("xx") == "en-US"

        print("✅ 语言代码标准化测试通过")

    def test_is_supported(self):
        """测试语言支持检查"""
        assert LanguageDetector.is_supported("zh-CN") is True
        assert LanguageDetector.is_supported("zh") is True
        assert LanguageDetector.is_supported("en-US") is True
        assert LanguageDetector.is_supported("xx-XX") is False

        print("✅ 语言支持检查测试通过")

    def test_detect_language_function(self):
        """测试便捷检测函数"""
        # 优先使用Accept-Language
        lang = detect_language(
            accept_language="zh-CN,en;q=0.8",
            text="Hello world"
        )
        assert lang == "zh-CN"

        # 只有文本
        lang = detect_language(text="你好世界")
        assert lang == "zh-CN"

        # 都没有，返回默认
        lang = detect_language()
        assert lang == "en-US"

        print("✅ 便捷检测函数测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("多语言支持测试")
    print("="*60 + "\n")

    # 翻译器测试
    print("【翻译器测试】")
    translator_tests = TestTranslator()
    translator_tests.test_basic_translation()
    translator_tests.test_variable_replacement()
    translator_tests.test_fallback()
    translator_tests.test_batch_translation()
    translator_tests.test_dynamic_translation()
    translator_tests.test_supported_languages()

    print("\n【语言检测器测试】")
    detector_tests = TestLanguageDetector()
    detector_tests.test_detect_from_accept_language()
    detector_tests.test_detect_from_text()
    detector_tests.test_normalize_language_code()
    detector_tests.test_is_supported()
    detector_tests.test_detect_language_function()

    print("\n" + "="*60)
    print("✅ 所有多语言测试通过！")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()
