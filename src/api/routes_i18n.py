"""
多语言API路由

提供多语言相关的API端点：
- 获取翻译
- 批量获取翻译
- 获取支持的语言列表
- 检测语言
"""

from fastapi import APIRouter, Header, Query
from typing import Optional, List
from pydantic import BaseModel

from src.i18n import get_translator, detect_language


router = APIRouter(prefix="/i18n", tags=["i18n"])


class TranslationRequest(BaseModel):
    """翻译请求"""
    key: str
    language: Optional[str] = None
    variables: Optional[dict] = None


class BatchTranslationRequest(BaseModel):
    """批量翻译请求"""
    keys: List[str]
    language: Optional[str] = None


class TranslationResponse(BaseModel):
    """翻译响应"""
    key: str
    text: str
    language: str


class BatchTranslationResponse(BaseModel):
    """批量翻译响应"""
    translations: dict[str, str]
    language: str


class LanguageDetectionResponse(BaseModel):
    """语言检测响应"""
    detected_language: str
    confidence: str  # "high", "medium", "low"


class SupportedLanguagesResponse(BaseModel):
    """支持的语言列表响应"""
    languages: List[dict]


@router.post("/translate", response_model=TranslationResponse)
async def translate_text(
    request: TranslationRequest,
    accept_language: Optional[str] = Header(None)
):
    """
    翻译文本

    Args:
        request: 翻译请求
        accept_language: HTTP Accept-Language头

    Returns:
        翻译后的文本

    Why: 提供API接口让前端获取翻译文本，支持动态语言切换

    Example:
        POST /api/i18n/translate
        {
            "key": "auth.login_success",
            "language": "zh-CN",
            "variables": {"username": "张三"}
        }

        Response:
        {
            "key": "auth.login_success",
            "text": "登录成功",
            "language": "zh-CN"
        }
    """
    translator = get_translator()

    # 确定目标语言
    target_language = request.language
    if not target_language:
        # 从Accept-Language检测
        target_language = detect_language(accept_language=accept_language)

    # 翻译
    text = translator.translate(
        key=request.key,
        language=target_language,
        variables=request.variables
    )

    return TranslationResponse(
        key=request.key,
        text=text,
        language=target_language
    )


@router.post("/translate/batch", response_model=BatchTranslationResponse)
async def translate_batch(
    request: BatchTranslationRequest,
    accept_language: Optional[str] = Header(None)
):
    """
    批量翻译

    Args:
        request: 批量翻译请求
        accept_language: HTTP Accept-Language头

    Returns:
        翻译结果字典

    Why: 减少HTTP请求次数，提高前端加载性能

    Example:
        POST /api/i18n/translate/batch
        {
            "keys": ["auth.login_success", "auth.login_failed"],
            "language": "zh-CN"
        }

        Response:
        {
            "translations": {
                "auth.login_success": "登录成功",
                "auth.login_failed": "登录失败"
            },
            "language": "zh-CN"
        }
    """
    translator = get_translator()

    # 确定目标语言
    target_language = request.language
    if not target_language:
        target_language = detect_language(accept_language=accept_language)

    # 批量翻译
    translations = translator.translate_batch(
        keys=request.keys,
        language=target_language
    )

    return BatchTranslationResponse(
        translations=translations,
        language=target_language
    )


@router.get("/languages", response_model=SupportedLanguagesResponse)
async def get_supported_languages():
    """
    获取支持的语言列表

    Returns:
        支持的语言列表

    Why: 让前端知道系统支持哪些语言，用于语言选择器

    Example:
        GET /api/i18n/languages

        Response:
        {
            "languages": [
                {"code": "zh-CN", "name": "简体中文", "native_name": "简体中文"},
                {"code": "en-US", "name": "English (US)", "native_name": "English (US)"},
                ...
            ]
        }
    """
    # 语言信息（代码、英文名、本地名）
    languages = [
        {"code": "zh-CN", "name": "Chinese (Simplified)", "native_name": "简体中文"},
        {"code": "zh-TW", "name": "Chinese (Traditional)", "native_name": "繁體中文"},
        {"code": "en-US", "name": "English (US)", "native_name": "English (US)"},
        {"code": "en-GB", "name": "English (UK)", "native_name": "English (UK)"},
        {"code": "ja-JP", "name": "Japanese", "native_name": "日本語"},
        {"code": "ko-KR", "name": "Korean", "native_name": "한국어"},
        {"code": "fr-FR", "name": "French", "native_name": "Français"},
        {"code": "de-DE", "name": "German", "native_name": "Deutsch"},
        {"code": "es-ES", "name": "Spanish", "native_name": "Español"},
        {"code": "ru-RU", "name": "Russian", "native_name": "Русский"},
    ]

    return SupportedLanguagesResponse(languages=languages)


@router.post("/detect", response_model=LanguageDetectionResponse)
async def detect_language_from_text(
    text: str = Query(..., description="要检测的文本"),
    accept_language: Optional[str] = Header(None)
):
    """
    检测文本语言

    Args:
        text: 要检测的文本
        accept_language: HTTP Accept-Language头（作为后备）

    Returns:
        检测到的语言

    Why: 帮助Agent自动识别用户输入的语言，选择合适的响应语言

    Example:
        POST /api/i18n/detect?text=你好世界

        Response:
        {
            "detected_language": "zh-CN",
            "confidence": "high"
        }
    """
    # 检测语言
    detected = detect_language(text=text)

    # 判断置信度
    # 如果检测结果与Accept-Language一致，置信度高
    # 如果文本很短，置信度低
    confidence = "medium"
    if accept_language:
        browser_lang = detect_language(accept_language=accept_language)
        if detected == browser_lang:
            confidence = "high"

    if len(text) < 10:
        confidence = "low"
    elif len(text) > 50:
        confidence = "high"

    return LanguageDetectionResponse(
        detected_language=detected,
        confidence=confidence
    )


@router.post("/reload")
async def reload_translations():
    """
    重新加载翻译文件

    Returns:
        操作结果

    Why: 支持热更新翻译，无需重启服务

    Example:
        POST /api/i18n/reload

        Response:
        {
            "message": "Translations reloaded successfully",
            "languages_count": 2
        }
    """
    translator = get_translator()
    translator.reload()

    return {
        "message": "Translations reloaded successfully",
        "languages_count": len(translator.get_supported_languages())
    }
