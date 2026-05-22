# Claude Code的Skill机制详解

## 核心概念

**Skill** 是Claude Code中的一种特殊工具，用于执行预定义的任务或提供专门的能力。用户通过 `/skill-name` 的方式调用，Claude通过 `Skill` 工具来执行。

## Skill的类型

### 1. Bundled Skills（内置技能）
- **定义位置**: `src/skills/bundled/`
- **注册方式**: 通过 `registerBundledSkill()` 函数
- **特点**: 
  - 编译到CLI二进制文件中
  - 所有用户都可用
  - 不需要外部文件

**示例**: `/remember` skill
```typescript
registerBundledSkill({
  name: 'remember',
  description: 'Review auto-memory entries and propose promotions',
  whenToUse: 'Use when the user wants to review, organize memory',
  userInvocable: true,
  isEnabled: () => isAutoMemoryEnabled(),
  async getPromptForCommand(args) {
    return [{ type: 'text', text: SKILL_PROMPT }]
  },
})
```

### 2. User Skills（用户技能）
- **定义位置**: 
  - 用户级: `~/.claude/skills/`
  - 项目级: `.claude/skills/`
  - 策略级: 管理员配置路径
- **格式**: Markdown文件 + YAML frontmatter
- **特点**: 用户可自定义，支持热加载

**示例**: `.claude/skills/commit.md`
```markdown
---
name: commit
description: Create a git commit with a well-formatted message
whenToUse: When the user asks to commit changes
allowedTools: [Bash, Read]
model: sonnet
---

# Commit Skill

1. Run `git status` to see changes
2. Run `git diff` to review changes
3. Create a commit message following the project's style
4. Run `git commit -m "message"`
```

### 3. Plugin Skills（插件技能）
- **来源**: 通过插件系统加载
- **位置**: 插件目录中的 `skills/` 子目录
- **特点**: 可分享、可版本控制

### 4. MCP Skills（MCP协议技能）
- **来源**: MCP服务器提供的prompts
- **特点**: 动态加载，支持远程服务

## Skill的执行模式

### 1. Inline模式（默认）
```typescript
context: 'inline'  // 或不指定
```

**工作流程**:
1. Skill工具被调用
2. 加载skill的prompt内容
3. 将prompt作为用户消息注入到当前对话
4. Claude在主会话中处理
5. 可以使用skill指定的 `allowedTools`

**特点**:
- 在主会话中执行
- 共享上下文
- 可以访问对话历史

### 2. Fork模式
```typescript
context: 'fork'
```

**工作流程**:
1. Skill工具被调用
2. 创建一个独立的子agent
3. 在子agent中执行skill的prompt
4. 子agent有独立的token预算
5. 执行完成后返回结果到主会话

**特点**:
- 隔离执行环境
- 独立的token预算
- 不污染主会话上下文
- 适合复杂、长时间的任务

**示例**: 某些复杂的分析或生成任务

## Skill的结构

### Frontmatter字段

```yaml
---
# 基本信息
name: skill-name              # 技能名称（必需）
description: Short description # 简短描述（必需）
whenToUse: When to use this   # 使用场景（推荐）

# 执行配置
context: inline               # inline | fork
allowedTools: [Bash, Read]    # 允许使用的工具
model: sonnet                 # 模型覆盖
effort: medium                # 思考努力程度

# 权限和可见性
userInvocable: true           # 用户是否可直接调用
disableModelInvocation: false # 是否禁用模型调用
isHidden: false               # 是否隐藏

# 高级功能
hooks:                        # 钩子配置
  pre-skill: "echo 'Starting'"
  post-skill: "echo 'Done'"
agent: custom-agent           # 指定agent类型
---
```

### Prompt内容

Skill的主体内容是Markdown格式的prompt，可以包含：
- 任务说明
- 步骤指引
- 示例
- 规则和约束

**变量替换**:
- `$ARGUMENTS` - 用户传入的参数
- `${CLAUDE_SKILL_DIR}` - skill目录路径
- `${CLAUDE_SESSION_ID}` - 会话ID

## Skill工具的实现

### SkillTool定义

```typescript
export const SkillTool: Tool = buildTool({
  name: 'Skill',
  inputSchema: z.object({
    skill: z.string().describe('The skill name'),
    args: z.string().optional().describe('Optional arguments'),
  }),
  
  async validateInput({ skill }, context) {
    // 验证skill是否存在
    // 验证skill是否可用
    // 验证skill类型
  },
  
  async checkPermissions({ skill, args }, context) {
    // 检查权限规则
    // 返回 allow/deny/ask
  },
  
  async call({ skill, args }, context, canUseTool, parentMessage, onProgress) {
    // 加载skill内容
    // 根据context决定执行模式
    // 返回结果
  },
})
```

### 执行流程

#### Inline模式执行流程
```
1. 用户: "帮我提交代码"
   ↓
2. Claude: 调用 Skill(skill="commit")
   ↓
3. SkillTool:
   - 验证skill存在
   - 检查权限
   - 加载 commit.md 内容
   - 替换变量
   ↓
4. 注入prompt到对话:
   UserMessage(content="[commit skill的prompt内容]", isMeta=true)
   ↓
5. Claude: 按照prompt执行
   - 调用 Bash("git status")
   - 调用 Bash("git diff")
   - 调用 Bash("git commit -m '...'")
   ↓
6. 返回结果给用户
```

