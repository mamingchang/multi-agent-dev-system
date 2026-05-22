# Bug修复：Agent感知和项目Agent配置

## 问题描述

用户试用系统时发现两个关键问题：

### 问题1：Agent调用不存在的Agent
- **现象**：Agent在输出中指定的`next_agent`可能不在项目配置的Agent列表中
- **影响**：工作流失败，提示"Agent不存在"
- **根本原因**：Agent在process()时不知道项目中有哪些可用的Agent

### 问题2：项目Agent配置不可修改
- **现象**：项目创建后，无法批量更新Agent配置
- **影响**：只能通过add-agent/remove-agent逐个修改，不方便
- **根本原因**：缺少批量更新命令

## 解决方案

### 修复1：增强Agent感知系统

**修改文件**：`src/agents/base_agent.py`

**修改内容**：在`_build_user_prompt()`方法中添加可用Agent列表提示

```python
# 2. 可用Agent列表（重要！）
available_agents = self.get_available_agents()
if available_agents:
    prompt_parts.append(f"\n# ⚠️ 项目可用Agent列表\n")
    prompt_parts.append(f"当前项目配置的Agent: {', '.join(available_agents)}\n")
    prompt_parts.append(f"\n**重要**: 你只能指定上述Agent作为next_agent，不能指定其他Agent！\n")
    prompt_parts.append(f"如果指定了不存在的Agent，工作流会失败。\n")
```

**效果**：
- Agent在处理任务时会明确看到可用的Agent列表
- LLM会被明确告知只能选择列表中的Agent
- 减少了指定不存在Agent的错误

### 修复2：添加批量更新命令

**修改文件**：`cli/project_commands.py`

**新增命令**：`project update-agents`

```bash
# 批量更新项目的Agent配置
./cli/main.py project update-agents my-app \
  --agents requester,developer,tester,devops
```

**功能**：
- 一次性替换项目的所有Agent配置
- 支持逗号分隔的Agent列表
- 自动保存到项目配置

## 使用示例

### 场景1：创建项目时指定Agent

```bash
# 创建项目，只使用必要的Agent
./cli/main.py project create --name quick-prototype \
  --agents requester,developer,tester
```

### 场景2：添加单个Agent

```bash
# 添加架构师Agent
./cli/main.py project add-agent quick-prototype --agent architect
```

### 场景3：批量更新Agent配置

```bash
# 更新为完整的Agent列表
./cli/main.py project update-agents quick-prototype \
  --agents requester,product_manager,architect,developer,code_reviewer,tester,devops
```

### 场景4：查看项目Agent

```bash
# 查看当前配置
./cli/main.py project list-agents quick-prototype
```

## 技术细节

### Agent感知机制

1. **项目上下文传递**
   - DynamicOrchestrator在execute()时设置`available_agents`
   - 通过`agent.project_context['available_agents']`传递

2. **Agent查询方法**
   ```python
   # Agent可以查询可用Agent
   available = self.get_available_agents()
   
   # Agent可以检查是否可以委托
   if self.can_delegate_to('Developer'):
       return self.delegate_to('Developer')
   ```

3. **Prompt增强**
   - 在用户提示词中明确列出可用Agent
   - 强调只能选择列表中的Agent
   - 警告选择不存在Agent的后果

### 验证机制

DynamicOrchestrator在执行时会验证：

```python
# 验证next_agent是否存在
if next_agent not in self.agents:
    print(f"\n⚠️  指定的Agent不存在: {next_agent}")
    print(f"   可用Agent: {', '.join(self.agents.keys())}")
    
    return self._escalate_to_human(
        task, current_agent_name,
        f"指定的Agent不存在: {next_agent}"
    )
```

## 测试建议

### 测试1：验证Agent感知

```bash
# 1. 创建项目，只配置3个Agent
./cli/main.py project create --name test-awareness \
  --agents requester,developer,tester

# 2. 运行工作流
./cli/main.py workflow dynamic --project test-awareness

# 3. 观察Agent是否只选择这3个Agent
```

### 测试2：验证配置更新

```bash
# 1. 查看当前配置
./cli/main.py project list-agents test-awareness

# 2. 更新配置
./cli/main.py project update-agents test-awareness \
  --agents requester,architect,developer,tester

# 3. 验证更新
./cli/main.py project list-agents test-awareness
```

## 预期效果

### 修复前
- ❌ Agent可能指定不存在的Agent
- ❌ 工作流频繁失败
- ❌ 需要逐个添加/移除Agent

### 修复后
- ✅ Agent明确知道可用的Agent列表
- ✅ LLM被明确告知约束条件
- ✅ 支持批量更新Agent配置
- ✅ 工作流更稳定可靠

## 相关文件

- `src/agents/base_agent.py` - Agent基类（增强prompt）
- `src/dynamic_orchestrator.py` - 动态路由编排器（验证逻辑）
- `cli/project_commands.py` - 项目管理命令（新增update-agents）
- `docs/USAGE_GUIDE.md` - 使用指南

## 后续优化建议

1. **智能推荐**：根据任务类型推荐合适的Agent组合
2. **Agent模板**：预定义常用的Agent组合（如"快速原型"、"完整流程"）
3. **依赖检查**：检查Agent之间的依赖关系（如Developer需要Architect的输出）
4. **动态加载**：支持运行时动态添加/移除Agent

## 总结

这次修复解决了两个核心问题：

1. **Agent感知不足** → 在prompt中明确列出可用Agent
2. **配置不灵活** → 添加批量更新命令

这些改进让系统更加健壮和易用，减少了用户的困惑和错误。
