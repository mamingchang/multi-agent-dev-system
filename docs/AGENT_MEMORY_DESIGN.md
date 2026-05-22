# Agent记忆和ID管理设计

## 核心改进

### 1. Agent ID全局唯一

**格式**：`{user_id}_{agent_name}`

**示例**：
- Alice的产品经理Agent：`user_alice_pm`
- Bob的产品经理Agent：`user_bob_pm`

**好处**：
- 全局唯一，避免冲突
- 可以跨项目迁移Agent
- 不同用户的同名Agent互不影响

### 2. Agent记忆在项目下

**旧架构（问题）**：
```
users/user_alice/agents/my_pm/
  └── memory/  # ❌ 记忆在Agent目录，跨项目共享
```

**新架构（改进）**：
```
users/user_alice/projects/todo-app/
  └── agent_memories/
      ├── user_alice_pm/      # Alice的产品经理Agent的记忆
      │   ├── short_term/
      │   ├── long_term/
      │   └── working/
      └── user_alice_dev/     # Alice的开发Agent的记忆
          ├── short_term/
          ├── long_term/
          └── working/
```

**好处**：
- ✅ Agent可以跨项目迁移（记忆不跟随Agent）
- ✅ 不同项目的记忆完全隔离
- ✅ 同一个Agent在不同项目中有独立的记忆
- ✅ 删除项目时，记忆一起删除
- ✅ 备份项目时，记忆一起备份

### 3. Agent可见性简化

**只有两种状态**：
- `private` - 只有创建用户可见和使用
- `public` - 所有用户可见和使用（但不能修改）

**移除**：
- ~~`shared`~~ - 过于复杂，不需要
- ~~`shared_with`~~ - 过于复杂，不需要

## 完整目录结构

```
users/
  └── user_alice/                      # 用户层
      ├── profile.yaml                 # 用户配置
      ├── .current_project             # 当前项目
      ├── agents/                      # Agent定义层
      │   ├── pm/                      # Agent名称（用户空间内唯一）
      │   │   ├── config.yaml          # Agent配置
      │   │   ├── metadata.yaml        # 元数据
      │   │   │   # agent_id: user_alice_pm  （全局唯一）
      │   │   │   # agent_name: pm
      │   │   │   # owner: user_alice
      │   │   │   # visibility: private
      │   │   ├── cache/               # Agent缓存
      │   │   └── workspace/           # Agent临时工作空间
      │   └── dev/
      │       └── ...
      └── projects/                    # 项目层
          ├── todo-app/
          │   ├── project.yaml
          │   ├── sessions/            # 会话（隔离）
          │   ├── workspace/           # 代码（隔离）
          │   ├── artifacts/           # 产物（隔离）
          │   ├── docs/                # 文档
          │   └── agent_memories/      # Agent记忆（隔离）✨
          │       ├── user_alice_pm/   # 使用agent_id命名
          │       │   ├── short_term/
          │       │   ├── long_term/
          │       │   └── working/
          │       └── user_alice_dev/
          │           └── ...
          └── blog-system/
              ├── ...
              └── agent_memories/      # 不同项目，独立记忆
                  ├── user_alice_pm/   # 同一个Agent，不同记忆
                  └── ...
```

## Agent元数据结构

**metadata.yaml**：
```yaml
# 全局唯一ID（格式：{user_id}_{agent_name}）
agent_id: user_alice_pm

# Agent名称（用户空间内唯一）
agent_name: pm

# 所有者
owner: user_alice

# 可见性（private 或 public）
visibility: private

# 创建时间
created_at: "2026-05-20T10:30:00"

# 更新时间
updated_at: "2026-05-20T10:30:00"

# 使用统计
usage_count: 0

# 标签
tags:
  - product_management
  - requirements
```

## Agent迁移性

### 场景1：Agent跨项目使用

```bash
# Alice在todo-app项目中使用pm Agent
./mas project use todo-app
./mas workflow run --title "开发功能A"
# 记忆保存到：projects/todo-app/agent_memories/user_alice_pm/

# Alice在blog-system项目中使用同一个pm Agent
./mas project use blog-system
./mas workflow run --title "开发功能B"
# 记忆保存到：projects/blog-system/agent_memories/user_alice_pm/

# 两个项目的记忆完全独立！
```

### 场景2：Agent配置迁移

```bash
# 导出Agent配置
./mas agent export pm > pm_config.yaml

# 在另一台机器上导入
./mas agent register --method file --name pm --file pm_config.yaml

# Agent配置迁移了，但记忆留在原项目中
```

### 场景3：公开Agent

```bash
# Alice创建一个公开的Agent
./mas agent register --method template --name public_pm --template product_manager --visibility public

# Bob可以看到并使用Alice的公开Agent
./mas user switch bob
./mas agent list --public  # 显示所有公开Agent
./mas agent use user_alice_public_pm  # 使用Alice的Agent

# Bob使用Alice的Agent时，记忆保存在Bob的项目下
# projects/bob_project/agent_memories/user_alice_public_pm/
```

## 唯一性保证

### User ID唯一性

**格式**：`user_{username}`

**检查**：
```python
class UserManager:
    def create_user(self, username):
        user_id = f"user_{username}"
        
        # 检查是否已存在
        if (self.base_dir / user_id).exists():
            raise ValueError(f"用户 {username} 已存在")
        
        # 创建用户目录
        (self.base_dir / user_id).mkdir()
```

