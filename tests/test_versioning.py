"""
版本管理测试

测试场景：
1. 版本号生成
2. 创建版本
3. 列出版本
4. 版本对比
5. 标记关键版本
6. 版本回滚
7. 清理旧版本
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime, timedelta
from src.versioning.version_manager import (
    VersionGenerator, VersionComparator, VersionManager
)
from src.database.database import Database
from src.database.models import Base

# 创建测试数据库
test_db = Database("sqlite:///:memory:")


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """初始化测试数据库 - 每个测试前自动运行"""
    Base.metadata.create_all(bind=test_db.engine)
    yield
    # 清理
    Base.metadata.drop_all(bind=test_db.engine)


def test_version_generation():
    """测试1: 版本号生成"""
    print("\n=== 测试1: 版本号生成 ===")

    # 生成版本号
    version1 = VersionGenerator.generate_version()
    print(f"生成版本号: {version1}")

    # 验证格式
    assert version1.startswith("v")
    assert len(version1) == 16  # v20260509_143022

    # 使用指定时间生成
    test_time = datetime(2026, 5, 9, 14, 30, 22)
    version2 = VersionGenerator.generate_version(test_time)
    assert version2 == "v20260509_143022"
    print(f"指定时间版本号: {version2}")

    print("✓ 版本号生成测试通过")


def test_version_comparison():
    """测试2: 版本对比"""
    print("\n=== 测试2: 版本对比 ===")

    old_content = """def hello():
    print("Hello")
    return True
"""

    new_content = """def hello():
    print("Hello, World!")
    print("Welcome")
    return True
