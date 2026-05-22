# CLI使用快速指南

## 快捷命令

在项目根目录下使用 `./mas` 命令：

```bash
# 查看帮助
./mas --help
./mas agent --help

# 列出所有Agent
./mas agent list
./mas agent list --format json
./mas agent list --format yaml

# 从模板创建Agent
./mas agent register --method template --name pm1 --template product_manager
./mas agent register --method template --name dev1 --template developer

# 交互式创建Agent
./mas agent register --method interactive

# 从已有Agent复制
./mas agent register --method existing --name dev2 --source dev1

# 查看Agent详情
./mas agent show pm1
./mas agent show pm1 --format json

# 更新Agent配置
./mas agent update pm1 --set description="新描述"
./mas agent update pm1 --set llm.temperature=0.8 --set llm.max_tokens=8192

# 注销Agent
./mas agent unregister pm1
./mas agent unregister pm1 --no-backup  # 不备份
```

## 可用模板

- `product_manager` - 产品经理
- `developer` - 开发者

## 示例工作流

```bash
# 1. 创建产品经理Agent
./mas agent register --method template --name pm1 --template product_manager

# 2. 创建开发者Agent
./mas agent register --method template --name dev1 --template developer

# 3. 查看所有Agent
./mas agent list

# 4. 查看dev1的详细配置
./mas agent show dev1

# 5. 更新dev1的描述
./mas agent update dev1 --set description="后端开发工程师"

# 6. 从dev1复制创建dev2
./mas agent register --method existing --name dev2 --source dev1 \
  --override description="前端开发工程师"

# 7. 列出所有Agent（JSON格式）
./mas agent list --format json

# 8. 注销不需要的Agent
./mas agent unregister dev2
```

## 配置文件位置

- Agent配置: `config/agents/{name}.yaml`
- 模板配置: `config/templates/{template}.yaml`
- 备份配置: `config/agents/backups/`

## 数据目录

每个Agent有独立的数据目录：
- `data/agents/{name}/memory/` - 记忆数据
- `data/agents/{name}/cache/` - 缓存数据
- `data/agents/{name}/logs/` - 日志文件
