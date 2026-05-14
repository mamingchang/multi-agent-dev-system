"""
任务失败补偿机制

当任务执行失败时，自动执行补偿操作，清理临时资源和回滚数据变更。

补偿内容：
1. 清理临时文件
2. 清理Redis缓存
3. 清理数据库临时记录
4. 回滚数据变更（如果任务部分完成）
5. 记录失败原因到审计日志
6. 发送失败通知
"""

import os
import shutil
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from ..database.models import Task, TaskStatus, AuditAction
from ..api.audit_helper import log_audit
from ..api.notification_helper import send_task_notification


class CompensationContext:
    """
    补偿上下文

    记录任务执行过程中创建的资源，用于失败时清理。
    """

    def __init__(self, task_id: str):
        """
        初始化补偿上下文

        Args:
            task_id: 任务ID
        """
        self.task_id = task_id
        self.temp_files: List[str] = []  # 临时文件路径列表
        self.temp_dirs: List[str] = []  # 临时目录路径列表
        self.redis_keys: List[str] = []  # Redis键列表
        self.db_records: List[Dict[str, Any]] = []  # 数据库记录列表
        self.rollback_actions: List[callable] = []  # 回滚操作列表

    def add_temp_file(self, file_path: str):
        """
        添加临时文件

        Args:
            file_path: 文件路径
        """
        self.temp_files.append(file_path)

    def add_temp_dir(self, dir_path: str):
        """
        添加临时目录

        Args:
            dir_path: 目录路径
        """
        self.temp_dirs.append(dir_path)

    def add_redis_key(self, key: str):
        """
        添加Redis键

        Args:
            key: Redis键
        """
        self.redis_keys.append(key)

    def add_db_record(self, table: str, record_id: Any):
        """
        添加数据库记录

        Args:
            table: 表名
            record_id: 记录ID
        """
        self.db_records.append({
            "table": table,
            "record_id": record_id
        })

    def add_rollback_action(self, action: callable):
        """
        添加回滚操作

        Args:
            action: 回滚操作函数
        """
        self.rollback_actions.append(action)

    def get_summary(self) -> Dict[str, Any]:
        """
        获取补偿上下文摘要

        Returns:
            dict: 摘要信息
        """
        return {
            "task_id": self.task_id,
            "temp_files_count": len(self.temp_files),
            "temp_dirs_count": len(self.temp_dirs),
            "redis_keys_count": len(self.redis_keys),
            "db_records_count": len(self.db_records),
            "rollback_actions_count": len(self.rollback_actions)
        }


