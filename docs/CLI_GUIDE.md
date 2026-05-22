# CLI命令完整指南

Multi-Agent Dev System提供了完整的CLI工具集，让你可以管理Agent、监控任务、运行交互式工作流。

## 快速开始

```bash
# 查看所有命令
./mas --help

# 查看版本
./mas --version
```

## 三大命令组

### 1. Agent管理 (`agent`)

管理Agent的注册、配置和查看。

```bash
# 列出所有已注册的Agent
./mas agent list

# 查看Agent详情
./mas agent show requester

# 注册新Agent（从模板）
./mas agent register --method template --name my_pm --template product_manager

# 更新Agent配置
./mas agent update requester --set description="新的描述"

# 注销Agent
./mas agent unregister my_pm
```

📖 详细文档：`docs/agent_cli_guide.md`

### 2. 任务管理 (`task`)

查看工作流执行状态和Agent回复。

```bash
# 列出所有会话
./mas task list

# 查看最新会话详情
./mas task show --latest

# 查看指定会话
./mas task show 084760cf

# 查看Agent状态摘要
./mas task agents --latest

# 只查看特定Agent的回复
./mas task agents --latest --agent Requester
```

📖 详细文档：`docs/task_cli_guide.md`

### 3. 交互式工作流 (`workflow`)

运行交互式工作流，实时查看Agent输出并提供人工反馈。

```bash
# 运行交互式工作流
./mas workflow run --title "Todo应用" --description "开发一个简单的Todo应用"

# 或使用交互式输入
./mas workflow run

# 实时监控工作流
./mas workflow monitor --latest

# 非交互模式（自动执行）
./mas workflow run --title "..." --description "..." --no-interactive
```

📖 详细文档：`docs/workflow_cli_guide.md`

## 典型工作流

### 场景1：首次使用系统

```bash
# 1. 查看已注册的Agent
./mas agent list

# 2. 如果没有Agent，注册所有需要的Agent
./mas agent register --method template --name requester --template requester
./mas agent register --method template --name product_manager --template product_manager
./mas agent register --method template --name architect --template architect
./mas agent register --method template --name developer --template developer
./mas agent register --method template --name code_reviewer --template code_reviewer
./mas agent register --method template --name tester --template tester
./mas agent register --method template --name devops --template devops

# 3. 运行第一个工作流
./mas workflow run
```

### 场景2：运行交互式开发任务

```bash
# 终端1：运行工作流
./mas workflow run --title "开发Todo应用" --description "..."

# 终端2：实时监控
./mas workflow monitor --latest

# 当系统请求人工介入时：
# - 查看Agent的分析结果
# - 提供反馈或澄清
# - 选择继续/重试/跳过/终止
```

### 场景3：查看历史任务

```bash
# 1. 列出所有会话
./mas task list

# 2. 查看特定会话的详细信息
./mas task show 084760cf

# 3. 查看各Agent的状态
./mas task agents 084760cf

# 4. 只查看某个Agent的回复
./mas task agents 084760cf --agent Developer
```

### 场景4：管理自定义Agent

```bash
# 1. 创建自定义Agent配置文件
cat > my_agent.yaml <<EOF
name: my_custom_agent
role: 自定义角色
description: 我的自定义Agent
llm:
  provider: claude
  model: claude-sonnet-4-5
tools:
  inherit_global: true
  whitelist:
    - file_operations
    - code_analysis
EOF

# 2. 从文件注册
./mas agent register --method file --name my_agent --file my_agent.yaml

# 3. 查看配置
./mas agent show my_agent

# 4. 更新配置
./mas agent update my_agent --set description="更新后的描述"

# 5. 注销
./mas agent unregister my_agent
```

## 命令速查表

