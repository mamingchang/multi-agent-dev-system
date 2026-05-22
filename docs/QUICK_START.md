# 快速入门指南

## 前提条件

1. **Python 3.8+**
2. **依赖安装**：
   ```bash
   pip install -r requirements.txt
   ```

3. **LLM API配置**（可选，用于实际运行工作流）：
   ```bash
   # Claude API
   export CLAUDE_API_KEY=your_key
   
   # 或 OpenAI API
   export OPENAI_API_KEY=your_key
   ```

## 5分钟快速体验

### 第1步：创建用户

```bash
# 创建你的用户账号
./mas user init --username alice --email alice@example.com

# 查看当前用户
./mas user whoami
```

**输出**：
```
✓ 用户创建成功: user_alice
✓ 已设置为当前用户
当前用户: alice (user_alice)
```

### 第2步：注册Agent

```bash
# 从模板注册一个产品经理Agent
./mas agent register --method template --name pm --template product_manager

# 注册一个开发Agent（自定义配置）
./mas agent register --method template --name dev --template developer \
  --override tools.whitelist=file_operations,code_analysis \
  --override skills.whitelist=code_generation

# 查看你的Agent列表
./mas agent list
```

**输出**：
```
✓ Agent 'pm' 注册成功 (agent_id=user_alice_pm)
✓ Agent 'dev' 注册成功 (agent_id=user_alice_dev)

当前用户的Agent (2个):
  1. pm (product_manager) - private
  2. dev (developer) - private
```

### 第3步：创建项目

```bash
# 创建一个Todo应用项目
./mas project create --name todo-app --description "Todo应用开发项目"

# 查看项目列表
./mas project list

# 查看项目详情
./mas project show todo-app
```

**输出**：
```
✓ 项目创建成功: todo-app
✓ 已设置为当前项目

项目详情:
  名称: todo-app
  描述: Todo应用开发项目
  工作空间: users/user_alice/projects/todo-app/workspace/
  产物目录: users/user_alice/projects/todo-app/artifacts/
```

### 第4步：运行工作流（需要LLM API）

```bash
# 在项目中运行工作流
./mas workflow run --title "开发用户认证功能" \
  --description "实现用户登录、注册、密码重置功能"

# 或使用当前项目（已经设置为todo-app）
./mas workflow run --title "添加任务管理功能"
```

**注意**：这一步需要配置LLM API才能实际运行。如果没有配置，会提示错误。

### 第5步：查看任务和会话

```bash
# 列出所有会话
./mas task list

# 列出指定项目的会话
./mas task list --project todo-app

# 查看最新会话详情
./mas task show --latest

# 查看Agent状态
./mas task agents --latest
```

## 完整命令参考

### 用户管理

```bash
# 创建用户
./mas user init --username <name> [--email <email>]

# 查看当前用户
./mas user whoami

# 切换用户
./mas user switch <username>

# 列出所有用户
./mas user list
```

### Agent管理

```bash
# 从模板注册
./mas agent register --method template --name <name> --template <template>

# 自定义配置注册
./mas agent register --method template --name <name> --template <template> \
  --override tools.whitelist=tool1,tool2 \
  --override skills.whitelist=skill1,skill2

# 从文件注册
./mas agent register --method file --name <name> --file config.yaml

# 交互式注册
./mas agent register --method interactive

# 查看Agent列表
./mas agent list

# 查看Agent详情
./mas agent show <name>

# 更新Agent配置
./mas agent update <name> --set tools.whitelist=tool1,tool2

# 删除Agent
./mas agent unregister <name>
```

**可用模板**：
- `product_manager` - 产品经理
- `architect` - 架构师
- `developer` - 开发工程师
- `code_reviewer` - 代码审查员
- `tester` - 测试工程师
- `devops` - DevOps工程师
- `requester` - 需求分析师

### 项目管理

```bash
# 创建项目
./mas project create --name <name> [--description <desc>]

# 列出项目
./mas project list

# 查看项目详情
./mas project show <name>

# 设置当前项目
./mas project use <name>

# 查看当前项目
./mas project current

# 查看项目会话
./mas project sessions <name>

# 归档项目
./mas project archive <name>

# 激活项目
./mas project activate <name>

# 删除项目
./mas project delete <name>
```

### 工作流执行

```bash
# 在指定项目中运行
./mas workflow run --project <name> --title <title> [--description <desc>]

# 在当前项目中运行
./mas workflow run --title <title> [--description <desc>]

# 非交互模式
./mas workflow run --title <title> --no-interactive

# 监控工作流
./mas workflow monitor --latest
./mas workflow monitor <session_id>
```

### 任务管理

```bash
# 列出所有会话
./mas task list [--limit N]

# 列出指定项目的会话
./mas task list --project <name>

# 查看会话详情
./mas task show --latest
./mas task show <session_id>
./mas task show --project <name> --latest

# 查看Agent状态
./mas task agents --latest
./mas task agents --project <name> --latest
./mas task agents --latest --agent <agent_name>
```

## 目录结构

运行命令后，会自动创建以下目录结构：

