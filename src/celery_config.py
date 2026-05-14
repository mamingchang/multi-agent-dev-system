"""
Celery任务队列配置

使用Celery实现异步任务处理，替代简单的后台任务。

为什么使用Celery：
1. 可靠性：任务持久化，崩溃后可恢复
2. 可扩展：支持分布式worker
3. 监控：提供任务状态追踪
4. 重试：自动重试失败任务
5. 调度：支持定时任务和周期任务

架构：
- Broker：使用Redis存储任务队列
- Backend：使用Redis存储任务结果
- Worker：执行任务的进程
- Beat：定时任务调度器（可选）

安装依赖：
pip install celery[redis]
"""

try:
    from celery import Celery
    HAS_CELERY = True
except ImportError:
    HAS_CELERY = False
    Celery = None

import os

# Redis配置
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# 创建Celery应用
if HAS_CELERY:
    celery_app = Celery(
        'multi_agent_dev_system',
        broker=REDIS_URL,
        backend=REDIS_URL
    )

    # Celery配置
    celery_app.conf.update(
        # 任务序列化
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Asia/Shanghai',
        enable_utc=True,

        # 任务结果配置
        result_expires=3600,  # 结果保留1小时
        result_backend_transport_options={'master_name': 'mymaster'},

        # 任务执行配置
        task_acks_late=True,  # 任务完成后才确认
        task_reject_on_worker_lost=True,  # worker丢失时拒绝任务
        task_track_started=True,  # 追踪任务开始状态

        # 重试配置
        task_default_retry_delay=60,  # 默认重试延迟60秒
        task_max_retries=3,  # 最多重试3次

        # Worker配置
        worker_prefetch_multiplier=1,  # 每次只预取1个任务
        worker_max_tasks_per_child=1000,  # 每个worker最多执行1000个任务后重启

        # 任务路由（可选）
        task_routes={
            'src.tasks.workflow.*': {'queue': 'workflow'},
            'src.tasks.notification.*': {'queue': 'notification'},
        },

        # 任务优先级
        task_default_priority=5,
        broker_transport_options={
            'priority_steps': list(range(10)),
        }
    )

    # 自动发现任务
    celery_app.autodiscover_tasks(['src.tasks'])
else:
    celery_app = None


if __name__ == '__main__':
    # 启动worker
    # celery -A src.celery_config worker --loglevel=info
    if celery_app:
        celery_app.start()

