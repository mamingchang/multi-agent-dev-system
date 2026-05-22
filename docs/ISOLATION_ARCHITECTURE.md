# 三层隔离架构设计

## 架构概述

```
用户层 (User)
  ├── Agent层 (Agent) - 用户注册的Agent，可选公开
  └── 项目层 (Project) - 用户创建的项目，完全隔离
```

## 三层隔离

### 1. 用户层 (User Level)

每个用户有独立的命名空间：

```
users/
  ├── user_alice/
  │   ├── agents/          # Alice注册的Agent
  │   ├── projects/        # Alice的项目
  │   └── profile.yaml     # 用户配置
  └── user_bob/
      ├── agents/
      ├── projects/
      └── profile.yaml
```

**用户配置** (`profile.yaml`):
```yaml
user_id: user_alice
username: alice
email: alice@example.com
created_at: 2026-05-21T10:00:00
settings:
  default_llm: claude-sonnet-4-5
  workspace_path: users/user_alice/workspace
```

### 2. Agent层 (Agent Level)

Agent属于用户，可以选择公开：

```
users/user_alice/agents/
  ├── my_custom_pm/
  │   ├── config.yaml      # Agent配置
  │   ├── memory/          # Agent记忆
  │   ├── cache/           # Agent缓存
  │   └── metadata.yaml    # 元数据（是否公开、使用统计等）
  └── my_developer/
      ├── config.yaml
      └── ...

# 公开Agent索引
shared_agents/
  ├── index.yaml           # 所有公开Agent的索引
  └── user_alice/
      └── my_custom_pm -> ../../users/user_alice/agents/my_custom_pm  # 软链接
```

**Agent元数据** (`metadata.yaml`):
```yaml
agent_id: my_custom_pm
owner: user_alice
visibility: public  # public / private
created_at: 2026-05-21T10:00:00
usage_count: 42
shared_with:  # 如果是private，可以指定分享给谁
  - user_bob
  - user_charlie
tags:
  - product-management
  - agile
description: 我的自定义产品经理Agent
```

### 3. 项目层 (Project Level)

项目完全隔离，每个项目有独立的工作空间：

```
users/user_alice/projects/
  ├── todo-app/
  │   ├── project.yaml         # 项目配置
  │   ├── sessions/            # 该项目的所有会话
  │   │   ├── session-001.json
  │   │   └── session-002.json
  │   ├── workspace/           # 生成的代码
  │   │   ├── src/
  │   │   ├── tests/
  │   │   └── README.md
  │   ├── artifacts/           # 所有产物
  │   │   ├── requirements/
  │   │   ├── designs/
  │   │   ├── code/
  │   │   └── tests/
  │   ├── docs/                # 生成的文档
  │   └── .git/                # Git仓库（可选）
  └── blog-system/
      ├── project.yaml
      ├── sessions/
      └── workspace/
```

**项目配置** (`project.yaml`):
```yaml
project_id: todo-app
project_name: Todo应用
owner: user_alice
created_at: 2026-05-21T10:00:00
description: 一个简单的Todo待办事项管理应用

# 项目使用的Agent（可以是自己的或公开的）
agents:
  - user_alice/my_custom_pm      # 自己的私有Agent
  - user_alice/my_developer      # 自己的私有Agent
  - shared/standard_tester       # 公开Agent

# 项目设置
settings:
  workspace_path: users/user_alice/projects/todo-app/workspace
  git_enabled: true
  auto_commit: true

# 项目状态
status: active  # active / archived / completed
tags:
  - web-app
  - python
  - flask
```

## 目录结构完整示例

```
multi-agent-dev-system/
├── users/
│   ├── user_alice/
│   │   ├── profile.yaml
│   │   ├── agents/
│   │   │   ├── my_custom_pm/
│   │   │   │   ├── config.yaml
│   │   │   │   ├── metadata.yaml
│   │   │   │   ├── memory/
│   │   │   │   └── cache/
│   │   │   └── my_developer/
│   │   │       └── ...
│   │   └── projects/
│   │       ├── todo-app/
│   │       │   ├── project.yaml
│   │       │   ├── sessions/
│   │       │   ├── workspace/
│   │       │   ├── artifacts/
│   │       │   └── docs/
│   │       └── blog-system/
│   │           └── ...
│   └── user_bob/
│       ├── profile.yaml
│       ├── agents/
│       └── projects/
│
├── shared_agents/
│   ├── index.yaml
│   └── user_alice/
│       └── my_custom_pm -> ../../users/user_alice/agents/my_custom_pm
│
├── templates/
│   ├── agents/              # Agent模板
│   └── projects/            # 项目模板
│
└── config/
    └── system.yaml          # 系统配置
```

