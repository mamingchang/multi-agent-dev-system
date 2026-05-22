# Agent注册系统使用指南

## 概述

Agent注册系统提供了灵活的Agent管理能力，支持：
- **4种注册方式**：模板创建、交互式创建、文件导入、复制已有Agent
- **能力隔离**：基于角色的工具/技能/插件过滤
- **数据隔离**：每个Agent独立的数据目录
- **配置管理**：YAML格式的配置文件，支持版本控制

## 核心组件

### 1. CapabilityLoader（能力加载器）

负责加载和过滤Agent的能力：

```python
from src.agents.capability_loader import CapabilityLoader

# 创建加载器
loader = CapabilityLoader(agent_config)

# 加载工具（应用白名单/黑名单过滤）
tools = loader.load_tools()

# 加载技能
skills = loader.load_skills()

# 加载插件
plugins = loader.load_plugins()

# 加载MCP服务器
mcp_servers = loader.load_mcp_servers()

# 获取数据路径
data_paths = loader.get_data_paths()
```

**工作流程**：
1. 加载全局工具（如果`inherit_global=true`）
2. 加载角色专属工具（从`tools/roles/{role}/`）
3. 应用白名单过滤（优先级最高）
4. 应用黑名单过滤

### 2. AgentRegistration（注册管理器）

负责Agent的CRUD操作：

```python
from src.agents.registration import AgentRegistration

registration = AgentRegistration()

# 从模板创建
config = registration.register_from_template(
    agent_name="pm1",
    template_name="product_manager",
    overrides={"description": "我的产品经理"}
)

# 列出所有Agent
agents = registration.list_agents()

# 加载配置
config = registration.load_config("pm1")

# 更新配置
config = registration.update_config("pm1", {"llm": {"temperature": 0.8}})

# 注销Agent
registration.unregister("pm1", backup=True)
```

## 使用方式

### 方式1：CLI命令

```bash
# 从模板创建Agent
python cli/agent_commands.py register --method template --name pm1 --template product_manager

# 交互式创建
python cli/agent_commands.py register --method interactive

# 从文件导入
python cli/agent_commands.py register --method file --file my_agent.yaml

# 从已有Agent复制
python cli/agent_commands.py register --method existing --name dev2 --source dev1

# 列出所有Agent
python cli/agent_commands.py list

# 显示Agent详情
python cli/agent_commands.py show pm1

# 更新Agent配置
python cli/agent_commands.py update pm1 --set description="新描述" --set llm.temperature=0.8

# 注销Agent
python cli/agent_commands.py unregister pm1
```

### 方式2：Web API

```bash
# 启动API服务器
uvicorn api.main:app --reload

# 注册Agent
curl -X POST http://localhost:8000/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "method": "template",
    "name": "pm1",
    "template": "product_manager",
    "overrides": {"description": "我的产品经理"}
  }'

# 列出所有Agent
curl http://localhost:8000/api/agents

# 获取Agent详情
curl http://localhost:8000/api/agents/pm1

# 更新Agent
curl -X PUT http://localhost:8000/api/agents/pm1 \
  -H "Content-Type: application/json" \
  -d '{
    "updates": {
      "description": "新描述",
      "llm": {"temperature": 0.8}
    }
  }'

# 注销Agent
curl -X DELETE http://localhost:8000/api/agents/pm1?backup=true

# 列出可用模板
curl http://localhost:8000/api/agents/templates/list

# 获取模板详情
curl http://localhost:8000/api/agents/templates/product_manager
```

### 方式3：Python代码

```python
from src.agents.registration import AgentRegistration
from src.agents.base_agent import BaseAgent

# 1. 注册Agent
registration = AgentRegistration()
config = registration.register_from_template(
    agent_name="pm1",
    template_name="product_manager"
)

# 2. 创建Agent实例
agent = BaseAgent(
    name=config['name'],
    role=config['role'],
    config=config,  # 传入完整配置
    llm_client=llm_client
)

# 3. Agent会自动加载能力
print(f"工具: {len(agent.tools)}")
print(f"技能: {len(agent.skills)}")
print(f"数据路径: {agent.data_paths['root']}")

# 4. 使用Agent
result = agent.process(task)
```

