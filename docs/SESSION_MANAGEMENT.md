# Session管理系统详解

## 一、Session管理的必要性

### 原始系统的问题
```python
# 没有Session管理时
orchestrator = Orchestrator()
task = Task(...)
result = orchestrator.execute_workflow(task)
# 程序结束，所有状态丢失 ❌
```

### 有Session管理后
```python
# 有Session管理
session_mgr = SessionManager()
session = session_mgr.create_session(user_id="alice")
orchestrator.execute_workflow(task, session=session)
# 状态自动保存到磁盘 ✅
# 可以随时恢复 ✅
```

## 二、Session管理架构

### 核心组件

```
SessionManager (会话管理器)
    ├── create_session()      # 创建新会话
    ├── get_session()         # 获取会话（内存+磁盘）
    ├── save_session()        # 保存到磁盘
    ├── load_session()        # 从磁盘加载
    ├── list_sessions()       # 列出所有会话
    ├── pause_session()       # 暂停会话
    ├── resume_session()      # 恢复会话
    └── delete_session()      # 删除会话

Session (会话对象)
    ├── session_id            # 唯一标识
    ├── user_id               # 用户标识
    ├── tasks: Dict[str, Task]  # 任务列表
    ├── status                # active/paused/completed/failed
    ├── metadata              # 自定义元数据
    └── timestamps            # 创建/更新时间
```

## 三、Session生命周期

### 1. 创建阶段
```python
session_mgr = SessionManager(storage_path="./sessions")
session = session_mgr.create_session(user_id="user_001")
# 生成UUID: 13f0b194-e2dd-469b-8763-37670eb62687
```

### 2. 执行阶段
```python
orchestrator = Orchestrator(session_manager=session_mgr)
result = orchestrator.execute_workflow(
    task=task,
    session=session,
    auto_save=True  # 每个Agent执行后自动保存
)
```

### 3. 持久化
```json
{
  "session_id": "13f0b194-...",
  "user_id": "user_001",
  "status": "active",
  "tasks": {
    "TASK-001": {
      "title": "开发用户管理系统",
      "status": "in_testing",
      "artifacts": {...},
      "feedback": [...]
    }
  }
}
```

### 4. 恢复阶段
```python
# 程序重启后
session = session_mgr.resume_session("13f0b194-...")
task = session.get_task("TASK-001")
# 继续执行或查看状态
```

## 四、关键特性

### 1. 自动保存机制
```python
# 在Orchestrator中
def execute_workflow(self, task, session, auto_save=True):
    for agent in workflow:
        result = agent.process(task)
        
        # 每个Agent执行后自动保存
        if auto_save and session:
            self.session_manager.save_session(session)
```

**优点**：
- ✅ 防止数据丢失
- ✅ 支持断点续传
- ✅ 可追溯每一步

### 2. 多用户隔离
```python
# 用户A的会话
session_a = session_mgr.create_session(user_id="alice")

# 用户B的会话
session_b = session_mgr.create_session(user_id="bob")

# 查询特定用户的会话
alice_sessions = session_mgr.list_sessions(user_id="alice")
```

### 3. 状态管理
```python
class Session:
    status: str  # active, paused, completed, failed
    
# 暂停会话
session_mgr.pause_session(session_id)

# 恢复会话
session_mgr.resume_session(session_id)
```

### 4. 内存+磁盘双层缓存
```python
def get_session(self, session_id):
    # 1. 先查内存（快速）
    if session_id in self.active_sessions:
        return self.active_sessions[session_id]
    
    # 2. 再查磁盘（持久）
    session = self.load_session(session_id)
    if session:
        self.active_sessions[session_id] = session
    return session
```

## 五、使用场景

### 场景1：长时间运行的任务
```python
# 启动任务
session = session_mgr.create_session()
orchestrator.execute_workflow(task, session)

# 程序崩溃或重启后
session = session_mgr.resume_session(session_id)
# 查看进度，决定是否继续
```

### 场景2：多任务并发
```python
session = session_mgr.create_session()

# 添加多个任务
task1 = Task("TASK-001", "功能A", "...")
task2 = Task("TASK-002", "功能B", "...")

session.add_task(task1)
session.add_task(task2)

# 分别执行
orchestrator.execute_workflow(task1, session)
orchestrator.execute_workflow(task2, session)
```

