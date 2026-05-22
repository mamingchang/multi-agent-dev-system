# 完整使用指南 - 项目级Agent配置和动态路由

## 功能1: 项目级Agent配置

### 创建项目时指定Agent

```bash
# 创建项目并指定使用哪些Agent
./cli/main.py project create \
  --name my-app \
  --description "我的应用" \
  --agents requester,developer,tester

# 输出:
# ✓ 项目创建成功: my-app
#   配置的Agent: requester, developer, tester
```

### 添加Agent到现有项目

```bash
# 添加自己的Agent
./cli/main.py project add-agent my-app --agent architect

# 添加其他用户的公开Agent
./cli/main.py project add-agent my-app \
  --agent devops \
  --from-user user_bob

# 输出:
# ✓ 已添加Agent: devops (来自用户 user_bob)
```

### 查看项目的Agent

```bash
./cli/main.py project list-agents my-app

# 输出:
# 项目: my-app
# 配置的Agent (5个):
#
#   • requester
#   • developer
#   • tester
#   • architect
#   • devops (来自 user_bob)
```

### 移除Agent

```bash
./cli/main.py project remove-agent my-app --agent architect

# 输出:
# ✓ 已移除Agent: architect
```

## 功能2: 动态路由工作流

### 基本使用

```bash
./cli/main.py workflow dynamic --project my-app

# 系统会提示输入:
任务标题: 实现用户登录
需求描述: 支持邮箱密码登录
```

### 指定起始Agent

```bash
./cli/main.py workflow dynamic \
  --project my-app \
  --start-agent Developer
```

### 执行过程示例

```
==================================================
🎯 动态路由工作流 - Agent自主决定
==================================================

当前用户: user_alice
当前项目: my-app

任务ID: abc-123-def
会话ID: session-456

✓ 已加载 5 个Agent
  可用Agent: Requester, Developer, Tester, Architect, DevOps

==================================================
🚀 动态路由工作流
==================================================
任务: 实现用户登录
可用Agent: Requester, Developer, Tester, Architect, DevOps
==================================================

==================================================
🔄 轮次 1: Requester (需求分析师)
   Agent迭代: 1/10
==================================================

⏱️  耗时: 3.45秒

✅ Requester 处理成功
📄 输出: 需求分析完成，明确了登录功能的核心需求...

→ 下一个Agent: Developer

==================================================
🔄 轮次 2: Developer (开发工程师)
   Agent迭代: 1/10
==================================================

⏱️  耗时: 5.23秒

✅ Developer 处理成功
📄 输出: 代码实现完成，包含登录API和会话管理...

→ 下一个Agent: Tester

==================================================
🔄 轮次 3: Tester (测试工程师)
   Agent迭代: 1/10
==================================================

⏱️  耗时: 4.12秒

✅ Tester 处理成功
📄 输出: 测试完成，所有测试用例通过...

🎉 Tester 标记任务完成

==================================================
✅ 工作流执行成功
==================================================

消息: 任务完成
总迭代次数: 3

执行路径 (3步):
  1. Requester (第1次)
  2. Developer (第1次)
  3. Tester (第1次)

会话已保存: session-456
```

## Agent如何指定下一个处理者

### 方法1: 使用delegate_to()

```python
class MyAgent(BaseAgent):
    def process(self, task):
        # ... 处理逻辑 ...
        
        # 委托给Developer
        return self.delegate_to('Developer', '需要实现代码')
```

### 方法2: 直接返回next_agent

```python
class MyAgent(BaseAgent):
    def process(self, task):
        # ... 处理逻辑 ...
        
        return {
            'success': True,
            'output': '...',
            'next_agent': 'Tester'  # 指定下一个
        }
```

### 方法3: 标记任务完成

```python
class MyAgent(BaseAgent):
    def process(self, task):
        # ... 处理逻辑 ...
        
        # 任务完成，不需要其他Agent
        return self.mark_task_completed()
```

### 方法4: 智能建议

```python
class MyAgent(BaseAgent):
    def suggest_next_agent(self, task_context):
        """根据任务状态建议下一个Agent"""
        if task_context.get('needs_review'):
            return 'CodeReviewer'
        elif task_context.get('needs_test'):
            return 'Tester'
        else:
            return 'DevOps'
    
    def process(self, task):
        # ... 处理逻辑 ...
        
        next_agent = self.suggest_next_agent(task_context)
        
        return {
            'success': True,
            'output': '...',
            'next_agent': next_agent
        }
```

## Agent感知系统

### 查询可用Agent