class CompensationHandler:
    """
    补偿处理器

    执行任务失败后的补偿操作。
    """

    @staticmethod
    def compensate(
        session: Session,
        task_id: str,
        error_message: str,
        context: Optional[CompensationContext] = None,
        user_id: Optional[int] = None,
        organization_id: Optional[int] = None
    ):
        """
        执行补偿操作

        Args:
            session: 数据库会话
            task_id: 任务ID
            error_message: 错误消息
            context: 补偿上下文（可选）
            user_id: 用户ID（可选）
            organization_id: 组织ID（可选）
        """
        print(f"\n=== 开始执行任务补偿 [任务 {task_id}] ===")

        compensation_results = {
            "temp_files_cleaned": 0,
            "temp_dirs_cleaned": 0,
            "redis_keys_cleaned": 0,
            "db_records_cleaned": 0,
            "rollback_actions_executed": 0,
            "errors": []
        }

        # 1. 清理临时文件
        if context and context.temp_files:
            print(f"清理 {len(context.temp_files)} 个临时文件...")
            for file_path in context.temp_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        compensation_results["temp_files_cleaned"] += 1
                        print(f"  ✓ 删除文件: {file_path}")
                except Exception as e:
                    error_msg = f"删除文件失败 {file_path}: {str(e)}"
                    compensation_results["errors"].append(error_msg)
                    print(f"  ✗ {error_msg}")

        # 2. 清理临时目录
        if context and context.temp_dirs:
            print(f"清理 {len(context.temp_dirs)} 个临时目录...")
            for dir_path in context.temp_dirs:
                try:
                    if os.path.exists(dir_path):
                        shutil.rmtree(dir_path)
                        compensation_results["temp_dirs_cleaned"] += 1
                        print(f"  ✓ 删除目录: {dir_path}")
                except Exception as e:
                    error_msg = f"删除目录失败 {dir_path}: {str(e)}"
                    compensation_results["errors"].append(error_msg)
                    print(f"  ✗ {error_msg}")

        # 3. 清理Redis缓存
        if context and context.redis_keys:
            print(f"清理 {len(context.redis_keys)} 个Redis键...")
            # TODO: 实现Redis清理
            # 这里需要Redis客户端实例
            print("  ⚠ Redis清理功能待实现")

        # 4. 清理数据库临时记录
        if context and context.db_records:
            print(f"清理 {len(context.db_records)} 条数据库记录...")
            # TODO: 实现数据库记录清理
            # 这里需要根据表名和记录ID删除记录
            print("  ⚠ 数据库记录清理功能待实现")

        # 5. 执行回滚操作
        if context and context.rollback_actions:
            print(f"执行 {len(context.rollback_actions)} 个回滚操作...")
            for action in context.rollback_actions:
                try:
                    action()
                    compensation_results["rollback_actions_executed"] += 1
                    print(f"  ✓ 回滚操作执行成功")
                except Exception as e:
                    error_msg = f"回滚操作失败: {str(e)}"
                    compensation_results["errors"].append(error_msg)
                    print(f"  ✗ {error_msg}")

        # 6. 更新任务状态
        try:
            task = session.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = TaskStatus.FAILED
                task.error_message = error_message
                task.updated_at = datetime.utcnow()
                session.commit()
                print(f"  ✓ 任务状态已更新为FAILED")
        except Exception as e:
            error_msg = f"更新任务状态失败: {str(e)}"
            compensation_results["errors"].append(error_msg)
            print(f"  ✗ {error_msg}")

        # 7. 记录审计日志
        try:
            log_audit(
                session=session,
                action=AuditAction.TASK_FAILED,
                resource_type="task",
                resource_id=task_id,
                user_id=user_id,
                organization_id=organization_id,
                details={
                    "error_message": error_message,
                    "compensation_results": compensation_results
                }
            )
            print(f"  ✓ 审计日志已记录")
        except Exception as e:
            error_msg = f"记录审计日志失败: {str(e)}"
            compensation_results["errors"].append(error_msg)
            print(f"  ✗ {error_msg}")

        # 8. 发送失败通知
        if user_id:
            try:
                # TODO: 获取任务和项目信息
                # send_task_notification(
                #     session=session,
                #     user_id=user_id,
                #     task_id=task_id,
                #     task_title="任务标题",
                #     project_name="项目名称",
                #     status="failed",
                #     error_message=error_message
                # )
                print(f"  ⚠ 任务失败通知功能待完善")
            except Exception as e:
                error_msg = f"发送失败通知失败: {str(e)}"
                compensation_results["errors"].append(error_msg)
                print(f"  ✗ {error_msg}")

        print(f"\n=== 补偿操作完成 ===")
        print(f"清理结果: {compensation_results}")

        return compensation_results


def with_compensation(func):
    """
    补偿装饰器

    自动为函数添加补偿机制，失败时执行补偿操作。

    Example:
        @with_compensation
        def execute_task(session, task_id):
            # 任务执行代码
            pass
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 尝试从参数中提取session和task_id
        session = kwargs.get('session') or (args[0] if len(args) > 0 else None)
        task_id = kwargs.get('task_id') or (args[1] if len(args) > 1 else None)

        # 创建补偿上下文
        context = CompensationContext(task_id) if task_id else None

        # 将上下文添加到kwargs中
        if context:
            kwargs['compensation_context'] = context

        try:
            return func(*args, **kwargs)

        except Exception as e:
            # 执行补偿
            if session and task_id:
                CompensationHandler.compensate(
                    session=session,
                    task_id=task_id,
                    error_message=str(e),
                    context=context
                )

            # 重新抛出异常
            raise

    return wrapper
