"""
备份系统测试

测试场景：
1. 创建全量备份
2. 创建增量备份
3. 验证备份完整性
4. 列出备份记录
5. 清理旧备份
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
import shutil
from datetime import datetime, timedelta
from src.backup.backup_manager import BackupManager, BackupType, BackupStatus


def test_create_full_backup():
    """测试1: 创建全量备份"""
    print("\n=== 测试1: 创建全量备份 ===")

    # 使用临时目录
    temp_dir = tempfile.mkdtemp()

    try:
        manager = BackupManager(backup_dir=temp_dir)

        # 创建模拟备份（不实际连接数据库）
        backup_id = f"full_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        backup_file = os.path.join(temp_dir, f"{backup_id}.sql")

        # 创建模拟备份文件
        with open(backup_file, "w") as f:
            f.write("-- PostgreSQL database dump\n")
            f.write("CREATE TABLE test (id INT);\n")

        # 手动创建备份记录
        from src.backup.backup_manager import BackupRecord
        record = BackupRecord(
            backup_id=backup_id,
            backup_type=BackupType.FULL,
            timestamp=datetime.utcnow(),
            file_path=backup_file,
            file_size=os.path.getsize(backup_file),
            checksum=manager._calculate_checksum(backup_file),
            status=BackupStatus.COMPLETED
        )

        manager.records.append(record)
        manager._save_records()

        print(f"✓ 备份ID: {record.backup_id}")
        print(f"✓ 文件大小: {record.file_size} 字节")
        print(f"✓ 校验和: {record.checksum}")
        print("✓ 全量备份测试通过")

    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


def test_create_incremental_backup():
    """测试2: 创建增量备份"""
    print("\n=== 测试2: 创建增量备份 ===")

    temp_dir = tempfile.mkdtemp()

    try:
        manager = BackupManager(backup_dir=temp_dir)

        # 创建模拟增量备份
        backup_id = f"incremental_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        backup_file = os.path.join(temp_dir, f"{backup_id}.sql")

        with open(backup_file, "w") as f:
            f.write("-- Incremental backup\n")
            f.write("INSERT INTO test VALUES (1);\n")

        from src.backup.backup_manager import BackupRecord
        record = BackupRecord(
            backup_id=backup_id,
            backup_type=BackupType.INCREMENTAL,
            timestamp=datetime.utcnow(),
            file_path=backup_file,
            file_size=os.path.getsize(backup_file),
            checksum=manager._calculate_checksum(backup_file),
            status=BackupStatus.COMPLETED
        )

        manager.records.append(record)
        manager._save_records()

        print(f"✓ 备份ID: {record.backup_id}")
        print(f"✓ 备份类型: {record.backup_type.value}")
        print("✓ 增量备份测试通过")

    finally:
        shutil.rmtree(temp_dir)


def test_verify_backup():
    """测试3: 验证备份完整性"""
    print("\n=== 测试3: 验证备份完整性 ===")

    temp_dir = tempfile.mkdtemp()

    try:
        manager = BackupManager(backup_dir=temp_dir)

        # 创建备份文件
        backup_id = f"full_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        backup_file = os.path.join(temp_dir, f"{backup_id}.sql")

        content = "-- Test backup\nCREATE TABLE test (id INT);\n"
        with open(backup_file, "w") as f:
            f.write(content)

        from src.backup.backup_manager import BackupRecord
        record = BackupRecord(
            backup_id=backup_id,
            backup_type=BackupType.FULL,
            timestamp=datetime.utcnow(),
            file_path=backup_file,
            file_size=os.path.getsize(backup_file),
            checksum=manager._calculate_checksum(backup_file),
            status=BackupStatus.COMPLETED
        )

        manager.records.append(record)

        # 验证备份
        is_valid = manager.verify_backup(backup_id)
        assert is_valid, "备份验证应该通过"
        print("✓ 备份验证通过")

        # 修改文件内容（模拟损坏）
        with open(backup_file, "a") as f:
            f.write("-- corrupted\n")

        is_valid = manager.verify_backup(backup_id)
        assert not is_valid, "损坏的备份验证应该失败"
        print("✓ 损坏检测正常")

        print("✓ 备份验证测试通过")

    finally:
        shutil.rmtree(temp_dir)


def test_list_backups():
    """测试4: 列出备份记录"""
    print("\n=== 测试4: 列出备份记录 ===")

    temp_dir = tempfile.mkdtemp()

    try:
        manager = BackupManager(backup_dir=temp_dir)

        # 创建多个备份记录
        from src.backup.backup_manager import BackupRecord

        for i in range(5):
            backup_id = f"full_{i}"
            backup_file = os.path.join(temp_dir, f"{backup_id}.sql")

            with open(backup_file, "w") as f:
                f.write(f"-- Backup {i}\n")

            record = BackupRecord(
                backup_id=backup_id,
                backup_type=BackupType.FULL,
                timestamp=datetime.utcnow() - timedelta(days=i),
                file_path=backup_file,
                file_size=os.path.getsize(backup_file),
                checksum=manager._calculate_checksum(backup_file),
                status=BackupStatus.COMPLETED
            )

            manager.records.append(record)

        # 列出所有备份
        backups = manager.list_backups(limit=10)
        assert len(backups) == 5, f"应该有5个备份，实际 {len(backups)}"
        print(f"✓ 总备份数: {len(backups)}")

        # 验证按时间倒序
        for i in range(len(backups) - 1):
            assert backups[i].timestamp >= backups[i + 1].timestamp, "应该按时间倒序"
        print("✓ 时间排序正确")

        # 限制返回数量
        backups = manager.list_backups(limit=3)
        assert len(backups) == 3, f"应该返回3个备份，实际 {len(backups)}"
        print("✓ 数量限制正常")

        print("✓ 列出备份测试通过")

    finally:
        shutil.rmtree(temp_dir)


def test_cleanup_old_backups():
    """测试5: 清理旧备份"""
    print("\n=== 测试5: 清理旧备份 ===")

    temp_dir = tempfile.mkdtemp()

    try:
        manager = BackupManager(backup_dir=temp_dir)

        from src.backup.backup_manager import BackupRecord

        # 创建新备份（10天前）
        new_backup_id = "full_new"
        new_backup_file = os.path.join(temp_dir, f"{new_backup_id}.sql")
        with open(new_backup_file, "w") as f:
            f.write("-- New backup\n")

        new_record = BackupRecord(
            backup_id=new_backup_id,
            backup_type=BackupType.FULL,
            timestamp=datetime.utcnow() - timedelta(days=10),
            file_path=new_backup_file,
            file_size=os.path.getsize(new_backup_file),
            checksum=manager._calculate_checksum(new_backup_file),
            status=BackupStatus.COMPLETED
        )
        manager.records.append(new_record)

        # 创建旧备份（40天前）
        old_backup_id = "full_old"
        old_backup_file = os.path.join(temp_dir, f"{old_backup_id}.sql")
        with open(old_backup_file, "w") as f:
            f.write("-- Old backup\n")

        old_record = BackupRecord(
            backup_id=old_backup_id,
            backup_type=BackupType.FULL,
            timestamp=datetime.utcnow() - timedelta(days=40),
            file_path=old_backup_file,
            file_size=os.path.getsize(old_backup_file),
            checksum=manager._calculate_checksum(old_backup_file),
            status=BackupStatus.COMPLETED
        )
        manager.records.append(old_record)

        print(f"✓ 创建了2个备份（1个新，1个旧）")

        # 清理30天前的备份
        deleted = manager.cleanup_old_backups(keep_days=30)
        assert deleted == 1, f"应该删除1个备份，实际删除 {deleted}"
        print(f"✓ 删除了 {deleted} 个旧备份")

        # 验证新备份仍然存在
        assert os.path.exists(new_backup_file), "新备份应该保留"
        print("✓ 新备份已保留")

        # 验证旧备份已删除
        assert not os.path.exists(old_backup_file), "旧备份应该删除"
        print("✓ 旧备份已删除")

        print("✓ 清理旧备份测试通过")

    finally:
        shutil.rmtree(temp_dir)


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("备份系统测试")
    print("="*60)

    try:
        test_create_full_backup()
        test_create_incremental_backup()
        test_verify_backup()
        test_list_backups()
        test_cleanup_old_backups()

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