```python
class MyAgent(BaseAgent):
    def process(self, task):
        # 获取可用Agent列表
        available = self.get_available_agents()
        print(f"可用Agent: {available}")
        
        # 检查是否可以委托
        if self.can_delegate_to('Developer'):
            return self.delegate_to('Developer')
```

### 项目上下文

```python
class MyAgent(BaseAgent):
    def process(self, task):
        # 访问项目上下文
        workspace = self.project_context['workspace_path']
        available_agents = self.project_context['available_agents']
        
        print(f"工作空间: {workspace}")
        print(f"可用Agent: {available_agents}")
```

## 完整工作流示例

### 场景：快速原型开发

```bash
# 1. 创建项目，只使用必要的Agent
./cli/main.py project create \
  --name quick-prototype \
  --agents requester,developer,tester

# 2. 运行动态路由工作流
./cli/main.py workflow dynamic --project quick-prototype

# 输入:
任务标题: 实现简单的API
需求描述: 只需要一个GET /hello接口

# 执行路径:
# Requester → Developer → Tester → 完成
# (跳过了ProductManager, Architect, CodeReviewer, DevOps)
```

### 场景：使用他人的专业Agent

```bash
# 1. 创建项目
./cli/main.py project create --name my-app

# 2. 添加自己的Agent
./cli/main.py project add-agent my-app --agent requester
./cli/main.py project add-agent my-app --agent developer

# 3. 使用Bob的专业DevOps Agent
./cli/main.py project add-agent my-app \
  --agent devops \
  --from-user user_bob

# 4. 查看配置
./cli/main.py project list-agents my-app

# 输出:
# 项目: my-app
# 配置的Agent (3个):
#   • requester
#   • developer
#   • devops (来自 user_bob)

# 5. 运行工作流
./cli/main.py workflow dynamic --project my-app
```

## 工作流模式对比

### 1. 动态路由 (新) ⭐⭐⭐

```bash
./cli/main.py workflow dynamic --project my-app
```

**特点**:
- Agent自主决定下一步
- 灵活的工作流
- 可以跳过不需要的Agent
- 适合各种场景

**适用场景**:
- 快速原型开发
- 非标准流程
- 需要灵活路由

### 2. 协作讨论

```bash
./cli/main.py workflow watch --project my-app
```

**特点**:
- 固定顺序，但可以讨论
- Agent之间反馈循环
- 适合标准流程

**适用场景**:
- 标准软件开发流程
- 需要多轮讨论
- 质量要求高

### 3. 手动控制

```bash
./cli/main.py workflow run --project my-app --interactive
```

**特点**:
- 用户控制每一步
- 适合学习和调试

**适用场景**:
- 学习系统
- 调试问题
- 需要严格控制

## 最佳实践

### 1. 项目Agent配置

✅ **推荐**:
- 只配置真正需要的Agent
- 使用专业的公开Agent
- 定期审查Agent列表

❌ **不推荐**:
- 配置所有Agent（即使不需要）
- 重复配置相同角色的Agent

### 2. Agent路由

✅ **推荐**:
- 明确指定next_agent
- 及时标记任务完成
- 提供清晰的委托原因

❌ **不推荐**:
- 不指定next_agent（依赖自动推断）
- 无限循环（A→B→A→B...）
- 模糊的路由逻辑

### 3. 人工介入

✅ **推荐**:
- 使用watch模式观察
- 只在必要时介入
- 提供明确的指导

❌ **不推荐**:
- 过度介入
- 频繁打断工作流
- 模糊的指令

## 故障排除

### 问题1: Agent无限循环

**症状**: Agent A → B → A → B ...

**解决**:
1. 检查Agent的next_agent逻辑
2. 添加循环检测
3. 设置合理的迭代限制

### 问题2: 找不到Agent

**症状**: "Agent不存在: XXX"

**解决**:
1. 检查项目配置: `project list-agents`
2. 确认Agent名称正确
3. 添加缺失的Agent: `project add-agent`

### 问题3: 任务永不结束

**症状**: 达到迭代限制

**解决**:
1. 确保某个Agent调用`mark_task_completed()`
2. 检查任务是否过于复杂
3. 分解为多个小任务

## 总结

现在你可以：

✅ 创建项目时指定Agent  
✅ 添加/移除项目的Agent  
✅ 使用其他用户的公开Agent  
✅ Agent自主决定工作流路由  
✅ Agent感知其他可用Agent  
✅ Agent标记任务完成  
✅ 人工观察和介入  

**所有核心功能都已实现！**
