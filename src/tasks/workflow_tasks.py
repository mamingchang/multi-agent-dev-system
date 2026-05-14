"""
Celery异步任务定义

定义所有异步任务，包括：
1. 工作流执行任务
2. 通知发送任务
3. 数据清理任务
4. 报告生成任务

任务设计原则：
- 幂等性：同一任务多次执行结果相同
- 原子性：任务要么全部成功，要么全部失败
- 可重试：失败后可以安全重试
- 超时控制：避免任务无限执行
"""

from typing import Dict, Any, Optional
import time
from datetime import datetime

from ..celery_config import celery_app, HAS_CELERY
from ..workflow.task import Task
from ..workflow.notifying_orchestrator import NotifyingOrchestrator
from ..database.database import DatabaseManager
from ..database.models import Task as DBTask, TaskStatus as DBTaskStatus


if HAS_CELERY and celery_app:
    @celery_app.task(
        name='workflow.execute_task',
        bind=True,
        max_retries=3,
        soft_time_limit=3600,  # 软超时1小时
        time_limit=3660  # 硬超时1小时1分钟
    )
    def execute_workflow_task(self, task_id: str, db_url: Optional[str] = None) -> Dict[str, Any]:
        """
        执行工作流任务（异步）

        Args:
            self: Celery任务实例
        task_id: 任务ID
        db_url: 数据库URL（可选）

    Returns:
        Dict: 执行结果
        {
            'success': bool,
            'task_id': str,
            'message': str,
            'duration': float
        }

    为什么使用bind=True：
    - 可以访问self.request获取任务信息
    - 可以使用self.retry()重试任务
    - 可以更新任务状态
    """
    start_time = time.time()

    try:
        print(f"[Celery] 开始执行任务: {task_id}")

        # 更新任务状态为执行中
        self.update_state(
            state='PROGRESS',
            meta={'status': 'initializing', 'progress': 0}
        )

        # 从数据库加载任务
        db_manager = DatabaseManager(db_url)
        with db_manager.get_session() as session:
            db_task = session.query(DBTask).filter(DBTask.task_id == task_id).first()

            if not db_task:
                return {
                    'success': False,
                    'task_id': task_id,
                    'message': '任务不存在',
                    'duration': time.time() - start_time
                }

            # 创建工作流任务对象
            task = Task(
                task_id=db_task.task_id,
                title=db_task.title,
                description=db_task.description
            )

            # 更新进度
            self.update_state(
                state='PROGRESS',
                meta={'status': 'loading_agents', 'progress': 10}
            )

            # 创建Agent（这里简化，实际应该从配置加载）
            from ..agents.base_agent import BaseAgent
            from ..llm.llm_client import create_llm_client

            # 使用Mock LLM进行测试
            llm_client = create_llm_client("mock")

            # 创建简单的测试Agent
            class SimpleAgent(BaseAgent):
                def _get_responsibilities(self) -> str:
                    return "执行任务"

                def process(self, task) -> Dict[str, Any]:
                    return {
                        'success': True,
                        'output': f'{self.name}完成工作'
                    }

            agents = [
                SimpleAgent("Agent1", "测试Agent1", llm_client=llm_client)
            ]

            # 更新进度
            self.update_state(
                state='PROGRESS',
                meta={'status': 'executing', 'progress': 30}
            )

            # 创建编排器并执行
            orchestrator = NotifyingOrchestrator(
                agents=agents,
                max_iterations=5,
                enable_notifications=True
            )

            result = orchestrator.execute(task)

            # 更新进度
            self.update_state(
                state='PROGRESS',
                meta={'status': 'saving_results', 'progress': 90}
            )

            # 更新数据库任务状态
            if result['success']:
                db_task.status = DBTaskStatus.COMPLETED
            else:
                db_task.status = DBTaskStatus.FAILED

            db_task.completed_at = datetime.now()
            session.commit()

            duration = time.time() - start_time

            print(f"[Celery] 任务完成: {task_id}, 耗时: {duration:.2f}s")

            return {
                'success': result['success'],
                'task_id': task_id,
                'message': result['message'],
                'duration': duration
            }

    except Exception as e:
        print(f"[Celery] 任务执行失败: {task_id}, 错误: {str(e)}")

        # 重试任务
        try:
            raise self.retry(exc=e, countdown=60)  # 60秒后重试
        except self.MaxRetriesExceededError:
            # 达到最大重试次数
            return {
                'success': False,
                'task_id': task_id,
                'message': f'任务执行失败（已重试{self.request.retries}次）: {str(e)}',
                'duration': time.time() - start_time
            }