| 命令 | 说明 | 示例 |
|------|------|------|
| `agent list` | 列出所有Agent | `./mas agent list` |
| `agent show <name>` | 查看Agent详情 | `./mas agent show requester` |
| `agent register` | 注册新Agent | `./mas agent register --method template --name pm1 --template product_manager` |
| `agent update <name>` | 更新Agent配置 | `./mas agent update requester --set description="新描述"` |
| `agent unregister <name>` | 注销Agent | `./mas agent unregister pm1` |
| `task list` | 列出所有会话 | `./mas task list --limit 20` |
| `task show` | 查看会话详情 | `./mas task show --latest` |
| `task agents` | 查看Agent状态 | `./mas task agents --latest --agent Requester` |
| `workflow run` | 运行交互式工作流 | `./mas workflow run --title "Todo应用" --description "..."` |
| `workflow monitor` | 实时监控工作流 | `./mas workflow monitor --latest` |

## 环境变量

你可以通过环境变量配置CLI行为：

```bash
# 设置会话存储目录（默认：sessions/）
export MAS_SESSION_DIR=/path/to/sessions

# 设置Agent配置目录（默认：config/agents/）
export MAS_AGENT_CONFIG_DIR=/path/to/agents

# 设置模板目录（默认：config/templates/）
export MAS_TEMPLATE_DIR=/path/to/templates
```

## 配置文件

### Agent配置文件格式

```yaml
name: agent_name
role: Agent角色
description: Agent描述
llm:
  provider: claude  # 或 openai, ollama
  model: claude-sonnet-4-5
  api_key: ${CLAUDE_API_KEY}  # 支持环境变量
  base_url: https://api.anthropic.com
tools:
  inherit_global: true  # 继承全局工具
  whitelist:  # 白名单（只加载这些工具）
    - file_operations
    - code_analysis
  blacklist:  # 黑名单（排除这些工具）
    - dangerous_tool
  role_specific:  # 角色专属工具
    - path: tools/roles/developer
skills:
  inherit_global: true
  whitelist:
    - code_generation
  role_specific:
    - path: skills/roles/developer
plugins:
  enabled:
    - git_plugin
    - docker_plugin
mcp_servers:
  enabled:
    - filesystem
    - github
data_paths:
  workspace: data/agents/{agent_name}/workspace
  memory: data/agents/{agent_name}/memory
  cache: data/agents/{agent_name}/cache
```

## 故障排除

### 问题1：命令找不到

```bash
# 确保mas脚本有执行权限
chmod +x mas

# 或使用python直接运行
python3 cli/main.py --help
```

### 问题2：Agent加载失败

```bash
# 检查Agent是否已注册
./mas agent list

# 查看Agent配置
./mas agent show <agent_name>

# 重新注册Agent
./mas agent register --method template --name <agent_name> --template <template_name>
```

### 问题3：LLM调用失败

```bash
# 检查环境变量
echo $CLAUDE_API_KEY

# 检查Agent的LLM配置
./mas agent show <agent_name>

# 更新LLM配置
./mas agent update <agent_name> --set llm.model=claude-sonnet-4-5
```

### 问题4：工作流卡住

```bash
# 按Ctrl+C中断工作流
# 会话会自动保存

# 查看会话状态
./mas task show --latest

# 查看哪个Agent卡住了
./mas task agents --latest
```

## 演示脚本

我们提供了多个演示脚本帮助你快速上手：

```bash
# Agent管理演示
./demo/agent_cli_demo.sh

# 工作流演示
./demo/workflow_cli_demo.sh

# 完整系统演示
python3 demo/agent_collaboration.py --mode workflow
```

## 更多资源

- **Agent CLI指南**：`docs/agent_cli_guide.md`
- **任务CLI指南**：`docs/task_cli_guide.md`
- **工作流CLI指南**：`docs/workflow_cli_guide.md`
- **API文档**：`docs/api/`
- **架构文档**：`docs/architecture/`

## 反馈和支持

如果你遇到问题或有建议，请：
1. 查看文档：`docs/`
2. 查看示例：`demo/`
3. 提交Issue：GitHub Issues

---

**提示**：所有CLI命令都支持 `--help` 选项查看详细帮助。
