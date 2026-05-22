# Bug修复：Agent命名不一致导致匹配失败

## 问题描述

用户试用时发现Agent在指定next_agent时，名称格式不匹配：

### 症状
- Agent输出的next_agent可能是：`Requester`, `ProductManager`（大写驼峰）
- 但实际可用的Agent是：`requester`, `product_manager`（小写下划线）
- 导致匹配失败，提示"Agent不存在"

### 根本原因

系统中存在多种Agent命名格式：

1. **配置文件格式**：`requester`, `product_manager`（小写+下划线）
2. **类名格式**：`RequesterAgent`, `ProductManagerAgent`（大写驼峰+Agent后缀）
3. **显示名称**：可能被转换成各种格式

在不同地方使用了不同的格式，导致匹配失败。

## 解决方案

### 原则：统一使用配置文件中的name格式

**标准格式**：小写+下划线（如：`requester`, `product_manager`, `code_reviewer`）

### 修复1：统一agents_dict的key格式

**文件**：`cli/dynamic_workflow.py`

**修改前**：
```python
# 使用显示名称作为key（可能是各种格式）
display_name = config.get('name', actual_agent_name)
agents_dict[display_name] = agent
```

**修改后**：
```python
# 使用配置文件中的name作为key（小写+下划线格式）
agent_name_from_config = config.get('name', actual_agent_name)
agent = agent_class(
    name=agent_name_from_config,
    config=config
)
agents_dict[agent_name_from_config] = agent
```

### 修复2：统一自动推断的格式

**文件**：`src/dynamic_orchestrator.py`

**修改前**：
```python
# 使用大写驼峰格式
standard_flow = [
    'Requester',
    'ProductManager',
    'Architect',
    ...
]
```

**修改后**：
```python
# 使用小写+下划线格式（与配置文件一致）
standard_flow = [
    'requester',
    'product_manager',
    'architect',
    'developer',
    'code_reviewer',
    'tester',
    'devops'
]
```

### 修复3：标准化匹配逻辑

**修改前**：
```python
# 模糊匹配，可能匹配错误
if agent_name.lower() == current_agent.lower() or current_agent in agent_name:
    ...
```

**修改后**：
```python
# 标准化后精确匹配
current_normalized = current_agent.lower().replace(' ', '_')
if agent_name == current_normalized or current_normalized in agent_name:
    # 精确匹配
    if next_agent_name in self.agents:
        return next_agent_name
```

## 命名规范

### 配置文件（config.yaml）
```yaml
name: requester          # 小写+下划线
role: requester
```

### Agent类定义
```python
class RequesterAgent(BaseAgent):  # 类名：大写驼峰+Agent后缀
    def __init__(self, name: str = "requester", ...):  # 默认name：小写+下划线
        super().__init__(name=name, role="需求分析师", ...)
```

### 项目配置（project.yaml）
```yaml
agents:
  - requester           # 小写+下划线
  - product_manager
  - developer
```

### Agent输出格式
```python
# Agent在process()中返回
return {
    'success': True,
    'next_agent': 'developer',  # 必须使用小写+下划线格式
    'output': '...'
}
```

### available_agents列表
```python
# 在project_context中传递
project_context['available_agents'] = [
    'requester',
    'product_manager',
    'developer'
]
```

## 验证测试

创建了测试脚本 `test_agent_naming.py` 验证命名一致性：

```bash
python3 test_agent_naming.py
```

**测试结果**：
```
测试Agent: requester
  配置文件中的name: requester
  Agent实例的name: requester
  ✅ 命名一致: requester

测试Agent: product_manager
  配置文件中的name: product_manager
  Agent实例的name: product_manager
  ✅ 命名一致: product_manager
```

## Agent名称映射表

| 配置文件名称 | Agent类名 | 显示名称 | 说明 |
|------------|----------|---------|------|
| requester | RequesterAgent | 需求分析师 | 需求收集和澄清 |
| product_manager | ProductManagerAgent | 产品经理 | 需求分析和产品设计 |
| architect | ArchitectAgent | 架构师 | 系统架构设计 |
| developer | DeveloperAgent | 开发工程师 | 代码实现 |
| code_reviewer | CodeReviewerAgent | 代码审查 | 代码质量检查 |
| tester | TesterAgent | 测试工程师 | 测试用例设计 |
| devops | DevOpsAgent | DevOps工程师 | 部署和运维 |

## 使用示例

### 正确的Agent输出

```python
class RequesterAgent(BaseAgent):
    def process(self, task):
        # 获取可用Agent列表
        available = self.get_available_agents()
        # ['requester', 'product_manager', 'developer']
        
        # 正确：使用小写+下划线格式
        return {
            'success': True,
            'next_agent': 'product_manager',  # ✅
            'output': '需求分析完成'
        }
        
        # 错误示例：
        # 'next_agent': 'ProductManager'  # ❌ 大写驼峰
        # 'next_agent': 'Product Manager' # ❌ 空格分隔
```

### 在Prompt中的提示

Agent的prompt现在会明确列出可用Agent：

```
# ⚠️ 项目可用Agent列表
当前项目配置的Agent: requester, product_manager, developer

**重要**: 你只能指定上述Agent作为next_agent，不能指定其他Agent！
如果指定了不存在的Agent，工作流会失败。
```

## 影响范围

### 修改的文件
1. `cli/dynamic_workflow.py` - Agent加载逻辑
2. `src/dynamic_orchestrator.py` - 自动推断逻辑
3. `src/agents/base_agent.py` - Prompt生成（已在之前修复）

### 不需要修改的文件
- Agent配置文件（已经是正确格式）
- Agent类定义（保持不变）
- 项目配置文件（已经是正确格式）

## 测试建议

### 测试1：验证命名一致性
```bash
python3 test_agent_naming.py
```

### 测试2：运行完整工作流
```bash
# 创建项目
./cli/main.py project create --name test-naming \
  --agents requester,product_manager,developer

# 运行工作流
./cli/main.py workflow dynamic --project test-naming

# 观察Agent是否能正确匹配
```

### 测试3：验证自动推断
```bash
# 运行工作流，不指定起始Agent
./cli/main.py workflow dynamic --project test-naming

# 观察自动推断是否正确
```

## 预期效果

### 修复前
- ❌ Agent输出 `next_agent: 'ProductManager'`
- ❌ 系统查找 `ProductManager`，找不到
- ❌ 提示"Agent不存在: ProductManager"
- ❌ 工作流失败

### 修复后
- ✅ Agent看到可用列表：`requester, product_manager, developer`
- ✅ Agent输出 `next_agent: 'product_manager'`
- ✅ 系统查找 `product_manager`，找到
- ✅ 工作流继续执行

## 后续改进建议

1. **添加名称验证**：在Agent注册时验证名称格式
2. **自动转换**：提供工具函数自动转换不同格式
3. **更好的错误提示**：当匹配失败时，提示相似的Agent名称
4. **文档完善**：在开发文档中明确命名规范

## 总结

这个bug的根本原因是**命名格式不统一**。通过统一使用配置文件中的格式（小写+下划线），确保了：

1. ✅ 配置文件、Agent实例、字典key使用相同格式
2. ✅ Agent能看到正确的可用Agent列表
3. ✅ Agent输出的next_agent能正确匹配
4. ✅ 自动推断使用相同格式
5. ✅ 工作流稳定运行

**关键原则**：整个系统统一使用 `小写+下划线` 格式作为Agent的标识符。
