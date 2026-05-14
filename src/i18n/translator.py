"""
翻译器模块

提供多语言翻译功能，支持：
- 文本翻译
- 模板翻译（带变量替换）
- 批量翻译
- 翻译缓存
"""

from typing import Dict, Optional, Any
from enum import Enum
import json
from pathlib import Path


class Language(str, Enum):
    """支持的语言"""
    ZH_CN = "zh-CN"  # 简体中文
    ZH_TW = "zh-TW"  # 繁体中文
    EN_US = "en-US"  # 英语（美国）
    EN_GB = "en-GB"  # 英语（英国）
    JA_JP = "ja-JP"  # 日语
    KO_KR = "ko-KR"  # 韩语
    FR_FR = "fr-FR"  # 法语
    DE_DE = "de-DE"  # 德语
    ES_ES = "es-ES"  # 西班牙语
    RU_RU = "ru-RU"  # 俄语


class Translator:
    """
    翻译器类

    功能：
    1. 加载翻译文件（JSON格式）
    2. 根据key和语言返回翻译文本
    3. 支持变量替换（{var}格式）
    4. 翻译缓存提高性能

    Why: 统一管理多语言文本，避免硬编码，便于维护和扩展

    How to apply:
    - 在API返回错误消息时使用translator.translate()
    - 在Agent Prompt中根据用户语言选择模板
    - 在前端通过API获取翻译文本
    """

    def __init__(self, translations_dir: str = None):
        """
        初始化翻译器

        Args:
            translations_dir: 翻译文件目录路径

        Why: 从文件加载翻译，支持动态更新而不需要重启服务
        """
        if translations_dir is None:
            # 默认使用当前模块目录下的translations文件夹
            current_dir = Path(__file__).parent
            translations_dir = current_dir / "translations"

        self.translations_dir = Path(translations_dir)
        self.translations: Dict[str, Dict[str, str]] = {}  # {language: {key: text}}
        self._cache: Dict[str, str] = {}  # 翻译缓存
        self.default_language = Language.EN_US

        # 加载所有翻译文件
        self._load_translations()

    def _load_translations(self):
        """
        加载所有翻译文件

        Why: 启动时一次性加载所有翻译，避免运行时IO开销
        """
        if not self.translations_dir.exists():
            self.translations_dir.mkdir(parents=True, exist_ok=True)
            # 创建默认翻译文件
            self._create_default_translations()

        # 遍历翻译文件目录
        for lang_file in self.translations_dir.glob("*.json"):
            lang_code = lang_file.stem  # 文件名即语言代码
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
            except Exception as e:
                print(f"Failed to load translation file {lang_file}: {e}")

    def _create_default_translations(self):
        """
        创建默认翻译文件（英文和中文）

        Why: 提供开箱即用的基础翻译
        """
        # 英文翻译
        en_translations = {
            # 通用
            "common.success": "Success",
            "common.error": "Error",
            "common.warning": "Warning",
            "common.info": "Information",

            # 认证
            "auth.login_success": "Login successful",
            "auth.login_failed": "Login failed",
            "auth.invalid_credentials": "Invalid username or password",
            "auth.token_expired": "Token expired, please login again",
            "auth.unauthorized": "Unauthorized access",

            # 项目
            "project.created": "Project created successfully",
            "project.updated": "Project updated successfully",
            "project.deleted": "Project deleted successfully",
            "project.not_found": "Project not found",
            "project.permission_denied": "You don't have permission to access this project",

            # 任务
            "task.created": "Task created successfully",
            "task.started": "Task started",
            "task.completed": "Task completed successfully",
            "task.failed": "Task failed: {error}",
            "task.not_found": "Task not found",

            # Agent
            "agent.processing": "{agent_name} is processing...",
            "agent.completed": "{agent_name} completed",
            "agent.failed": "{agent_name} failed: {error}",
            "agent.iteration_limit": "Iteration limit reached, escalating to human",

            # 工作流
            "workflow.started": "Workflow started",
            "workflow.completed": "Workflow completed successfully",
            "workflow.failed": "Workflow failed: {error}",
            "workflow.paused": "Workflow paused",
            "workflow.resumed": "Workflow resumed",

            # 错误
            "error.internal_server": "Internal server error",
            "error.bad_request": "Bad request: {details}",
            "error.not_found": "Resource not found",
            "error.validation": "Validation error: {details}",
            "error.quota_exceeded": "Quota exceeded",
        }

        # 中文翻译
        zh_translations = {
            # 通用
            "common.success": "成功",
            "common.error": "错误",
            "common.warning": "警告",
            "common.info": "信息",

            # 认证
            "auth.login_success": "登录成功",
            "auth.login_failed": "登录失败",
            "auth.invalid_credentials": "用户名或密码错误",
            "auth.token_expired": "令牌已过期，请重新登录",
            "auth.unauthorized": "未授权访问",

            # 项目
            "project.created": "项目创建成功",
            "project.updated": "项目更新成功",
            "project.deleted": "项目删除成功",
            "project.not_found": "项目不存在",
            "project.permission_denied": "您没有权限访问此项目",

            # 任务
            "task.created": "任务创建成功",
            "task.started": "任务已开始",
            "task.completed": "任务完成",
            "task.failed": "任务失败：{error}",
            "task.not_found": "任务不存在",

            # Agent
            "agent.processing": "{agent_name}正在处理...",
            "agent.completed": "{agent_name}已完成",
            "agent.failed": "{agent_name}失败：{error}",
            "agent.iteration_limit": "达到迭代上限，升级到人工处理",

            # 工作流
            "workflow.started": "工作流已开始",
            "workflow.completed": "工作流完成",
            "workflow.failed": "工作流失败：{error}",
            "workflow.paused": "工作流已暂停",
            "workflow.resumed": "工作流已恢复",

            # 错误
            "error.internal_server": "服务器内部错误",
            "error.bad_request": "请求错误：{details}",
            "error.not_found": "资源不存在",
            "error.validation": "验证错误：{details}",
            "error.quota_exceeded": "配额已超限",
        }

        # 保存翻译文件
        with open(self.translations_dir / "en-US.json", 'w', encoding='utf-8') as f:
            json.dump(en_translations, f, ensure_ascii=False, indent=2)

        with open(self.translations_dir / "zh-CN.json", 'w', encoding='utf-8') as f:
            json.dump(zh_translations, f, ensure_ascii=False, indent=2)

        # 加载到内存
        self.translations["en-US"] = en_translations
        self.translations["zh-CN"] = zh_translations

    def translate(
        self,
        key: str,
        language: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        fallback: Optional[str] = None
    ) -> str:
        """
        翻译文本

        Args:
            key: 翻译键（如 "auth.login_success"）
            language: 目标语言（如 "zh-CN"），None则使用默认语言
            variables: 变量字典，用于替换文本中的{var}占位符
            fallback: 找不到翻译时的后备文本

        Returns:
            翻译后的文本

        Why:
        - 使用key而不是直接文本，便于统一管理和批量修改
        - 支持变量替换，灵活处理动态内容
        - 提供fallback机制，确保总能返回可读文本

        Example:
            translator.translate("task.failed", "zh-CN", {"error": "网络超时"})
            # 返回: "任务失败：网络超时"
        """
        # 使用默认语言
        if language is None:
            language = self.default_language

        # 生成缓存键
        cache_key = f"{language}:{key}"
        if cache_key in self._cache:
            text = self._cache[cache_key]
        else:
            # 查找翻译
            lang_translations = self.translations.get(language, {})
            text = lang_translations.get(key)

            # 如果找不到，尝试使用默认语言
            if text is None and language != self.default_language:
                default_translations = self.translations.get(self.default_language, {})
                text = default_translations.get(key)

            # 如果还是找不到，使用fallback或key本身
            if text is None:
                text = fallback if fallback else key

            # 缓存结果
            self._cache[cache_key] = text

        # 变量替换
        if variables:
            try:
                text = text.format(**variables)
            except KeyError as e:
                print(f"Missing variable in translation: {e}")

        return text

    def translate_batch(
        self,
        keys: list[str],
        language: Optional[str] = None
    ) -> Dict[str, str]:
        """
        批量翻译

        Args:
            keys: 翻译键列表
            language: 目标语言

        Returns:
            {key: translated_text} 字典

        Why: 批量翻译减少函数调用开销，适合前端一次性获取多个翻译
        """
        return {key: self.translate(key, language) for key in keys}

    def add_translation(self, language: str, key: str, text: str):
        """
        动态添加翻译

        Args:
            language: 语言代码
            key: 翻译键
            text: 翻译文本

        Why: 支持运行时动态添加翻译，无需重启服务
        """
        if language not in self.translations:
            self.translations[language] = {}

        self.translations[language][key] = text

        # 清除缓存
        cache_key = f"{language}:{key}"
        if cache_key in self._cache:
            del self._cache[cache_key]

    def get_supported_languages(self) -> list[str]:
        """
        获取支持的语言列表

        Returns:
            语言代码列表
        """
        return list(self.translations.keys())

    def reload(self):
        """
        重新加载翻译文件

        Why: 支持热更新翻译，无需重启服务
        """
        self.translations.clear()
        self._cache.clear()
        self._load_translations()


# 全局翻译器实例
_translator: Optional[Translator] = None


def get_translator() -> Translator:
    """
    获取全局翻译器实例（单例模式）

    Why: 避免重复加载翻译文件，提高性能
    """
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator
