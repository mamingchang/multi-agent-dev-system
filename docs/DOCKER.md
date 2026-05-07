# Docker部署指南

## 快速启动（推荐）

### 一键启动

```bash
./docker-start.sh
```

这个脚本会自动：
1. 检查Docker环境
2. 创建数据目录
3. 构建Docker镜像
4. 初始化数据库
5. 启动所有服务

### 访问系统

- **前端**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 手动启动

### 1. 准备环境

```bash
# 创建数据目录
mkdir -p data

# 配置环境变量（可选）
cp .env.docker .env
# 编辑.env，填入Claude API密钥
```

### 2. 构建镜像

```bash
docker-compose build
```

### 3. 初始化数据库

```bash
docker-compose run --rm db-init
```

### 4. 启动服务

```bash
docker-compose up -d
```

### 5. 查看状态

```bash
docker-compose ps
```

## 常用命令

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看后端日志
docker-compose logs -f backend

# 查看前端日志
docker-compose logs -f frontend
```

### 停止服务

```bash
# 停止但保留容器
docker-compose stop

# 停止并删除容器
docker-compose down

# 停止并删除容器和数据卷
docker-compose down -v
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启单个服务
docker-compose restart backend
```

### 进入容器

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入前端容器
docker-compose exec frontend sh
```

### 查看资源使用

```bash
docker stats
```

## 服务说明

### 后端服务 (backend)

- **端口**: 8000
- **镜像**: Python 3.10
- **数据卷**: 
  - `./data:/app/data` - 数据库文件
  - `./src:/app/src` - 源代码（热重载）
  - `./backend:/app/backend` - 后端代码（热重载）

### 前端服务 (frontend)

- **端口**: 3000
- **镜像**: Node 20
- **数据卷**:
  - `./frontend/src:/app/src` - 源代码（热重载）
  - `./frontend/public:/app/public` - 静态资源

### 数据库初始化 (db-init)

- **运行方式**: 一次性
- **作用**: 创建SQLite数据库表结构

## 配置说明

### 环境变量

编辑 `.env.docker` 或在 `docker-compose.yml` 中修改：

```yaml
environment:
  - ANTHROPIC_API_KEY=your_api_key_here  # Claude API密钥
  - SECRET_KEY=your-secret-key           # JWT密钥
  - DATABASE_URL=sqlite:////app/data/multi_agent_dev.db
```

### 端口映射

如果端口冲突，修改 `docker-compose.yml`：

```yaml
ports:
  - "8001:8000"  # 将后端映射到8001
  - "3001:3000"  # 将前端映射到3001
```

### 数据持久化

数据库文件保存在 `./data` 目录：

```bash
ls -la data/
# multi_agent_dev.db - SQLite数据库
```

## 开发模式

Docker配置支持热重载：

1. **后端**: 修改 `src/` 或 `backend/` 下的文件会自动重启
2. **前端**: 修改 `frontend/src/` 下的文件会自动刷新

## 生产部署

### 1. 修改配置

```yaml
# docker-compose.prod.yml
services:
  backend:
    environment:
      - SECRET_KEY=${SECRET_KEY}  # 使用强密钥
    restart: always
    
  frontend:
    command: npm run build && npm run preview
    restart: always
```

### 2. 使用生产配置

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 3. 配置Nginx反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

## 故障排查

### 1. 端口被占用

```bash
# 查看端口占用
lsof -i :8000
lsof -i :3000

# 修改docker-compose.yml中的端口映射
```

### 2. 数据库初始化失败

```bash
# 删除旧数据库
rm -rf data/multi_agent_dev.db

# 重新初始化
docker-compose run --rm db-init
```

### 3. 容器无法启动

```bash
# 查看详细日志
docker-compose logs backend
docker-compose logs frontend

# 重新构建
docker-compose build --no-cache
```

### 4. 前端无法连接后端

检查 `frontend/src/api/client.js` 中的API地址：

```javascript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

### 5. 权限问题

```bash
# 修复数据目录权限
sudo chown -R $USER:$USER data/
```

## 清理环境

### 停止并删除所有容器

```bash
docker-compose down
```

### 删除镜像

```bash
docker-compose down --rmi all
```

### 完全清理（包括数据）

```bash
docker-compose down -v
rm -rf data/
```

## 性能优化

### 1. 使用多阶段构建

```dockerfile
# 生产环境Dockerfile
FROM python:3.10-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.10-slim
COPY --from=builder /root/.local /root/.local
COPY . .
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0"]
```

### 2. 限制资源

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

## 监控

### 查看资源使用

```bash
docker stats multi-agent-backend multi-agent-frontend
```

### 健康检查

```bash
# 后端健康检查
curl http://localhost:8000/health

# 查看容器健康状态
docker-compose ps
```

## 备份和恢复

### 备份数据库

```bash
# 备份
cp data/multi_agent_dev.db data/backup_$(date +%Y%m%d).db

# 或使用tar
tar -czf backup_$(date +%Y%m%d).tar.gz data/
```

### 恢复数据库

```bash
# 停止服务
docker-compose down

# 恢复数据
cp data/backup_20260507.db data/multi_agent_dev.db

# 重启服务
docker-compose up -d
```

## 总结

Docker环境提供：
- ✅ 完全隔离的测试环境
- ✅ 一键启动和停止
- ✅ 数据持久化
- ✅ 热重载开发模式
- ✅ 易于清理和重置

开始使用：
```bash
./docker-start.sh
```
