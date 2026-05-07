# Backend API

Multi-Agent Dev System 后端API服务

## 技术栈

- **FastAPI** - 现代Python Web框架
- **SQLAlchemy** - ORM
- **SQLite** - 数据库
- **JWT** - 认证
- **Pydantic** - 数据验证

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
python scripts/init_database.py
```

### 3. 启动服务

```bash
cd backend
python main.py
```

或使用uvicorn：

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API端点

### 认证 (`/api/auth`)

- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

### 项目管理 (`/api/projects`)

- `GET /api/projects` - 列出用户的项目
- `POST /api/projects` - 创建项目
- `GET /api/projects/{id}` - 获取项目详情
- `PUT /api/projects/{id}` - 更新项目
- `DELETE /api/projects/{id}` - 删除项目
- `GET /api/projects/{id}/members` - 列出项目成员
- `POST /api/projects/{id}/members` - 添加成员
- `DELETE /api/projects/{id}/members/{uid}` - 移除成员
- `PUT /api/projects/{id}/members/{uid}` - 更新成员角色
- `GET /api/projects/{id}/stats` - 项目统计

### 任务和决策 (`/api`)

- `GET /api/decisions/pending` - 获取待处理决策
- `POST /api/decisions/{id}/resolve` - 解决决策
- `GET /api/tasks/{id}/timeline` - 获取任务时间线

## 认证

API使用JWT Bearer Token认证。

### 获取Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=your_password"
```

### 使用Token

```bash
curl -X GET http://localhost:8000/api/projects \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 配置

在项目根目录创建 `.env` 文件：

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./multi_agent.db
DEBUG=True
```

## 开发

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black backend/
```

### 类型检查

```bash
mypy backend/
```

## 部署

### Docker

```bash
docker build -t multi-agent-backend .
docker run -p 8000:8000 multi-agent-backend
```

### 生产环境

```bash
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 项目结构

```
backend/
├── main.py              # FastAPI应用入口
├── config.py            # 配置
├── dependencies.py      # 依赖注入
└── api/
    ├── auth.py          # 认证API
    ├── projects.py      # 项目管理API
    └── tasks.py         # 任务和决策API
```

## 许可证

MIT