## 配置文件格式

Agent配置文件（YAML格式）：

```yaml
name: pm1
role: product_manager
description: 产品经理Agent

# 工具配置
tools:
  inherit_global: true  # 继承全局工具
  role_specific_path: tools/roles/product_manager  # 可选
  whitelist:  # 白名单（优先级高）
    - read_file
    - write_file
  blacklist:  # 黑名单
    - execute_code
    - deploy

# 技能配置
skills:
  load_from:
    - global
    - project
    - roles/product_manager
  whitelist: []
  blacklist:
    - code_review

# 插件配置
plugins:
  enabled:
    - jira_integration
    - confluence_integration
  disabled: []

# MCP服务器配置
mcp_servers:
  - name: requirements_db
    enabled: true
    config:
      host: localhost
      port: 5432

# 数据路径配置
data:
  root_path: data/agents/pm1  # 可选，默认为 data/agents/{name}
  isolated: true

# LLM配置
llm:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  temperature: 0.7
  max_tokens: 4096

# 记忆系统配置
memory:
  short_term_capacity: 10
  long_term_enabled: true
  working_memory_enabled: true

# 提示词配置
prompts:
  system_prompt: |
    你是一个专业的产品经理Agent...
  role_persistence: |
    记住：你是产品经理，专注于需求分析...

# 协作配置
collaboration:
  can_collaborate_with:
    - architect
    - developer
    - tester
  output_format: markdown
  requires_human_review: true

# 元数据（自动生成）
metadata:
  created_at: "2026-05-20T10:30:00"
  created_from: template
  template: product_manager
  version: "1.0.0"
```

## 目录结构

```
multi-agent-dev-system/
├── config/
│   ├── agents/              # Agent配置文件
│   │   ├── pm1.yaml
│   │   ├── dev1.yaml
│   │   └── backups/         # 备份目录
│   └── templates/           # Agent模板
│       ├── product_manager.yaml
│       ├── developer.yaml
│       ├── architect.yaml
│       └── tester.yaml
├── src/
│   ├── agents/
│   │   ├── capability_loader.py  # 能力加载器
│   │   ├── registration.py       # 注册管理器
│   │   └── base_agent.py         # 基础Agent类
│   ├── tools/
│   │   ├── global/          # 全局工具
│   │   └── roles/           # 角色专属工具
│   │       ├── product_manager/
│   │       ├── developer/
│   │       └── tester/
│   └── skills/
│       ├── global/          # 全局技能
│       ├── project/         # 项目技能
│       └── roles/           # 角色专属技能
├── data/
│   └── agents/              # Agent数据目录（隔离）
│       ├── pm1/
│       │   ├── memory/
│       │   ├── cache/
│       │   └── logs/
│       └── dev1/
├── cli/
│   └── agent_commands.py    # CLI命令
└── api/
    └── agent_routes.py      # Web API
```

## 能力过滤规则

### 工具过滤

1. **继承全局工具**（`inherit_global: true`）
   - 加载 `tools/global/` 下的所有工具

2. **加载角色专属工具**
   - 从 `tools/roles/{role}/` 加载
   - 或从 `role_specific_path` 指定的路径加载

3. **应用白名单**（优先级最高）
   - 如果设置了 `whitelist`，只保留白名单中的工具
   - 白名单为空或null时，不过滤

4. **应用黑名单**
   - 移除 `blacklist` 中的工具

### 技能过滤

1. **从指定路径加载**（`load_from`）
   - `global` → `skills/global/`
   - `project` → `skills/project/`
   - `roles/xxx` → `skills/roles/xxx/`

2. **应用白名单和黑名单**（同工具过滤）

### 插件过滤

- 只加载 `enabled` 列表中的插件
- 排除 `disabled` 列表中的插件

### MCP服务器过滤

- 只加载 `enabled: true` 的服务器

## 最佳实践

### 1. 使用模板创建Agent

模板提供了预配置的角色设置，减少配置工作：

