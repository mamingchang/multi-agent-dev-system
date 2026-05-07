# 快速启动指南

## 项目状态

✅ **已完成**:
- 数据库层（SQLite + SQLAlchemy）
- 7个AI Agent（Requester, PM, Architect, Developer, CodeReviewer, Tester, DevOps）
- 人工Agent系统（同步/异步模式）
- 项目管理和RBAC权限
- 决策队列系统
- 事件日志和追溯
- FastAPI后端API
- React前端界面
- 测试框架

⚠️ **需要配置**:
- Python依赖安装
- 数据库初始化
- 环境变量配置
- API密钥配置（Claude API）

## 安装步骤

### 1. 安装Python依赖

```bash
# 如果有pip
pip install -r requirements.txt

# 或使用系统包管理器
sudo apt install python3-pip
pip3 install -r requirements.txt
```

**主要依赖**:
- fastapi
- uvicorn
- sqlalchemy
- python-jose[cryptography]
- passlib[bcrypt]
- python-multipart
- anthropic (Claude API)

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# API配置
ANTHROPIC_API_KEY=your_claude_api_key_here

# 数据库
DATABASE_URL=sqlite:///./multi_agent_dev.db

# JWT认证
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 服务器
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:3000
```

### 3. 初始化数据库

```bash
python3 -c "
from src.database.models import Base
from src.database.migrations import init_database
from sqlalchemy import create_engine

engine = create_engine('sqlite:///./multi_agent_dev.db')
Base.metadata.create_all(engine)
print('Database initialized successfully!')
"
```

### 4. 启动后端服务

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问: http://localhost:8000/docs (Swagger API文档)

### 5. 启动前端服务

```bash
cd frontend
npm install  # 已完成
npm run dev
```

访问: http://localhost:3000

## 使用流程

### 第一次使用

1. **注册账号**
   - 访问 http://localhost:3000
   - 点击"注册"
   - 填写用户名、邮箱、密码

2. **创建项目**
   - 登录后进入项目列表
   - 点击"创建项目"
   - 填写项目名称和描述
   - 你将自动成为项目Owner

3. **添加团队成员**
   - 进入项目详情
   - 点击"成员管理"
   - 添加成员并分配角色：
     - Owner: 完全控制权
     - Admin: 管理成员和配置
     - Member: 执行任务
     - Viewer: 只读访问

4. **创建任务**
   - 在项目中点击"新建任务"
   - 输入需求描述
   - 选择工作流模式：
     - 全自动：AI Agent自动执行
     - 人工介入：在关键节点需要人工决策

5. **执行工作流**
   - 点击"执行任务"
   - 系统按顺序调用7个Agent：
     1. Requester - 需求分析
     2. ProductManager - 产品设计
     3. Architect - 架构设计
     4. Developer - 代码开发
     5. CodeReviewer - 代码审查
     6. Tester - 测试
     7. DevOps - 部署

6. **处理决策**（如果配置了人工Agent）
   - 进入"决策中心"
   - 查看待办决策
   - 审查Agent的输出
   - 提交批准/拒绝/修改意见

7. **查看追溯**
   - 在任务详情页查看时间线
   - 查看每个Agent的操作历史
   - 查看生成的产物（代码、文档、测试）

## 配置人工介入

编辑 `config/agent_config.json`：

```json
{
  "agents": {
    "Requester": {"mode": "ai"},
    "ProductManager": {"mode": "human", "interaction": "async"},
    "Architect": {"mode": "ai"},
    "Developer": {"mode": "ai"},
    "CodeReviewer": {"mode": "human", "interaction": "sync"},
    "Tester": {"mode": "ai"},
    "DevOps": {"mode": "human", "interaction": "async"}
  }
}
```

**模式说明**:
- `ai`: 完全自动化
- `human` + `async`: 创建待办决策，工作流暂停
- `human` + `sync`: 阻塞等待人工输入

## 命令行使用（无Web界面）

```bash
# 创建会话
python3 -c "
from src.session_manager import SessionManager
from src.orchestrator import Orchestrator

sm = SessionManager()
session = sm.create_session('test-project')
print(f'Session created: {session.session_id}')
"

# 执行任务
python3 examples/run_workflow.py --requirement "创建一个用户登录功能"
```

## 测试系统

```bash
# 运行集成测试
python3 tests/integration_test.py

# 运行单元测试（需要安装pytest）
pytest tests/

# 检查语法
find src backend -name "*.py" -exec python3 -m py_compile {} \;
```

## 常见问题

### 1. 缺少ANTHROPIC_API_KEY

**错误**: `Error: ANTHROPIC_API_KEY not found`

**解决**: 
```bash
export ANTHROPIC_API_KEY=your_key_here
# 或在.env文件中配置
```

### 2. 数据库未初始化

**错误**: `no such table: users`

**解决**: 运行步骤3的数据库初始化命令

### 3. 端口被占用

**错误**: `Address already in use`

**解决**:
```bash
# 更改端口
uvicorn main:app --port 8001
# 或杀死占用进程
lsof -ti:8000 | xargs kill -9
```

### 4. 前端无法连接后端

**错误**: `Network Error`

**解决**: 检查 `frontend/.env`:
```
VITE_API_URL=http://localhost:8000
```

## 架构概览

```
用户 → Web界面 → FastAPI后端 → Orchestrator → Agents
                      ↓
                  SQLite数据库
                      ↓
              事件日志 + 决策队列
```

## 下一步

1. **获取Claude API密钥**: https://console.anthropic.com/
2. **安装Python依赖**: `pip install -r requirements.txt`
3. **初始化数据库**: 运行步骤3
4. **启动服务**: 后端 + 前端
5. **创建第一个项目**: 注册 → 登录 → 创建项目 → 创建任务

## 生产部署

参考 `docs/DEPLOYMENT.md`（待创建）：
- Docker容器化
- Nginx反向代理
- 数据库备份策略
- 监控和日志
- HTTPS配置

## 获取帮助

- 查看API文档: http://localhost:8000/docs
- 查看测试文档: `docs/TESTING.md`
- 查看架构设计: 计划文件中的详细说明
- GitHub Issues: https://github.com/mamingchang/multi-agent-dev-system/issues
