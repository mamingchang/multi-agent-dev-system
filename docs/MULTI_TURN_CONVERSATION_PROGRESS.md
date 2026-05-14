# 多轮对话系统实现进度

**开始时间**: 2026-05-08
**当前状态**: 第1阶段完成（基础设施）

---

## ✅ 已完成

### 1. 对话系统（Conversation）
**文件**: `src/conversation.py`

**核心功能**：
- ✅ 消息类型定义（提问、建议、质疑、批准等）
- ✅ 消息记录和存储
- ✅ 对话历史查询
- ✅ 反馈消息过滤
- ✅ 对话上下文生成（用于传递给LLM）
- ✅ 格式化输出（可视化对话）

**关键设计**：
```python
class MessageType(Enum):
    QUESTION = "question"              # 提问
    SUGGESTION = "suggestion"          # 建议
    OBJECTION = "objection"           # 质疑/反对
    REVISION_REQUEST = "revision_request"  # 要求修改
    APPROVAL = "approval"             # 批准通过
```

### 2. Task模型改进
**文件**: `src/workflow/task.py`

**改进内容**：
- ✅ 集成Conversation对话系统
- ✅ 需求锚点（requirement_anchor）- 保存原始需求
- ✅ 迭代计数器（iteration_count）- 记录每个Agent执行次数
- ✅ 产物多版本支持（artifacts改为列表）
- ✅ 首次执行判断（is_first_iteration）

**关键方法**：
```python
task.conversation.add_message(from_agent, to_agent, content, type)
task.get_requirement_anchor()  # 获取原始需求
task.get_iteration_count(agent_name)  # 获取迭代次数
task.is_first_iteration(agent_name)  # 是否首次执行
```

---

## 🚧 待实现

### 第2阶段：修改Agent支持多轮对话

需要修改每个Agent的`process`方法：

#### 2.1 检查是否有反馈
```python
def process(self, task):
    # 检查是否是首次执行
    if task.is_first_iteration(self.name):
        # 首次执行：正常处理
        return self._process_new(task)
    else:
        # 非首次：检查反馈
        feedback = task.conversation.get_feedback_for(self.name)
        if feedback:
            # 根据反馈修改
            return self._process_revision(task, feedback)
```

#### 2.2 添加对话上下文到Prompt
```python
def _build_user_prompt(self, task):
    prompt = f"任务：{task.title}\n"
    
    # 添加对话历史
    conversation_context = task.conversation.get_conversation_context(self.name)
    prompt += f"\n{conversation_context}\n"
    
    # 添加需求锚点
    anchor = task.get_requirement_anchor()
    prompt += f"\n原始需求（不可偏离）：{anchor['description']}\n"
    
    return prompt
```

#### 2.3 发送消息给其他Agent
```python
# 如果发现问题，发送质疑消息
if has_issue:
    task.conversation.add_message(
        from_agent=self.name,
        to_agent='PreviousAgent',
        content={'issue': '具体问题', 'suggestion': '建议'},
        message_type=MessageType.OBJECTION
    )
```

### 第3阶段：修改Orchestrator支持反馈循环

#### 3.1 反馈循环逻辑
```python
def execute_workflow(self, task):
    while not task_completed:
        agent = get_next_agent(task)
        
        # 检查迭代次数
        if task.get_iteration_count(agent.name) > 5:
            # 超过限制，升级到人工
            return self.escalate_to_human(task)
        
        result = agent.process(task)
        
        if result['success']:
            # 成功，进入下一个Agent
            current_step += 1
        else:
            # 失败，检查是否需要回退
            if result.get('action') == 'revise':
                # 回退到指定Agent
                current_step = get_agent_index(result['next_agent'])
```

#### 3.2 收敛机制
```python
# 检查是否陷入无限循环
if total_iterations > 50:
    print("工作流迭代次数过多，可能陷入死循环")
    return self.escalate_to_human(task)

# 检查是否有Agent反复执行
for agent_name, count in task.iteration_count.items():
    if count > 5:
        print(f"{agent_name}执行次数过多，升级到人工")
        return self.escalate_to_human(task)
```

### 第4阶段：强化角色原则

#### 4.1 在Prompt中明确角色立场
```python
system_prompt = """你是{role}，你的职责是{responsibility}。

你必须坚持以下原则：
1. {principle_1}
2. {principle_2}
3. {principle_3}

如果其他Agent的输出违反了这些原则，你应该：
1. 明确指出问题
2. 提出具体的修改建议
3. 不要轻易妥协专业原则

但同时要注意：
- 保持专业和尊重
- 提供建设性的反馈
- 考虑团队协作
"""
```