```bash
# 创建产品经理Agent
python cli/agent_commands.py register --method template --name pm1 --template product_manager

# 覆盖部分配置
python cli/agent_commands.py register --method template --name pm2 --template product_manager \
  --override description="专注于移动端产品" \
  --override llm.temperature=0.8
```

### 2. 角色专属能力

为不同角色创建专属工具和技能：

```
src/tools/roles/
├── product_manager/
│   ├── jira_tool.py
│   └── user_story_tool.py
├── developer/
│   ├── git_tool.py
│   └── test_runner_tool.py
└── tester/
    ├── test_case_tool.py
    └── bug_report_tool.py
```

### 3. 数据隔离

每个Agent有独立的数据目录，避免数据冲突：

```python
# Agent的数据路径
data_paths = agent.data_paths
# {
#   'root': Path('data/agents/pm1'),
#   'memory': Path('data/agents/pm1/memory'),
#   'cache': Path('data/agents/pm1/cache'),
#   'logs': Path('data/agents/pm1/logs')
# }

# 保存Agent专属数据
memory_file = data_paths['memory'] / 'requirements.json'
memory_file.write_text(json.dumps(requirements))
```

### 4. 版本控制

配置文件支持版本控制：

```yaml
metadata:
  version: "1.2.3"
  updated_at: "2026-05-20T15:30:00"
```

每次更新会自动递增版本号（1.0.0 → 1.0.1 → 1.0.2）。

### 5. 配置备份

注销Agent时自动备份配置：

```bash
# 备份到 config/agents/backups/pm1_20260520_153000.yaml
python cli/agent_commands.py unregister pm1

# 不备份
python cli/agent_commands.py unregister pm1 --no-backup
```

## 测试

运行测试验证系统：

```bash
# 运行所有测试
python3 tests/test_agent_registration.py

# 预期输出：
# ============================================================
# Agent注册系统测试
# ============================================================
# 
# === 测试1：从模板创建Agent ===
# ✓ 创建成功: pm_test
# 
# === 测试2：CapabilityLoader加载能力 ===
# ✓ 加载工具: 0个
# ✓ 加载技能: 0个
# ...
# 
# ============================================================
# 测试结果汇总
# ============================================================
# 通过: 6/6
# ✓ 所有测试通过
```

## 下一步

1. **创建更多模板**：为所有7个角色创建模板
2. **实现工具和技能**：在 `tools/roles/` 和 `skills/roles/` 下实现具体能力
3. **集成到Orchestrator**：让Orchestrator使用注册系统创建Agent
4. **Web界面**：创建Agent管理的Web UI

## 常见问题

### Q: 如何添加新的工具？

A: 在 `src/tools/global/` 或 `src/tools/roles/{role}/` 下创建Python文件：

```python
# src/tools/roles/developer/git_tool.py

class GitTool:
    def commit(self, message: str):
        # 实现git commit
        pass

    def push(self):
        # 实现git push
        pass
```

工具会被自动发现和加载（文件名以Tool结尾）。

### Q: 如何限制Agent只能使用特定工具？

A: 使用白名单：

```yaml
tools:
  inherit_global: true
  whitelist:
    - read_file
    - write_file
    - search_files
```

### Q: 如何禁止Agent使用某些工具？

A: 使用黑名单：

```yaml
tools:
  inherit_global: true
  blacklist:
    - execute_code  # 禁止执行代码
    - deploy        # 禁止部署
```

### Q: 白名单和黑名单可以同时使用吗？

A: 可以，但白名单优先级更高。如果设置了白名单，黑名单会被忽略。

### Q: 如何查看Agent加载了哪些能力？

A: 使用CLI命令：

```bash
python cli/agent_commands.py show pm1
```

或在代码中：

```python
print(f"工具: {list(agent.tools.keys())}")
print(f"技能: {list(agent.skills.keys())}")
```

## 总结

Agent注册系统提供了：
- ✅ 灵活的Agent创建方式（4种）
- ✅ 基于角色的能力隔离
- ✅ 白名单/黑名单过滤
- ✅ 数据路径隔离
- ✅ 配置版本控制
- ✅ CLI和Web API支持
- ✅ 完整的测试覆盖

这为多Agent协作系统提供了坚实的基础。
