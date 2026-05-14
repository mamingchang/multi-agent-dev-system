# Celery任务队列使用指南

## 概述

Celery是一个分布式任务队列系统，用于异步执行工作流任务。

## 架构

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   FastAPI   │─────>│    Redis    │<─────│   Worker    │
│   (API)     │      │  (Broker)   │      │  (执行器)   │
└─────────────┘      └─────────────┘      └─────────────┘
       │                     │                     │
       │                     │                     │
       └─────────────────────┴─────────────────────┘
                          │
                   ┌──────┴──────┐
                   │   Backend   │
                   │   (Redis)   │
                   └─────────────┘
```

## 安装依赖

```bash
pip install celery[redis] redis
```

## 启动服务

### 1. 启动Redis

```bash
# 方式1：直接启动
redis-server

# 方式2：使用Docker
docker run -d -p 6379:6379 redis

# 验证Redis运行
redis-cli ping
# 应该返回: PONG
```

### 2. 启动Celery Worker

```bash
# 在项目根目录执行
celery -A src.celery_config worker --loglevel=info

# 指定队列
celery -A src.celery_config worker -Q workflow,notification --loglevel=info

# 指定并发数
celery -A src.celery_config worker --concurrency=4 --loglevel=info
```

### 3. 启动Celery Beat（定时任务调度器）

```bash
celery -A src.celery_config beat --loglevel=info
```

### 4. 启动Flower（监控界面，可选）

```bash
# 安装Flower
pip install flower

# 启动
celery -A src.celery_config flower

# 访问 http://localhost:5555
```

## 使用API

### 1. 创建并执行任务

```bash
# 1. 创建任务
curl -X POST http://localhost:8000/celery/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "session_id": "session-xxx",
    "title": "实现登录功能",
    "description": "实现用户登录功能"
  }'

# 返回: {"id": "task-xxx", ...}

# 2. 执行任务
curl -X POST http://localhost:8000/celery/tasks/task-xxx/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{}'

# 返回: {"celery_task_id": "abc-123-def", "status": "submitted", ...}
```

### 2. 查询任务状态

```bash
curl http://localhost:8000/celery/tasks/abc-123-def/status \
  -H "Authorization: Bearer YOUR_TOKEN"

# 返回:
# {
#   "celery_task_id": "abc-123-def",
#   "state": "PROGRESS",
#   "ready": false,
#   "progress": {"status": "executing", "progress": 50}
# }
```

### 3. 撤销任务

```bash
# 软撤销（标记为撤销，但不强制终止）
curl -X POST http://localhost:8000/celery/tasks/abc-123-def/revoke \
  -H "Authorization: Bearer YOUR_TOKEN"

# 强制终止
curl -X POST "http://localhost:8000/celery/tasks/abc-123-def/revoke?terminate=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. 查看Worker状态

```bash
curl http://localhost:8000/celery/workers/status \
  -H "Authorization: Bearer YOUR_TOKEN"

# 返回:
# {
#   "active_workers": ["celery@hostname"],
#   "worker_count": 1,
#   "registered_tasks": {...},
#   "stats": {...}
# }
```

### 5. 查看队列统计

```bash
curl http://localhost:8000/celery/queue/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 任务类型

### 1. 工作流执行任务

```python
from src.tasks.workflow_tasks import execute_workflow_task

# 异步执行
result = execute_workflow_task.delay(
    task_id="task-xxx",
    db_url="sqlite:///./test.db"
)

# 获取结果
task_result = result.get(timeout=3600)
```

### 2. 邮件通知任务

```python
from src.tasks.workflow_tasks import send_email_notification

result = send_email_notification.delay(
    to_email="user@example.com",
    subject="任务完成通知",
    content="您的任务已完成"
)
```

### 3. 清理过期任务（定时任务）

```python
from src.tasks.workflow_tasks import cleanup_expired_tasks

# 手动触发
result = cleanup_expired_tasks.delay(days=30)

# 自动执行：每2小时执行一次
```

### 4. 生成每日报告（定时任务）

```python
from src.tasks.workflow_tasks import generate_daily_report

# 手动触发
result = generate_daily_report.delay(date="2026-05-08")

# 自动执行：每天执行一次
```

## 配置

### 环境变量

```bash
# Redis URL
export REDIS_URL="redis://localhost:6379/0"

# 数据库URL
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
```

### Celery配置

编辑 `src/celery_config.py`:

```python
celery_app.conf.update(
    # 任务结果保留时间
    result_expires=3600,  # 1小时
    
    # 最大重试次数
    task_max_retries=3,
    
    # Worker配置
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # 任务路由
    task_routes={
        'src.tasks.workflow.*': {'queue': 'workflow'},
        'src.tasks.notification.*': {'queue': 'notification'},
    }
)
```

## 监控和调试

### 查看任务日志

```bash
# Worker日志
celery -A src.celery_config worker --loglevel=debug

# 查看特定任务
celery -A src.celery_config inspect active
celery -A src.celery_config inspect scheduled
celery -A src.celery_config inspect reserved
```

### 使用Flower监控

访问 http://localhost:5555 查看:
- 实时任务状态
- Worker状态
- 任务历史
- 任务统计图表

### 清空队列

```bash
# 清空所有队列
celery -A src.celery_config purge

# 清空特定队列
celery -A src.celery_config purge -Q workflow
```

## 生产环境部署

### 使用Supervisor管理进程

创建 `/etc/supervisor/conf.d/celery.conf`:

```ini
[program:celery-worker]
command=celery -A src.celery_config worker --loglevel=info
directory=/path/to/project
user=www-data
numprocs=1
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker_error.log

[program:celery-beat]
command=celery -A src.celery_config beat --loglevel=info
directory=/path/to/project
user=www-data
numprocs=1
autostart=true
autorestart=true
startsecs=10
stdout_logfile=/var/log/celery/beat.log
stderr_logfile=/var/log/celery/beat_error.log
```

### 使用systemd管理

创建 `/etc/systemd/system/celery-worker.service`:

```ini
[Unit]
Description=Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/project
ExecStart=/path/to/venv/bin/celery -A src.celery_config worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:

```bash
sudo systemctl enable celery-worker
sudo systemctl start celery-worker
sudo systemctl status celery-worker
```

## 常见问题

### 1. 任务一直处于PENDING状态

**原因**: Worker未启动或未连接到Broker

**解决**:
```bash
# 检查Redis
redis-cli ping

# 检查Worker
celery -A src.celery_config inspect active
```

### 2. 任务执行失败

**原因**: 代码错误或依赖缺失

**解决**:
```bash
# 查看详细日志
celery -A src.celery_config worker --loglevel=debug

# 查看任务错误
from celery.result import AsyncResult
result = AsyncResult('task-id')
print(result.traceback)
```

### 3. 内存占用过高

**原因**: Worker执行太多任务未重启

**解决**:
```python
# 配置worker定期重启
celery_app.conf.worker_max_tasks_per_child = 1000
```

### 4. 任务重复执行

**原因**: 多个Worker或Beat实例

**解决**:
- 确保只有一个Beat实例
- 使用分布式锁（Redis）

## 最佳实践

1. **任务幂等性**: 确保任务可以安全重试
2. **超时设置**: 为长时间任务设置超时
3. **错误处理**: 捕获异常并记录日志
4. **监控告警**: 使用Flower或Prometheus监控
5. **资源限制**: 限制并发数和内存使用
6. **队列分离**: 不同优先级任务使用不同队列

## 参考资料

- [Celery官方文档](https://docs.celeryproject.org/)
- [Redis官方文档](https://redis.io/documentation)
- [Flower文档](https://flower.readthedocs.io/)
