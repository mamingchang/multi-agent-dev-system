# Agent协作使用指南

## 快速开始

### 1. 查看已注册的Agent

```bash
# 使用CLI查看
./mas agent list

# 使用演示脚本查看详细信息
python3 demo/agent_collaboration.py --mode info
```

### 2. 测试Agent协作（简单模式）

由于LLM API需要配置，系统会以"简单模式"运行（不调用LLM，使用模拟输出）：

```bash
python3 demo/agent_collaboration.py --mode workflow
```

### 3. 配置LLM API（可选）

如果你想让Agent真正调用LLM，需要配置API密钥：

```bash
# 方式1：环境变量
export ANTHROPIC_API_KEY="your-api-key"

# 方式2：配置文件
# 编辑 config/llm_config.yaml
```

## 当前状态

✅ **已完成**：
- 7个Agent已注册（requester, product_manager, architect, developer, code_reviewer, tester, devops）
- 每个Agent有独立的配置文件
- 每个Agent有独立的数据目录
- Orchestrator已集成注册系统
- Agent可以加载配置和能力

⚠️ **限制**：
- LLM API未配置，Agent运行在"简单模式"（模拟输出）
- 工具/技能目录为空（需要实现具体的工具和技能）
- Agent之间的协作是顺序执行，还没有实现真正的多轮对话

## 工作流程

当前的工作流是线性的：

```
用户需求
   ↓
1. Requester（分析需求）
   ↓
2. ProductManager（产品设计）
   ↓
3. Architect（架构设计）
   ↓
4. Developer（代码实现）
   ↓
5. CodeReviewer（代码审查）
   ↓
6. Tester（测试）
   ↓
7. DevOps（部署）
   ↓
完成
```

## 演示脚本说明

### agent_collaboration.py

```bash
# 查看Agent信息
python3 demo/agent_collaboration.py --mode info

# 执行工作流（简单模式）
python3 demo/agent_collaboration.py --mode workflow
```

**输出示例**：
```
从注册系统加载Agent...
  ✓ Requester (requester) - 已加载
  ✓ ProductManager (product_manager) - 已加载
  ✓ Architect (architect) - 已加载
  ✓ Developer (developer) - 已加载
  ✓ CodeReviewer (code_reviewer) - 已加载
  ✓ Tester (tester) - 已加载
  ✓ DevOps (devops) - 已加载
共加载 7 个Agent

已加载的Agent:

Requester:
  角色: 需求提出者
  配置: 需求分析师，负责需求收集和澄清
  工具数: 0
  技能数: 0
  数据路径: /home/.../data/agents/requester
```

## 自定义Agent

### 创建新Agent

```bash
# 从模板创建
./mas agent register --method template --name my_agent --template developer

# 修改配置
./mas agent update my_agent --set description="我的自定义Agent"

# 查看配置
./mas agent show my_agent
```

### 修改工作流

编辑 `src/orchestrator.py` 中的 `agent_mapping` 来改变工作流中的Agent：

```python
agent_mapping = {
    'requester': ('Requester', RequesterAgent),
    'my_agent': ('MyAgent', MyAgentClass),  # 添加自定义Agent
    # ...
}
```

## 下一步

### 1. 配置LLM API

让Agent能够真正调用LLM进行智能分析：

```bash
# 编辑配置文件
vim config/llm_config.yaml

# 或设置环境变量
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 2. 实现工具和技能

在以下目录创建具体的工具和技能：

```
src/tools/roles/
├── requester/
├── product_manager/
├── architect/
├── developer/
├── code_reviewer/
├── tester/
└── devops/

src/skills/roles/
├── requester/
├── product_manager/
└── ...
```

### 3. 测试真实案例

```bash
# 运行完整工作流
python3 demo/agent_collaboration.py --mode workflow
```

### 4. 查看Agent输出

每个Agent的输出会保存在独立的数据目录：

```bash
# 查看Requester的输出
ls -la data/agents/requester/

# 查看Developer的日志
cat data/agents/developer/logs/*.log
```

## 常见问题

### Q: 为什么显示"简单模式"？

A: 因为没有配置LLM API密钥。Agent会使用模拟输出而不是真正调用LLM。

### Q: 如何让Agent真正协作？

A: 需要：
1. 配置LLM API
2. 实现具体的工具和技能
3. 运行工作流：`python3 demo/agent_collaboration.py --mode workflow`

### Q: 工具数为什么是0？

A: 因为 `src/tools/roles/` 目录下还没有实现具体的工具。需要创建Python文件来实现工具。

### Q: 如何修改Agent的配置？

A: 使用CLI命令：
```bash
./mas agent update developer --set llm.temperature=0.5
```

### Q: 如何查看Agent的完整配置？

A: 使用CLI命令：
```bash
./mas agent show developer
```

或直接查看配置文件：
```bash
cat config/agents/developer.yaml
```

## 总结

当前系统已经具备：
- ✅ Agent注册和管理
- ✅ 配置文件系统
- ✅ 数据隔离
- ✅ Orchestrator集成
- ✅ 基本的工作流

还需要：
- ⏳ LLM API配置
- ⏳ 具体工具和技能实现
- ⏳ 真实案例测试
- ⏳ 多轮对话机制

你现在可以：
1. 查看和管理Agent（`./mas agent list/show/update`）
2. 查看Agent加载情况（`python3 demo/agent_collaboration.py --mode info`）
3. 配置LLM API后运行完整工作流
