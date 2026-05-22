# Sub-Agent工具使用指南

## 概述

Sub-Agent工具允许Agent在处理任务时调用其他Agent作为工具，实现**Agent之间的协作**而不仅仅是**工作流的转交**。

## 两种Agent协作模式

### 1. 工作流转交（Workflow Delegation）

**特点**：
- Agent A完成自己的工作后，将任务转交给Agent B
- Agent A的工作结束，Agent B接手
- 这是主工作流的路由

**实现方式**：
```json
{
    "output": "我的工作成果",
    "next_agent": "agent_b"
}
```

**示例**：
```
Requester → ProductManager → Architect → Developer
```

### 2. Sub-Agent调用（Sub-Agent Call）

**特点**：
- Agent A在处理任务时，调用Agent B完成子任务
- Agent B完成后返回结果给Agent A
- Agent A继续自己的工作，可能再调用其他Agent
- Agent A仍然控制主流程

**实现方式**：
```json
{
    "analysis": "我需要生成代码",
    "sub_agent_call": {
        "agent": "developer",
        "task": "编写数据处理脚本",
        "context": {...}
    },
    "output": "等待子Agent完成...",
    "next_agent": "tester"
}
```

**示例**：
```
DataScientist 处理任务
    ├─ 调用 Developer 生成代码
    ├─ 调用 UIDesigner 创建界面
    └─ 调用 DevOps 部署服务
DataScientist 完成 → 转交给 Tester
```

## 使用场景

### 场景1：数据科学家需要生产级代码

```yaml
# 数据科学家的输出
{
    "analysis": {
        "model": "随机森林分类器",
        "accuracy": "92%",
        "features": ["age", "income", "education"]
    },
    "sub_agent_call": {
        "agent": "developer",
        "task": "将模型封装为REST API服务",
        "context": {
            "model_type": "sklearn.RandomForestClassifier",
            "input_features": ["age", "income", "education"],
            "output": "prediction probability",
            "framework": "FastAPI"
        }
    },
    "output": "模型训练完成，等待代码实现",
    "next_agent": "devops"
}
```

### 场景2：架构师需要安全审查

```yaml
# 架构师的输出
{
    "architecture": {
        "style": "微服务",
        "components": ["API Gateway", "Auth Service", "Data Service"]
    },
    "sub_agent_call": {
        "agent": "security_expert",
        "task": "审查架构的安全性",
        "context": {
            "architecture": {...},
            "focus_areas": ["认证授权", "数据加密", "API安全"]
        }
    },
    "output": "架构设计完成，等待安全审查",
    "next_agent": "developer"
}
```

### 场景3：产品经理需要UI原型

```yaml
# 产品经理的输出
{
    "prd": {
        "features": [...],
        "user_stories": [...]
    },
    "sub_agent_call": {
        "agent": "ui_designer",
        "task": "设计用户登录和注册界面",
        "context": {
            "user_stories": [...],
            "brand_guidelines": {...}
        }
    },
    "output": "PRD完成，等待UI设计",
    "next_agent": "architect"
}
```

## 配置方法

### 1. 在Agent配置中启用sub_agent工具

```yaml
# config/agents/my_agent/config.yaml

tools:
  inherit_global: true
  whitelist:
    - read_file
    - write_file
    - sub_agent  # 启用sub_agent工具
  blacklist: []

# 可选：配置sub_agent行为
sub_agent:
  enabled: true
  max_depth: 2  # 最大嵌套深度
  timeout: 300  # 超时时间（秒）
  allowed_agents:  # 允许调用的Agent（空=全部）
    - developer
    - ui_designer
    - security_expert
```

### 2. 在system_prompt中说明可以使用sub_agent

GenericAgent会自动在system_prompt中添加sub_agent使用说明，包括：
- 可用的Agent列表
- 使用场景
- 输出格式
- 示例

### 3. Agent输出中包含sub_agent_call

```json
{
    "analysis": "你的分析",
    "sub_agent_call": {
        "agent": "agent_name",
        "task": "子任务描述",
        "context": {
            "key": "value"
        }
    },
    "output": "你的输出",
    "next_agent": "next_agent_name"
}
```

## 实现原理

### 1. Agent处理流程

```python
def process(self, task: Task) -> Dict[str, Any]:
    # 1. 使用LLM处理任务
    result = self._process_with_llm(task)
    
    # 2. 检查是否有sub_agent调用请求
    if 'sub_agent_call' in result:
        result = self._handle_sub_agent_call(task, result)
    
    # 3. 保存产物
    task.add_artifact(...)
    
    # 4. 提取next_agent
    next_agent = self.extract_and_validate_next_agent(result)
    
    return result
```

### 2. Sub-Agent调用处理

```python
def _handle_sub_agent_call(self, task, result):
    sub_agent_call = result['sub_agent_call']
    
    # 1. 创建子任务
    sub_task = Task(
        task_id=f"sub_{task.task_id}_{agent_name}",
        title=f"子任务: {sub_task_desc}",
        description=sub_task_desc
    )
    
    # 2. 调用子Agent
    target_agent = self.orchestrator.agents[agent_name]
    sub_result = target_agent.process(sub_task)
    
    # 3. 合并结果
    result['sub_agent_result'] = {
        'success': True,
        'agent': agent_name,
        'result': sub_result,
        'artifacts': sub_task.artifacts
    }
    
    return result
```