```
users/
  └── user_alice/                    # 你的用户目录
      ├── profile.yaml               # 用户配置
      ├── .current_project           # 当前项目
      ├── agents/                    # 你的Agent
      │   ├── pm/
      │   │   ├── config.yaml        # Agent配置
      │   │   ├── metadata.yaml      # 元数据（包含agent_id）
      │   │   ├── cache/
      │   │   └── workspace/
      │   └── dev/
      │       └── ...
      └── projects/                  # 你的项目
          └── todo-app/
              ├── project.yaml       # 项目配置
              ├── sessions/          # 会话记录
              ├── workspace/         # 代码工作空间
              ├── artifacts/         # 产物
              ├── docs/              # 文档
              └── agent_memories/    # Agent记忆（项目级）
                  ├── user_alice_pm/
                  └── user_alice_dev/
```

## Agent配置示例

### 最小配置

```yaml
name: simple_agent
role: developer
description: 简单的开发Agent
llm:
  provider: claude
  model: claude-sonnet-4-5
```

### 完整配置

```yaml
name: advanced_agent
role: developer
description: 高级开发Agent

llm:
  provider: claude
  model: claude-sonnet-4-5
  temperature: 0.7
  max_tokens: 4096

tools:
  inherit_global: true
  whitelist:
    - file_operations
    - code_analysis
    - git_operations
  blacklist:
    - dangerous_tool

skills:
  inherit_global: false
  whitelist:
    - code_generation
    - test_generation
    - refactoring

plugins:
  enabled:
    - git_plugin
    - docker_plugin

mcp_servers:
  enabled:
    - filesystem
    - github
```

## 常见问题

### Q1: 如何配置LLM API？

**A**: 设置环境变量：

```bash
# Claude
export CLAUDE_API_KEY=your_key

# OpenAI
export OPENAI_API_KEY=your_key

# Ollama（本地）
export OLLAMA_BASE_URL=http://localhost:11434
```

或在Agent配置中设置：

```yaml
llm:
  provider: claude
  api_key: ${CLAUDE_API_KEY}  # 从环境变量读取
```

### Q2: 如何查看Agent可用的工具和技能？

**A**: 查看Agent配置：

```bash
./mas agent show <agent_name>
```

### Q3: 如何让Agent在不同项目中使用？

**A**: Agent是用户级的，可以在任何项目中使用：

```bash
# 在项目A中使用
./mas project use project-a
./mas workflow run --title "任务A"

# 在项目B中使用同一个Agent
./mas project use project-b
./mas workflow run --title "任务B"

# Agent的记忆在两个项目中是独立的
```

### Q4: 如何分享Agent给其他用户？

**A**: 创建公开Agent：

```bash
./mas agent register --method template --name public_pm \
  --template product_manager --visibility public
```

其他用户可以看到并使用：

```bash
./mas agent list --public
```

### Q5: 如何备份项目？

**A**: 直接复制项目目录：

```bash
cp -r users/user_alice/projects/todo-app /backup/
```

项目目录包含所有内容：代码、会话、产物、Agent记忆。

### Q6: 如何删除用户？

**A**: 直接删除用户目录：

```bash
rm -rf users/user_alice/
```

**警告**：这会删除该用户的所有Agent和项目！

### Q7: 没有LLM API可以试用吗？

**A**: 可以试用所有管理命令（用户、Agent、项目、任务），但无法运行实际的工作流。工作流需要LLM API来驱动Agent协作。

你可以：
1. 创建用户和Agent
2. 创建项目
3. 查看目录结构
4. 测试Agent文件操作（见下面的Python示例）

### Q8: 如何测试Agent文件操作？

**A**: 使用Python测试：

```python
from src.agents.base_agent import BaseAgent

class TestAgent(BaseAgent):
    def process(self, task):
        return {'success': True}

# 创建项目上下文
project_context = {
    'project_name': 'test-project',
    'workspace_path': 'users/user_alice/projects/test-project/workspace'
}

# 创建Agent
agent = TestAgent('TestAgent', '测试', project_context=project_context)
agent.agent_id = 'user_alice_test'

# 测试文件操作
result = agent.write_file('test.txt', 'Hello World')
print(result)

result = agent.read_file('test.txt')
print(result)

result = agent.list_files()
print(result)
```

## 下一步

1. **配置LLM API** - 获取Claude或OpenAI的API密钥
2. **运行演示** - 执行 `./demo/complete_workflow_demo.sh`
3. **阅读文档** - 查看 `docs/` 目录下的详细文档
4. **创建真实项目** - 开始使用系统开发实际项目

## 相关文档

- `docs/FINAL_SUMMARY.md` - 系统完整总结
- `docs/ISOLATION_ARCHITECTURE.md` - 三层隔离架构
- `docs/AGENT_MEMORY_DESIGN.md` - Agent记忆和ID管理
- `docs/FILE_MANAGEMENT.md` - 文件管理机制
- `demo/complete_workflow_demo.sh` - 完整工作流演示
- `demo/agent_config_demo.sh` - Agent配置演示

## 获取帮助

```bash
# 查看命令帮助
./mas --help
./mas user --help
./mas agent --help
./mas project --help
./mas workflow --help
./mas task --help
```

---

**开始使用**：`./mas user init --username your_name`

**祝你使用愉快！** 🚀
