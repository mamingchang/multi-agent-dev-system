"""
项目导入测试
"""

import pytest


def test_import_modules():
    """测试导入模块"""
    from src.project_import import GitImporter, CodeAnalyzer, KnowledgeExtractor

    assert GitImporter is not None
    assert CodeAnalyzer is not None
    assert KnowledgeExtractor is not None


def test_code_analyzer_language_detection():
    """测试语言检测"""
    from src.project_import.code_analyzer import CodeAnalyzer

    analyzer = CodeAnalyzer()

    assert analyzer.LANGUAGE_EXTENSIONS[".py"] == "Python"
    assert analyzer.LANGUAGE_EXTENSIONS[".js"] == "JavaScript"
    assert analyzer.LANGUAGE_EXTENSIONS[".go"] == "Go"


def test_knowledge_extractor_summary():
    """测试知识提取摘要生成"""
    from src.project_import.knowledge_extractor import KnowledgeExtractor

    extractor = KnowledgeExtractor()

    knowledge = {
        "readme": {"found": True, "file": "README.md", "length": 1000},
        "api_endpoints": [{"method": "GET", "path": "/api/test"}],
        "database_models": [{"name": "User", "table": "users"}],
        "configuration": {"env_variables": ["DATABASE_URL", "SECRET_KEY"]},
        "documentation": {"markdown_files": [{"name": "guide.md"}]}
    }

    summary = extractor.generate_summary(knowledge)

    assert "README" in summary
    assert "API Endpoints" in summary
    assert "Database Models" in summary