"""

    # 对比版本
    diff_result = VersionComparator.diff_text(old_content, new_content)

    print(f"新增行数: {diff_result['added_lines']}")
    print(f"删除行数: {diff_result['removed_lines']}")
    print(f"总变更: {diff_result['total_changes']}")

    # 验证结果
    assert diff_result['added_lines'] > 0
    assert diff_result['removed_lines'] > 0

    # 生成语义描述
    description = VersionComparator.generate_semantic_description(
        old_content, new_content, diff_result
    )
    print(f"语义描述: {description}")

    print("✓ 版本对比测试通过")


def test_create_version():
    """测试3: 创建版本"""
    print("\n=== 测试3: 创建版本 ===")

    with test_db.get_session() as session:
        version_manager = VersionManager(session)

        # 创建第一个版本
        artifact1 = version_manager.create_version(
            task_id="task-1",
            artifact_name="main.py",
            artifact_type="code",
            content="print('Hello')",
            is_key_version=False
        )

        assert artifact1.version.startswith("v")
        print(f"✓ 创建版本1: {artifact1.version}")

        # 创建第二个版本
        artifact2 = version_manager.create_version(
            task_id="task-1",
            artifact_name="main.py",
            artifact_type="code",
            content="print('Hello, World!')",
            parent_version=artifact1.version
        )

        assert artifact2.version != artifact1.version
        assert artifact2.parent_version == artifact1.version
        print(f"✓ 创建版本2: {artifact2.version}")

    print("✓ 创建版本测试通过")


def test_list_versions():
    """测试4: 列出版本"""
    print("\n=== 测试4: 列出版本 ===")

    with test_db.get_session() as session:
        version_manager = VersionManager(session)

        # 先创建一些版本
        version_manager.create_version(
            task_id="task-1",
            artifact_name="main.py",
            artifact_type="code",
            content="print('Hello')",
            is_key_version=False
        )
        version_manager.create_version(
            task_id="task-1",
            artifact_name="main.py",
            artifact_type="code",
            content="print('Hello, World!')",
            is_key_version=False
        )

        # 列出所有版本
        versions = version_manager.list_versions(
            task_id="task-1",
            artifact_name="main.py"
        )

        print(f"✓ 找到 {len(versions)} 个版本")
        assert len(versions) >= 2

        for v in versions:
            print(f"  - {v.version} (关键版本: {v.is_key_version})")

    print("✓ 列出版本测试通过")


def test_mark_key_version():
    """测试5: 标记关键版本"""
    print("\n=== 测试5: 标记关键版本 ===")

    with test_db.get_session() as session:
        version_manager = VersionManager(session)

        # 先创建版本
        artifact1 = version_manager.create_version(
            task_id="task-1",
            artifact_name="main.py",
            artifact_type="code",
            content="print('Hello')",
            is_key_version=False
        )

        # 标记为关键版本
        success = version_manager.mark_as_key_version(
            task_id="task-1",
            artifact_name="main.py",
            version=artifact1.version,
            description="初始版本"
        )

        assert success
        print(f"✓ 标记关键版本: {artifact1.version}")

        # 验证
        artifact = version_manager.get_version("task-1", "main.py", artifact1.version)
        assert artifact.is_key_version
        assert artifact.version_description == "初始版本"

    print("✓ 标记关键版本测试通过")


def test_compare_versions():
    """测试6: 对比版本"""
    print("\n=== 测试6: 对比版本 ===")

    with test_db.get_session() as session:
        version_manager = VersionManager(session)

        # 创建两个版本
        artifact1 = version_manager.create_version(
            task_id="task-1",
            artifact_name="main.py",
            artifact_type="code",
            content="print('Hello')",
            is_key_version=False
        )
        artifact2 = version_manager.create_version(
            task_id="task-1",
            artifact_name="main.py",
            artifact_type="code",
            content="print('Hello, World!')",
            is_key_version=False
        )

        # 对比版本
        diff_result = version_manager.compare_versions(
            task_id="task-1",
            artifact_name="main.py",
            from_version=artifact1.version,
            to_version=artifact2.version
        )

        print(f"✓ 对比版本: {artifact1.version} -> {artifact2.version}")
        print(f"  总变更: {diff_result['total_changes']} 行")
        print(f"  语义描述: {diff_result['semantic_description']}")

        assert diff_result['total_changes'] > 0

    print("✓ 对比版本测试通过")


def test_rollback_version():
    """测试7: 版本回滚"""
    print("\n=== 测试7: 版本回滚 ===")

    with test_db.get_session() as session:
        version_manager = VersionManager(session)

        # 创建两个版本
        artifact1 = version_manager.create_version(
            task_id="task-1",
            artifact_name="main.py",
            artifact_type="code",
            content="print('Hello')",
            is_key_version=False
        )
        artifact2 = version_manager.create_version(
            task_id="task-1",
            artifact_name="main.py",
            artifact_type="code",
            content="print('Hello, World!')",
            is_key_version=False
        )

        # 回滚到第一个版本
        new_artifact = version_manager.rollback_to_version(
            task_id="task-1",
            artifact_name="main.py",
            target_version=artifact1.version
        )

        print(f"✓ 回滚到版本: {artifact1.version}")
        print(f"  新版本: {new_artifact.version}")
        print(f"  父版本: {new_artifact.parent_version}")

        # 验证内容相同
        assert new_artifact.content == artifact1.content
        assert new_artifact.parent_version == artifact1.version

    print("✓ 版本回滚测试通过")


def test_cleanup_versions():
    """测试8: 清理旧版本"""
    print("\n=== 测试8: 清理旧版本 ===")

    with test_db.get_session() as session:
        version_manager = VersionManager(session)

        # 创建一些版本
        for i in range(5):
            version_manager.create_version(
                task_id="task-1",
                artifact_name="main.py",
                artifact_type="code",
                content=f"print('Version {i}')",
                is_key_version=(i == 0)  # 第一个是关键版本
            )

        # 清理旧版本
        deleted_count = version_manager.cleanup_old_versions(
            task_id="task-1",
            artifact_name="main.py",
            keep_days=30
        )

        print(f"✓ 清理了 {deleted_count} 个旧版本")

        # 验证关键版本仍然存在
        versions = version_manager.list_versions(
            task_id="task-1",
            artifact_name="main.py",
            key_versions_only=True
        )

        assert len(versions) >= 1
        print(f"✓ 关键版本保留: {len(versions)} 个")

    print("✓ 清理旧版本测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("版本管理测试")
    print("="*60)

    try:
        setup_database()
        test_version_generation()
        test_version_comparison()
        test_create_version()
        test_list_versions()
        test_mark_key_version()
        test_compare_versions()
        test_rollback_version()
        test_cleanup_versions()

        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60)

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