#### 4.2 各Agent的角色原则

**ProductManager**：
- 坚持用户体验优先
- 功能必须有明确的用户价值
- 不能偏离原始需求

**Architect**：
- 坚持技术可行性
- 架构必须可扩展、可维护
- 不能选择团队不熟悉的技术

**Developer**：
- 坚持代码质量
- 必须有错误处理
- 不能有明显的Bug

**CodeReviewer**：
- 坚持代码规范
- 必须通过质量检查
- 不能妥协安全问题

### 第5阶段：实现HumanAgent

```python
class HumanAgent(BaseAgent):
    def process(self, task):
        # 展示当前状态
        print("需要人工介入：")
        print(f"原因：{task.escalation_reason}")
        
        # 展示对话历史
        print("\n对话历史：")
        for msg in task.conversation.messages[-10:]:
            print(f"  {msg}")
        
        # 等待人工决策
        decision = input("请输入决策（continue/abort/modify）：")
        
        if decision == 'continue':
            # 继续工作流
            return {'success': True, 'next_agent': task.current_agent}
        elif decision == 'abort':
            # 终止任务
            return {'success': False, 'message': '任务已终止'}
        elif decision == 'modify':
            # 修改需求或配置
            # ...
```

---

## 📊 实现优先级

1. **高优先级**（核心功能）：
   - ✅ 对话系统基础设施
   - ✅ Task模型改进
   - ⏳ 修改Agent支持多轮对话
   - ⏳ 修改Orchestrator支持反馈循环

2. **中优先级**（增强功能）：
   - ⏳ 强化角色原则
   - ⏳ 收敛机制优化

3. **低优先级**（辅助功能）：
   - ⏳ HumanAgent实现
   - ⏳ 对话可视化优化

---

## 🎯 下一步行动

**立即开始**：修改一个Agent（如Developer）支持多轮对话

**步骤**：
1. 修改Developer的process方法
2. 添加反馈检查逻辑
3. 添加对话上下文到Prompt
4. 测试多轮修改场景

**预期效果**：
```
CodeReviewer: "代码没有错误处理"
Developer: "收到反馈，正在添加错误处理..."
Developer: "已添加错误处理，请重新审查"
CodeReviewer: "通过审查"
```

---

## 💡 关键设计思想

### 1. 需求锚点（Requirement Anchor）
- 原始需求在任务创建时保存
- 整个过程中不可修改
- 所有讨论都要参考需求锚点
- 防止需求蔓延

### 2. 迭代计数器（Iteration Counter）
- 记录每个Agent执行次数
- 防止无限循环
- 超过阈值升级到人工

### 3. 对话上下文（Conversation Context）
- Agent能看到相关的对话历史
- 传递给LLM作为上下文
- 让Agent理解当前状态

### 4. 角色原则（Role Principles）
- 每个Agent有自己的"底线"
- 在Prompt中明确原则
- 不能轻易妥协

### 5. 收敛机制（Convergence Mechanism）
- 迭代次数限制
- 人工介入升级
- 强制收敛

---

## 📝 示例场景

### 场景1：代码质量争议
```
Developer: 生成代码（无错误处理）
CodeReviewer: 质疑 - "缺少错误处理"
Developer: 修改代码（添加错误处理）
CodeReviewer: 批准 - "通过审查"
Tester: 开始测试
```

### 场景2：架构争议
```
Architect: 设计微服务架构
Developer: 质疑 - "团队没有微服务经验"
Architect: 建议 - "可以先用单体，预留扩展接口"
Developer: 批准 - "这个方案可行"
Architect: 修改架构设计
Developer: 开始开发
```

### 场景3：需求偏离
```
ProductManager: 添加社交分享功能
Requester: 质疑 - "原始需求没有社交功能"
ProductManager: 澄清 - "这是增强用户体验"
Requester: 反对 - "偏离了需求锚点"
ProductManager: 修改PRD（去掉社交功能）
Architect: 开始架构设计
```

---

## ✨ 预期效果

实现后，系统将具备：
- ✅ 真正的多轮对话和协作
- ✅ Agent之间的讨论和质疑
- ✅ 迭代修改和优化
- ✅ 需求锚点保证不偏离
- ✅ 收敛机制保证最终完成
- ✅ 角色原则保证专业性

这将是一个**真实模拟人类团队协作**的AI系统！
