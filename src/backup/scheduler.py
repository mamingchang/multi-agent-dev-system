"""
备份调度器

实现自动化的备份调度。

调度策略：
- 全量备份：每周日凌晨2点
- 增量备份：每天凌晨3点
- 备份清理：每月1号清理30天前的备份
"""

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False
    BackgroundScheduler = None
    CronTrigger = None

from datetime import datetime
from typing import Optional

from .backup_manager import backup_manager, BackupType


class BackupScheduler:
    """备份调度器"""

    def __init__(self):
        """初始化调度器"""
        if not HAS_APSCHEDULER:
            self.scheduler = None
            return
        self.scheduler = BackgroundScheduler()
        self._setup_jobs()

    def _setup_jobs(self):
        """设置调度任务"""
        if not HAS_APSCHEDULER or not self.scheduler:
            return
        # 全量备份：每周日凌晨2点
        self.scheduler.add_job(
            func=self._run_full_backup,
            trigger=CronTrigger(day_of_week="sun", hour=2, minute=0),
            id="full_backup",
            name="全量备份",
            replace_existing=True
        )

        # 增量备份：每天凌晨3点
        self.scheduler.add_job(
            func=self._run_incremental_backup,
            trigger=CronTrigger(hour=3, minute=0),
            id="incremental_backup",
            name="增量备份",
            replace_existing=True
        )

        # 备份清理：每月1号凌晨4点
        self.scheduler.add_job(
            func=self._run_cleanup,
            trigger=CronTrigger(day=1, hour=4, minute=0),
            id="backup_cleanup",
            name="备份清理",
            replace_existing=True
        )

    def _run_full_backup(self):
        """执行全量备份"""
        try:
            print(f"\n[{datetime.utcnow()}] 开始全量备份...")
            record = backup_manager.create_backup(BackupType.FULL)
            print(f"全量备份完成: {record.backup_id}")
        except Exception as e:
            print(f"全量备份失败: {e}")

    def _run_incremental_backup(self):
        """执行增量备份"""
        try:
            print(f"\n[{datetime.utcnow()}] 开始增量备份...")
            record = backup_manager.create_backup(BackupType.INCREMENTAL)
            print(f"增量备份完成: {record.backup_id}")
        except Exception as e:
            print(f"增量备份失败: {e}")

    def _run_cleanup(self):
        """执行备份清理"""
        try:
            print(f"\n[{datetime.utcnow()}] 开始清理旧备份...")
            deleted = backup_manager.cleanup_old_backups(keep_days=30)
            print(f"清理完成: 删除 {deleted} 个旧备份")
        except Exception as e:
            print(f"清理失败: {e}")

    def start(self):
        """启动调度器"""
        if not HAS_APSCHEDULER or not self.scheduler:
            print("备份调度器不可用 (apscheduler未安装)")
            return
        if not self.scheduler.running:
            self.scheduler.start()
            print("备份调度器已启动")

    def stop(self):
        """停止调度器"""
        if not HAS_APSCHEDULER or not self.scheduler:
            return
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("备份调度器已停止")

    def trigger_backup(self, backup_type: BackupType = BackupType.FULL):
        """
        手动触发备份

        Args:
            backup_type: 备份类型
        """
        if backup_type == BackupType.FULL:
            self._run_full_backup()
        else:
            self._run_incremental_backup()

    def get_next_run_times(self):
        """获取下次执行时间"""
        if not HAS_APSCHEDULER or not self.scheduler:
            return {}
        jobs = self.scheduler.get_jobs()
        return {
            job.name: job.next_run_time.isoformat() if job.next_run_time else None
            for job in jobs
        }


# 全局调度器实例
backup_scheduler = BackupScheduler()