### 场景3：审计和追溯
```python
# 查看历史会话
sessions = session_mgr.list_sessions(user_id="alice")

for s in sessions:
    session = session_mgr.get_session(s['session_id'])
    for task_id in session.list_tasks():
        task = session.get_task(task_id)
        print(f"任务: {task.title}")
        print(f"状态: {task.status}")
        print(f"反馈: {len(task.feedback)}条")
```

### 场景4：定期清理
```python
# 清理30天前的旧会话
deleted = session_mgr.cleanup_old_sessions(days=30)
```

## 六、存储格式

### 文件结构
```
sessions/
├── 13f0b194-e2dd-469b-8763-37670eb62687.json  # 会话1
├── 5d09ee43-bbf7-40fc-b740-cae30bbfa611.json  # 会话2
└── 89381c97-ff33-4f58-9577-03cd5a61b05c.json  # 会话3
```

### JSON格式
```json
{
  "session_id": "uuid",
  "user_id": "alice",
  "created_at": "2026-05-07T11:40:05",
  "updated_at": "2026-05-07T11:45:30",
  "status": "active",
  "metadata": {},
  "tasks": {
    "TASK-001": {
      "task_id": "TASK-001",
      "title": "开发用户管理系统",
      "status": "in_testing",
      "artifacts": {
        "raw_requirement": {...},
        "prd": {...},
        "architecture": {...},
        "code": {...}
      },
      "feedback": [
        {
          "from": "Tester",
          "to": "Developer",
          "content": "发现1个测试失败",
          "type": "rejection"
        }
      ]
    }
  }
}
```

## 七、与原系统的对比

### 原系统（无Session）
```python
orchestrator = Orchestrator()
task = Task(...)
result = orchestrator.execute_workflow(task)
# ❌ 无法恢复
# ❌ 无法追溯
# ❌ 无法多用户
# ❌ 程序结束即丢失
```

### 新系统（有Session）
```python
session_mgr = SessionManager()
session = session_mgr.create_session(user_id="alice")
orchestrator = Orchestrator(session_manager=session_mgr)
result = orchestrator.execute_workflow(task, session, auto_save=True)
# ✅ 自动保存
# ✅ 可恢复
# ✅ 可追溯
# ✅ 多用户隔离
# ✅ 持久化存储
```

## 八、扩展方向

### 1. 数据库存储
```python
# 当前：JSON文件
# 未来：PostgreSQL/MongoDB
class DatabaseSessionManager(SessionManager):
    def save_session(self, session):
        db.sessions.insert_or_update(session.to_dict())
```

### 2. 分布式Session
```python
# 当前：本地文件
# 未来：Redis/Memcached
class RedisSessionManager(SessionManager):
    def __init__(self):
        self.redis = Redis(host='localhost')
```

### 3. Session共享
```python
# 多个Orchestrator共享同一个Session
orchestrator1.execute_workflow(task1, session)
orchestrator2.execute_workflow(task2, session)
```

### 4. 实时同步
```python
# WebSocket推送Session状态变化
session_mgr.on_session_update(lambda s: ws.send(s.to_dict()))
```

## 九、最佳实践

### 1. 总是使用Session
```python
# ✅ 推荐
session = session_mgr.create_session()
orchestrator.execute_workflow(task, session, auto_save=True)

# ❌ 不推荐（除非是临时测试）
orchestrator.execute_workflow(task)
```

### 2. 合理设置auto_save
```python
# 长时间任务：开启auto_save
orchestrator.execute_workflow(task, session, auto_save=True)

# 短时间任务：手动保存
result = orchestrator.execute_workflow(task, session, auto_save=False)
if result['success']:
    session_mgr.save_session(session)
```

### 3. 定期清理
```python
# 定时任务：每周清理一次
import schedule
schedule.every().week.do(lambda: session_mgr.cleanup_old_sessions(30))
```

### 4. 错误处理
```python
try:
    result = orchestrator.execute_workflow(task, session)
except Exception as e:
    session.status = "failed"
    session.metadata['error'] = str(e)
    session_mgr.save_session(session)
```

## 十、总结

Session管理系统为多Agent系统提供了：

1. **持久化** - 状态不会丢失
2. **可恢复** - 支持断点续传
3. **可追溯** - 完整的历史记录
4. **多用户** - 用户隔离
5. **可扩展** - 易于扩展到分布式

这是生产级系统的必备功能！