### 3. Orchestrator设置

```python
# 在Orchestrator初始化时，为每个Agent设置orchestrator引用
for agent in self.agents.values():
    if hasattr(agent, 'set_orchestrator'):
        agent.set_orchestrator(self)
```

## 高级特性

### 1. 嵌套调用

Sub-Agent可以再调用其他Sub-Agent（受max_depth限制）：

```
Agent A
  └─ 调用 Agent B
       └─ 调用 Agent C
            └─ 调用 Agent D (如果max_depth=3，这里会失败)
```

### 2. 上下文传递

父Agent可以向子Agent传递上下文：

```json
{
    "sub_agent_call": {
        "agent": "developer",
        "task": "实现功能",
        "context": {
            "parent_task_id": "task-123",
            "parent_agent": "data_scientist",
            "requirements": {...},
            "constraints": [...]
        }
    }
}
```

### 3. 结果合并

子Agent的结果会自动合并到父Agent的输出：

```json
{
    "analysis": "父Agent的分析",
    "sub_agent_call": {...},
    "sub_agent_result": {
        "success": true,
        "agent": "developer",
        "result": {
            "files": [...],
            "tests": [...]
        },
        "artifacts": [...]
    },
    "output": "父Agent的输出",
    "next_agent": "tester"
}
```

## 最佳实践

### 1. 明确子任务边界

✅ 好的子任务：
```json
{
    "agent": "developer",
    "task": "编写Python脚本读取CSV文件，计算平均值，输出JSON",
    "context": {
        "input_file": "data.csv",
        "columns": ["age", "income"],
        "output_format": "json"
    }
}
```

❌ 不好的子任务：
```json
{
    "agent": "developer",
    "task": "写代码",
    "context": {}
}
```

### 2. 选择合适的Agent

根据子任务的性质选择专业Agent：
- 代码实现 → `developer`
- UI设计 → `ui_designer`
- 安全审查 → `security_expert`
- 数据分析 → `data_analyst`
- 部署运维 → `devops`

### 3. 传递足够的上下文

子Agent需要足够的信息才能完成任务：
```json
{
    "context": {
        "requirements": "具体需求",
        "constraints": ["约束条件"],
        "dependencies": ["依赖项"],
        "expected_output": "预期输出格式"
    }
}
```

### 4. 处理子Agent失败

检查sub_agent_result的success字段：
```python
if result.get('sub_agent_result', {}).get('success'):
    # 子Agent成功，使用结果
    sub_output = result['sub_agent_result']['result']
else:
    # 子Agent失败，处理错误
    error = result['sub_agent_result']['error']
```

## 限制和注意事项

### 1. 性能影响

- 每次sub_agent调用都会增加执行时间
- 嵌套调用会指数级增加复杂度
- 建议max_depth不超过3

### 2. 循环依赖

避免Agent之间的循环调用：
```
Agent A → 调用 Agent B → 调用 Agent A (死循环！)
```

解决方案：
- 设置max_depth限制
- 在context中记录调用链
- 检测循环并拒绝

### 3. 成本考虑

- 每个sub_agent调用都会消耗LLM tokens
- 复杂任务可能需要多次调用
- 建议监控token使用量

## 示例：完整的数据科学工作流

```python
# 用户任务：构建客户流失预测系统

# 1. DataScientist处理
{
    "analysis": {
        "problem": "客户流失预测",
        "approach": "随机森林分类",
        "features": ["tenure", "monthly_charges", "total_charges"]
    },
    "sub_agent_call": {
        "agent": "developer",
        "task": "实现模型训练和预测API",
        "context": {
            "model": "RandomForestClassifier",
            "features": [...],
            "framework": "FastAPI"
        }
    },
    "output": "模型设计完成，等待代码实现",
    "next_agent": null  # 继续处理
}

# 2. Developer完成代码实现，返回给DataScientist

# 3. DataScientist继续
{
    "analysis": "代码实现完成，需要UI界面",
    "sub_agent_call": {
        "agent": "ui_designer",
        "task": "设计预测结果展示界面",
        "context": {
            "data": "prediction probability, risk level",
            "charts": ["probability gauge", "feature importance"]
        }
    },
    "output": "等待UI设计",
    "next_agent": null
}

# 4. UIDesigner完成设计，返回给DataScientist

# 5. DataScientist完成
{
    "output": "完整的客户流失预测系统",
    "deliverables": {
        "model": "trained model",
        "api": "REST API code",
        "ui": "dashboard design"
    },
    "next_agent": "devops"  # 转交给DevOps部署
}
```

## 总结

Sub-Agent工具实现了Agent之间的**工具级协作**，让Agent可以：
- ✅ 调用其他专业Agent完成子任务
- ✅ 获取子Agent的结果继续工作
- ✅ 保持对主流程的控制
- ✅ 实现复杂的多Agent协作

这与工作流转交（next_agent）是互补的：
- **next_agent**：我完成了，下一个Agent接手
- **sub_agent**：我需要帮助，调用其他Agent，然后我继续

两者结合，实现了灵活强大的多Agent系统。
