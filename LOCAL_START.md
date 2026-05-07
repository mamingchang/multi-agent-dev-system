# 本地启动指南

## 🚀 快速启动

### 方式1: 一键启动（推荐）

```bash
./start.sh
```

这会同时启动前后端服务（后台运行）。

### 方式2: 分别启动

**终端1 - 启动后端**:
```bash
./start-backend.sh
```

**终端2 - 启动前端**:
```bash
cd frontend
./start-frontend.sh
```

## 📋 前提条件

### 必须完成

1. **Python依赖安装**:
```bash
python3 -m pip install --user -r requirements.txt
```

2. **前端依赖安装**（已完成）:
```bash
cd frontend
npm install
```

### 可选配置

编辑 `.env` 文件配置API密钥：
```bash
ANTHROPIC_API_KEY=your_api_key_here
```

## 🌐 访问地址

- **前端**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 📊 查看日志

```bash
# 后端日志
tail -f backend.log

# 前端日志
tail -f frontend.log
```

## 🛑 停止服务

```bash
./stop.sh
```

## 🔍 故障排查

### 1. Python依赖未安装

**错误**: `ModuleNotFoundError: No module named 'sqlalchemy'`

**解决**:
```bash
python3 -m pip install --user -r requirements.txt
```

### 2. 端口被占用

**错误**: `Address already in use`

**解决**:
```bash
# 查看占用
lsof -i :8000
lsof -i :3000

# 停止服务
./stop.sh

# 或手动杀死进程
kill -9 <PID>
```

### 3. 数据库未初始化

**错误**: `no such table: users`

**解决**:
```bash
python3 -c "
from sqlalchemy import create_engine
from src.database.models import Base
engine = create_engine('sqlite:///./multi_agent_dev.db')
Base.metadata.create_all(engine)
print('数据库初始化完成')
"
```

### 4. 前端无法连接后端

检查 `frontend/src/api/client.js` 中的API地址：
```javascript
const API_URL = 'http://localhost:8000';
```

## 📝 使用流程

1. **启动服务**: `./start.sh`
2. **访问前端**: http://localhost:3000
3. **注册账号**: 填写用户名、邮箱、密码
4. **创建项目**: 点击"创建项目"
5. **创建任务**: 输入需求描述
6. **执行工作流**: 观察7个Agent执行
7. **查看结果**: 任务时间线和产物

## 🎯 当前状态

- ✅ 启动脚本已创建
- ⏳ Python依赖正在安装中
- ✅ 前端依赖已安装
- ✅ 数据库Schema已定义

## ⏰ 等待依赖安装

Python依赖正在后台安装中，完成后运行：

```bash
# 检查是否安装完成
python3 -c "import sqlalchemy; print('✓ 依赖已安装')"

# 如果成功，启动系统
./start.sh
```

## 📚 更多文档

- 完整使用指南: `QUICKSTART.md`
- 项目状态: `STATUS.md`
- 测试文档: `docs/TESTING.md`
