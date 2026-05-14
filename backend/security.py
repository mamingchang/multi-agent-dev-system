"""
Security utilities
安全工具函数
"""
import bleach


def sanitize_html(text: str) -> str:
    """
    清理HTML，防止XSS攻击

    Args:
        text: 输入文本

    Returns:
        清理后的文本
    """
    if not text:
        return text

    # 移除所有HTML标签
    return bleach.clean(text, tags=[], strip=True)


def sanitize_dict(data: dict, fields: list) -> dict:
    """
    清理字典中指定字段的HTML

    Args:
        data: 输入字典
        fields: 需要清理的字段列表

    Returns:
        清理后的字典
    """
    result = data.copy()
    for field in fields:
        if field in result and isinstance(result[field], str):
            result[field] = sanitize_html(result[field])
    return result
