# Docker快速开始

## 🚀 一键启动

```bash
./docker-start.sh
```

等待几分钟后访问：
- **前端**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 📋 前提条件

- Docker 20.10+
- docker-compose 1.29+

检查安装：
```bash
docker --version
docker-compose --version
```

## 🔧 详细步骤

### 1. 启动服务

```bash
# 方式1: 使用启动脚本（推荐）
./docker-start.sh

# 方式2: 手动启动
docker-compose build
docker-compose run --rm db-init
docker-compose up -d
```

### 2. 测试服务

```bash
./docker-test.sh
```

### 3. 查看日志

```bash
# 所有服务
docker-compose logs -f

# 只看后端
docker-compose logs -f backend

# 只看前端
docker-compose logs -f frontend
```

### 4. 停止服务

```bash
# 停止但保留数据
docker-compose down

# 停止并删除所有数据
docker-compose down -v
rm -rf data/
```

## 📁 目录结构

```
.
├── Dockerfile.backend      # 后端镜像
├── Dockerfile.frontend     # 前端镜像
├── docker-compose.yml      # 服务编排
├── docker-start.sh         # 启动脚本
├── docker-test.sh          # 测试脚本
├── .env.docker             # 环境变量
├── .dockerignore           # 忽略文件
└── data/                   # 数据持久化目录
    └── multi_agent_dev.db  # SQLite数据库
```

## ⚙️ 配置

### 环境变量

编辑 `.env.docker`:

```bash
# Claude API密钥（可选）
ANTHROPIC_API_KEY=your_api_key_here

# JWT密钥（生产环境必须修改）
SECRET_KEY=your-secret-key
```

### 端口修改

如果端口冲突，编辑 `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # 改为8001
  frontend:
    ports:
      - "3001:3000"  # 改为3001
```

## 🔍 故障排查

### 端口被占用

```bash
# 查看占用
lsof -i :8000
lsof -i :3000

# 修改docker-compose.yml中的端口
```

### 服务无法启动

```bash
# 查看详细日志
docker-compose logs backend
docker-compose logs frontend

# 重新构建
docker-compose build --no-cache
docker-compose up -d
```

### 数据库问题

```bash
# 删除并重新初始化
docker-compose down
rm -rf data/
docker-compose run --rm db-init
docker-compose up -d
```

### 前端无法连接后端

检查浏览器控制台，确认API地址正确：
- 应该是 `http://localhost:8000`
- 不是 `http://backend:8000`（容器内部地址）

## 🎯 使用流程

1. **启动服务**: `./docker-start.sh`
2. **访问前端**: http://localhost:3000
3. **注册账号**: 填写用户名、邮箱、密码
4. **创建项目**: 登录后创建第一个项目
5. **创建任务**: 在项目中创建开发任务
6. **查看结果**: 观察Agent执行过程

## 📊 监控

### 查看资源使用

```bash
docker stats
```

### 查看容器状态

```bash
docker-compose ps
```

### 进入容器调试

```bash
# 进入后端
docker-compose exec backend bash

# 进入前端
docker-compose exec frontend sh
```

## 🧹 清理

### 停止服务

```bash
docker-compose down
```

### 删除镜像

```bash
docker-compose down --rmi all
```

### 完全清理

```bash
docker-compose down -v
rm -rf data/
docker system prune -a
```

## 📚 更多文档

- 详细Docker文档: `docs/DOCKER.md`
- 快速启动指南: `QUICKSTART.md`
- 项目状态: `STATUS.md`

## ❓ 常见问题

**Q: 如何修改API密钥？**
A: 编辑 `.env.docker`，重启服务：`docker-compose restart`

**Q: 数据会丢失吗？**
A: 不会，数据保存在 `./data` 目录，除非执行 `docker-compose down -v`

**Q: 如何更新代码？**
A: 修改代码后，Docker会自动热重载（开发模式）

**Q: 生产环境如何部署？**
A: 参考 `docs/DOCKER.md` 的生产部署章节

## 🎉 开始使用

```bash
# 1. 启动
./docker-start.sh

# 2. 测试
./docker-test.sh

# 3. 访问
open http://localhost:3000
```

就这么简单！