### Agent ID唯一性

**格式**：`{user_id}_{agent_name}`

**检查**：
```python
class AgentRegistration:
    def register_from_template(self, agent_name, ...):
        # 检查用户空间内是否已存在
        if (self.config_dir / agent_name).exists():
            raise ValueError(f"Agent {agent_name} 已存在")
        
        # 生成全局唯一ID
        agent_id = f"{self.user_id}_{agent_name}"
        
        # 保存到metadata
        metadata = {
            'agent_id': agent_id,
            'agent_name': agent_name,
            ...
        }
```

### Agent记忆目录唯一性

**格式**：`projects/{project_name}/agent_memories/{agent_id}/`

**自动创建**：
```python
class BaseAgent:
    def _init_memory_system(self):
        if self.project_context:
            project_root = os.path.dirname(self.project_context['workspace_path'])
            memory_dir = os.path.join(
                project_root,
                'agent_memories',
                self.agent_id  # 使用全局唯一的agent_id
            )
        
        self.memory_index = MemoryIndex(memory_dir)
```

## 实现清单

### ✅ 已完成

1. **Agent ID生成**
   - `src/agents/registration.py` - 生成`{user_id}_{agent_name}`格式的agent_id
   - 保存到metadata.yaml

2. **Agent可见性简化**
   - 只保留`private`和`public`两种状态
   - 移除`shared`和`shared_with`

3. **记忆目录调整**
   - `src/agents/base_agent.py` - 记忆保存到项目下
   - 使用agent_id作为目录名

4. **Agent加载**
   - `cli/workflow_commands.py` - 加载metadata，获取agent_id
   - 传递给Agent实例

### 📝 待更新文档

1. **更新架构文档**
   - `docs/ISOLATION_ARCHITECTURE.md` - 更新目录结构
   - `docs/FILE_MANAGEMENT.md` - 更新文件管理说明

2. **更新完成报告**
   - `docs/UPDATE_COMPLETE.md` - 添加记忆管理改进
   - `docs/FINAL_SUMMARY.md` - 更新最终总结

3. **更新演示脚本**
   - `demo/complete_workflow_demo.sh` - 演示记忆隔离

## 测试验证

### 测试1：Agent ID唯一性

```bash
# Alice注册pm Agent
./mas user switch alice
./mas agent register --method template --name pm --template product_manager

# 查看metadata
cat users/user_alice/agents/pm/metadata.yaml
# agent_id: user_alice_pm  ✅

# Bob注册pm Agent
./mas user switch bob
./mas agent register --method template --name pm --template product_manager

# 查看metadata
cat users/user_bob/agents/pm/metadata.yaml
# agent_id: user_bob_pm  ✅

# 两个Agent的ID不同，不会冲突
```

### 测试2：记忆隔离

```bash
# Alice在todo-app中使用pm
./mas user switch alice
./mas project use todo-app
./mas workflow run --title "任务1"

# 检查记忆目录
ls users/user_alice/projects/todo-app/agent_memories/
# user_alice_pm/  ✅

# Alice在blog-system中使用pm
./mas project use blog-system
./mas workflow run --title "任务2"

# 检查记忆目录
ls users/user_alice/projects/blog-system/agent_memories/
# user_alice_pm/  ✅

# 两个项目的记忆目录独立
```

### 测试3：公开Agent

```bash
# Alice创建公开Agent
./mas user switch alice
./mas agent register --method template --name public_pm --template product_manager --visibility public

# Bob使用Alice的公开Agent
./mas user switch bob
./mas agent list --public
# user_alice_public_pm  ✅

# Bob在自己的项目中使用
./mas project use bob_project
./mas workflow run --title "使用Alice的Agent"

# 记忆保存在Bob的项目下
ls users/user_bob/projects/bob_project/agent_memories/
# user_alice_public_pm/  ✅
```

## 优势总结

### 1. Agent可迁移性

- ✅ Agent配置和记忆分离
- ✅ 可以导出/导入Agent配置
- ✅ 记忆留在项目中，不跟随Agent

### 2. 记忆隔离性

- ✅ 不同项目的记忆完全独立
- ✅ 同一个Agent在不同项目中有不同记忆
- ✅ 删除项目时，记忆一起删除

### 3. ID唯一性

- ✅ User ID全局唯一
- ✅ Agent ID全局唯一
- ✅ 记忆目录全局唯一

### 4. 简化设计

- ✅ 可见性只有两种：private和public
- ✅ 移除复杂的shared机制
- ✅ 更容易理解和使用

## 未来扩展

### 1. Agent市场

```bash
# 发布Agent到市场
./mas agent publish pm --description "专业的产品经理Agent"

# 从市场安装Agent
./mas agent install user_alice_pm
```

### 2. 记忆导出/导入

```bash
# 导出项目记忆
./mas project export-memories todo-app > memories.json

# 导入到另一个项目
./mas project import-memories blog-system < memories.json
```

### 3. 记忆分析

```bash
# 分析Agent在项目中的学习情况
./mas agent analyze-memory pm --project todo-app

# 输出：
# - 短期记忆：50条
# - 长期记忆：20条
# - 工作记忆：5条
# - 最常用的知识点：...
```

---

**设计完成时间**：2026-05-20

**设计者**：基于用户需求改进