## 权限控制

### Agent权限

```yaml
# Agent可见性级别
visibility:
  - private: 只有owner可以使用
  - shared: 指定用户可以使用
  - public: 所有用户可以使用

# 示例
metadata.yaml:
  visibility: shared
  shared_with:
    - user_bob
    - user_charlie
```

### 项目权限

```yaml
# 项目协作
project.yaml:
  owner: user_alice
  collaborators:
    - user: user_bob
      role: developer
      permissions:
        - read
        - write
    - user: user_charlie
      role: viewer
      permissions:
        - read
```

## CLI命令设计

### 用户管理

```bash
# 创建用户（首次使用）
./mas user init --username alice --email alice@example.com

# 切换用户
./mas user switch alice

# 查看当前用户
./mas user whoami
```

### Agent管理（用户级别）

```bash
# 注册Agent（自动属于当前用户）
./mas agent register --name my_pm --template product_manager

# 列出我的Agent
./mas agent list

# 列出公开Agent
./mas agent list --public

# 公开我的Agent
./mas agent share my_pm --visibility public

# 分享给特定用户
./mas agent share my_pm --to bob,charlie

# 使用别人的公开Agent
./mas agent use bob/custom_developer --in-project todo-app
```

### 项目管理

```bash
# 创建项目
./mas project create --name todo-app --description "Todo应用"

# 列出我的项目
./mas project list

# 切换到项目
./mas project use todo-app

# 在项目中运行工作流
./mas workflow run --project todo-app --title "添加用户认证"

# 查看项目状态
./mas project status todo-app

# 查看项目文件
./mas project files todo-app

# 归档项目
./mas project archive todo-app
```

### 工作流（项目级别）

```bash
# 在当前项目运行工作流
./mas workflow run --title "添加功能"

# 在指定项目运行工作流
./mas workflow run --project todo-app --title "添加功能"

# 查看项目的所有会话
./mas task list --project todo-app

# 查看项目的最新会话
./mas task show --project todo-app --latest
```

## 数据隔离保证

### 1. Agent数据隔离

```python
class AgentDataPath:
    def __init__(self, user_id: str, agent_name: str):
        self.base = f"users/{user_id}/agents/{agent_name}"
        self.memory = f"{self.base}/memory"
        self.cache = f"{self.base}/cache"
        self.workspace = f"{self.base}/workspace"
    
    def ensure_isolation(self):
        """确保Agent不能访问其他Agent的数据"""
        # 只能访问自己的目录
        # 使用chroot或权限控制
```

### 2. 项目数据隔离

```python
class ProjectDataPath:
    def __init__(self, user_id: str, project_name: str):
        self.base = f"users/{user_id}/projects/{project_name}"
        self.sessions = f"{self.base}/sessions"
        self.workspace = f"{self.base}/workspace"
        self.artifacts = f"{self.base}/artifacts"
        self.docs = f"{self.base}/docs"
    
    def ensure_isolation(self):
        """确保项目不能访问其他项目的数据"""
        # 每个项目完全隔离
        # Agent在项目中工作时，只能访问该项目的workspace
```

### 3. 用户数据隔离

```python
class UserDataPath:
    def __init__(self, user_id: str):
        self.base = f"users/{user_id}"
        self.agents = f"{self.base}/agents"
        self.projects = f"{self.base}/projects"
        self.profile = f"{self.base}/profile.yaml"
    
    def ensure_isolation(self):
        """确保用户不能访问其他用户的数据"""
        # 用户级别完全隔离
        # 除非明确授权（shared_agents）
```

## 迁移路径

从当前架构迁移到新架构：

```bash
# 1. 创建默认用户
./mas user init --username default_user

# 2. 迁移现有Agent
./mas migrate agents --from config/agents --to users/default_user/agents

# 3. 迁移现有会话到项目
./mas migrate sessions --from sessions --to users/default_user/projects/legacy

# 4. 验证迁移
./mas migrate verify
```

## 优势

1. **清晰的所有权**：每个Agent、项目都有明确的owner
2. **完全隔离**：用户、Agent、项目三层隔离，互不干扰
3. **灵活共享**：Agent可以选择性公开或分享
4. **项目独立**：每个项目有独立的工作空间和会话历史
5. **可扩展**：支持多用户协作、Agent市场等未来功能
6. **安全性**：权限控制在每一层都有保障

## 下一步实现

1. 实现用户管理系统
2. 重构Agent注册系统（加入用户层）
3. 实现项目管理系统
4. 更新CLI命令
5. 数据迁移工具