@celery_app.task(name='notification.send_email')
def send_email_notification(
    to_email: str,
    subject: str,
    content: str
) -> Dict[str, Any]:
    """
    发送邮件通知（异步）

    Args:
        to_email: 收件人邮箱
        subject: 邮件主题
        content: 邮件内容

    Returns:
        Dict: 发送结果
    """
    try:
        print(f"[Celery] 发送邮件: {to_email}, 主题: {subject}")

        # 这里应该集成实际的邮件服务（如SendGrid, AWS SES等）
        # 现在只是模拟
        time.sleep(1)

        return {
            'success': True,
            'to_email': to_email,
            'message': '邮件发送成功'
        }

    except Exception as e:
        print(f"[Celery] 邮件发送失败: {str(e)}")
        return {
            'success': False,
            'to_email': to_email,
            'message': f'邮件发送失败: {str(e)}'
        }


@celery_app.task(name='cleanup.expired_tasks')
def cleanup_expired_tasks(days: int = 30) -> Dict[str, Any]:
    """
    清理过期任务（定时任务）

    Args:
        days: 保留天数

    Returns:
        Dict: 清理结果
    """
    try:
        print(f"[Celery] 清理{days}天前的任务")

        from datetime import timedelta
        from ..database.database import DatabaseManager
        from ..database.models import Task as DBTask

        db_manager = DatabaseManager()
        with db_manager.get_session() as session:
            cutoff_date = datetime.now() - timedelta(days=days)

            # 查找过期任务
            expired_tasks = session.query(DBTask).filter(
                DBTask.created_at < cutoff_date,
                DBTask.status.in_([DBTaskStatus.COMPLETED, DBTaskStatus.FAILED])
            ).all()

            count = len(expired_tasks)

            # 删除过期任务
            for task in expired_tasks:
                session.delete(task)

            session.commit()

            print(f"[Celery] 清理完成，删除了{count}个任务")

            return {
                'success': True,
                'deleted_count': count,
                'message': f'清理了{count}个过期任务'
            }

    except Exception as e:
        print(f"[Celery] 清理任务失败: {str(e)}")
        return {
            'success': False,
            'message': f'清理失败: {str(e)}'
        }


@celery_app.task(name='report.generate_daily_report')
def generate_daily_report(date: Optional[str] = None) -> Dict[str, Any]:
    """
    生成每日报告（定时任务）

    Args:
        date: 日期（YYYY-MM-DD），默认为昨天

    Returns:
        Dict: 报告生成结果
    """
    try:
        from datetime import date as dt_date, timedelta

        if date is None:
            report_date = dt_date.today() - timedelta(days=1)
        else:
            report_date = dt_date.fromisoformat(date)

        print(f"[Celery] 生成每日报告: {report_date}")

        from ..database.database import DatabaseManager
        from ..database.models import Task as DBTask

        db_manager = DatabaseManager()
        with db_manager.get_session() as session:
            # 统计当天的任务
            tasks = session.query(DBTask).filter(
                DBTask.created_at >= report_date,
                DBTask.created_at < report_date + timedelta(days=1)
            ).all()

            total = len(tasks)
            completed = sum(1 for t in tasks if t.status == DBTaskStatus.COMPLETED)
            failed = sum(1 for t in tasks if t.status == DBTaskStatus.FAILED)
            in_progress = total - completed - failed

            report = {
                'date': report_date.isoformat(),
                'total_tasks': total,
                'completed': completed,
                'failed': failed,
                'in_progress': in_progress,
                'success_rate': completed / total if total > 0 else 0
            }

            print(f"[Celery] 报告生成完成: {report}")

            # 这里可以将报告发送到邮件或存储到文件
            # send_email_notification.delay(
            #     to_email='admin@example.com',
            #     subject=f'每日报告 - {report_date}',
            #     content=json.dumps(report, indent=2)
            # )

            return {
                'success': True,
                'report': report,
                'message': '报告生成成功'
            }

    except Exception as e:
        print(f"[Celery] 报告生成失败: {str(e)}")
        return {
            'success': False,
            'message': f'报告生成失败: {str(e)}'
        }


# 定时任务配置（使用Celery Beat）
celery_app.conf.beat_schedule = {
    # 每天凌晨2点清理过期任务
    'cleanup-expired-tasks': {
        'task': 'cleanup.expired_tasks',
        'schedule': 7200.0,  # 每2小时执行一次（测试用）
        'args': (30,)  # 清理30天前的任务
    },
    # 每天早上8点生成昨日报告
    'generate-daily-report': {
        'task': 'report.generate_daily_report',
        'schedule': 86400.0,  # 每天执行一次
        'args': ()
    },
}