#### Fork模式执行流程
```
1. 用户: "分析这个大型项目"
   ↓
2. Claude: 调用 Skill(skill="analyze", context="fork")
   ↓
3. SkillTool:
   - 创建子agent (agentId: xxx)
   - 准备独立的上下文
   ↓
4. 子agent执行:
   - 独立的token预算
   - 执行analyze skill的prompt
   - 调用各种工具
   - 生成分析报告
   ↓
5. 提取结果:
   result = extractResultText(agentMessages)
   ↓
6. 返回到主会话:
   ToolResult(result="分析报告内容")
   ↓
7. Claude: 基于结果继续对话
```

## Skill的加载机制

### 加载顺序
1. **Bundled skills** - 启动时注册
2. **User skills** - 从 `~/.claude/skills/` 加载
3. **Project skills** - 从 `.claude/skills/` 加载
4. **Plugin skills** - 从插件加载
5. **MCP skills** - 从MCP服务器加载

### 去重机制
- 使用文件的 `realpath` 作为唯一标识
- 同名skill后加载的覆盖先加载的
- 插件skill可以覆盖bundled skill

### 热加载
- 监听文件系统变化
- 自动重新加载修改的skill
- 通知用户skill已更新

## Skill的权限系统

### 权限检查流程
```typescript
async checkPermissions({ skill, args }, context) {
  // 1. 检查deny规则
  if (matchesDenyRule(skill)) {
    return { behavior: 'deny' }
  }
  
  // 2. 检查allow规则
  if (matchesAllowRule(skill)) {
    return { behavior: 'allow' }
  }
  
  // 3. 检查安全属性
  if (skillHasOnlySafeProperties(skill)) {
    return { behavior: 'allow' }
  }
  
  // 4. 默认询问用户
  return {
    behavior: 'ask',
    suggestions: [
      { ruleContent: skill },           // 允许这个skill
      { ruleContent: `${skill}:*` },    // 允许skill的所有参数
    ]
  }
}
```

### 安全属性
只包含以下属性的skill自动允许：
- 基本信息: name, description, whenToUse
- 执行配置: model, effort, allowedTools
- 元数据: source, version, paths

包含其他属性（如hooks, agent）需要用户授权。

## Skill的发现机制

### System Reminder
Claude在每次对话中会收到skill列表：
```xml
<system-reminder>
Available skills:
- commit: Create a git commit
- review-pr: Review a pull request
- pdf: Extract text from PDF files
...
</system-reminder>
```

### 预算控制
- Skill列表占用上下文窗口的1%
- 每个skill描述最多250字符
- Bundled skills保留完整描述
- 其他skill按需截断

### 排序策略
1. Bundled skills优先
2. 最近使用的skill
3. 按名称字母排序

## 与本项目的对比

| 维度 | Claude Code Skill | 本项目 |
|------|-------------------|--------|
| **定位** | 预定义的任务模板 | 独立的专业Agent |
| **执行方式** | Prompt注入 | Agent实例 |
| **状态管理** | 无状态 | 有独立记忆 |
| **生命周期** | 临时（任务结束即销毁） | 持久（可跨会话） |
| **扩展性** | 用户可添加Markdown文件 | 需要编写Python类 |
| **复杂度** | 简单（声明式） | 复杂（编程式） |
| **适用场景** | 重复性任务、模板化工作 | 复杂协作、有状态任务 |

## 借鉴到本项目的建议

### 1. 添加Skill系统作为轻量级任务
```python
# 本项目可以添加类似的Skill机制
class SkillManager:
    def __init__(self):
        self.skills = {}
    
    def register_skill(self, name: str, prompt: str, config: dict):
        """注册一个skill"""
        self.skills[name] = {
            'prompt': prompt,
            'config': config
        }
    
    def execute_skill(self, name: str, args: str, agent: BaseAgent):
        """执行skill - 将prompt注入到agent的对话中"""
        skill = self.skills[name]
        prompt = skill['prompt'].replace('$ARGUMENTS', args)
        return agent.process_message(prompt)
```

### 2. 双层任务系统
```
轻量级任务（Skill）
  ↓ 适合：重复性、模板化、无状态
  - 代码提交
  - 代码审查
  - 文档生成
  
重量级任务（Agent）
  ↓ 适合：复杂、有状态、需要协作
  - 需求分析
  - 架构设计
  - 系统测试
```

### 3. 统一的工具调用
```python
# Agent可以调用Skill
class BaseAgent:
    def use_skill(self, skill_name: str, args: str):
        """使用skill完成子任务"""
        skill_manager = get_skill_manager()
        return skill_manager.execute_skill(skill_name, args, self)
```

## 总结

Claude Code的Skill机制是一个**轻量级、声明式的任务系统**：

**优点**:
1. 简单易用 - Markdown文件即可定义
2. 灵活扩展 - 用户可自由添加
3. 权限控制 - 细粒度的安全机制
4. 热加载 - 修改即生效
5. 多来源 - bundled/user/plugin/MCP

**适用场景**:
- 重复性任务（提交代码、审查PR）
- 模板化工作（生成文档、格式化代码）
- 快速原型（测试新想法）

**与Agent的区别**:
- Skill是**无状态的prompt模板**
- Agent是**有状态的智能实体**
- Skill适合**简单任务**
- Agent适合**复杂协作**

本项目可以借鉴Skill机制，建立**双层任务系统**：
- **Skill层**: 处理简单、重复的任务
- **Agent层**: 处理复杂、需要协作的任务
