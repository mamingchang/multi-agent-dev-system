# 三层隔离架构下的文件管理机制

## 文件管理概述

三层隔离后，文件管理遵循**严格的层级隔离原则**：

```
用户层 (User)
  ↓ 拥有
Agent层 (Agent) + 项目层 (Project)
  ↓ 工作在
文件层 (Files)
```

## 完整目录结构

```
multi-agent-dev-system/
├── users/                          # 用户数据根目录
│   ├── user_alice/                 # 用户alice的命名空间
│   │   ├── profile.yaml            # 用户配置
│   │   ├── .current_project        # 当前项目指针
│   │   │
│   │   ├── agents/                 # Alice注册的Agent
│   │   │   ├── my_custom_pm/       # 自定义产品经理Agent
│   │   │   │   ├── config.yaml     # Agent配置
│   │   │   │   ├── metadata.yaml   # 元数据（是否公开、使用统计）
│   │   │   │   ├── memory/         # Agent记忆（长期/短期）
│   │   │   │   │   ├── long_term/
│   │   │   │   │   └── short_term/
│   │   │   │   ├── cache/          # Agent缓存
│   │   │   │   └── workspace/      # Agent临时工作空间
│   │   │   │
│   │   │   └── my_developer/       # 自定义开发者Agent
│   │   │       └── ...
│   │   │
│   │   └── projects/               # Alice的项目
│   │       ├── todo-app/           # 项目1：Todo应用
│   │       │   ├── project.yaml    # 项目配置
│   │       │   │
│   │       │   ├── sessions/       # 该项目的所有会话
│   │       │   │   ├── 2026-05-21_001_requirement.json
│   │       │   │   ├── 2026-05-21_002_add_auth.json
│   │       │   │   └── 2026-05-22_003_fix_bug.json
│   │       │   │
│   │       │   ├── workspace/      # 项目代码（完全隔离）
│   │       │   │   ├── src/
│   │       │   │   │   ├── app.py
│   │       │   │   │   ├── models.py
│   │       │   │   │   └── routes.py
│   │       │   │   ├── tests/
│   │       │   │   │   └── test_app.py
│   │       │   │   ├── requirements.txt
│   │       │   │   ├── README.md
│   │       │   │   └── .gitignore
│   │       │   │
│   │       │   ├── artifacts/      # 产物（按Agent类型分类）
│   │       │   │   ├── requirements/
│   │       │   │   │   ├── v1_initial.md
│   │       │   │   │   └── v2_refined.md
│   │       │   │   ├── designs/
│   │       │   │   │   ├── prd_v1.md
│   │       │   │   │   ├── architecture_v1.md
│   │       │   │   │   └── api_design.yaml
│   │       │   │   ├── code/
│   │       │   │   │   ├── iteration_1/
│   │       │   │   │   └── iteration_2/
│   │       │   │   ├── tests/
│   │       │   │   │   └── test_report_v1.md
│   │       │   │   ├── reviews/
│   │       │   │   │   └── code_review_v1.md
│   │       │   │   └── deployments/
│   │       │   │       └── deployment_log.md
│   │       │   │
│   │       │   └── docs/           # 生成的文档
│   │       │       ├── API.md
│   │       │       ├── ARCHITECTURE.md
│   │       │       └── USER_GUIDE.md
│   │       │
│   │       └── blog-system/        # 项目2：博客系统（完全隔离）
│   │           ├── project.yaml
│   │           ├── sessions/
│   │           ├── workspace/
│   │           ├── artifacts/
│   │           └── docs/
│   │
│   └── user_bob/                   # 用户bob的命名空间（完全隔离）
│       ├── profile.yaml
│       ├── agents/
│       └── projects/
│
├── shared_agents/                  # 公开Agent索引
│   ├── index.yaml                  # 所有公开Agent的索引
│   └── user_alice/
│       └── my_custom_pm -> ../../users/user_alice/agents/my_custom_pm
│
├── templates/                      # 系统模板
│   ├── agents/                     # Agent模板
│   │   ├── requester.yaml
│   │   ├── product_manager.yaml
│   │   └── developer.yaml
│   └── projects/                   # 项目模板
│       └── default/
│
└── config/                         # 系统配置
    └── system.yaml
```

## 文件管理规则

### 1. 用户级别文件管理

**路径**: `users/{user_id}/`

**管理器**: `UserManager` (`src/user_manager.py`)

**规则**:
- 每个用户有独立的根目录
- 用户之间完全隔离，无法访问其他用户的文件
- 用户配置存储在 `profile.yaml`
- 当前项目指针存储在 `.current_project`

**示例**:
```python
from src.user_manager import UserManager

manager = UserManager()

# 创建用户（自动创建目录结构）
user = manager.create_user(username="alice", email="alice@example.com")
# 创建: users/user_alice/profile.yaml
#       users/user_alice/agents/
#       users/user_alice/projects/

# 获取用户目录
agents_dir = manager.get_user_agents_dir("user_alice")
# 返回: users/user_alice/agents/

projects_dir = manager.get_user_projects_dir("user_alice")
# 返回: users/user_alice/projects/
```

### 2. 项目级别文件管理

**路径**: `users/{user_id}/projects/{project_name}/`

**管理器**: `ProjectManager` (`src/project_manager.py`)

**规则**:
- 每个项目有独立的工作空间
- 项目之间完全隔离
- 所有项目相关文件都在项目目录下
- 不同项目的代码、会话、产物互不干扰

**目录说明**:

| 目录 | 用途 | 管理方式 |
|------|------|----------|
| `workspace/` | 生成的代码 | Agent写入，Git管理 |
| `sessions/` | 工作流会话记录 | SessionManager写入 |
| `artifacts/` | Agent产物（需求、设计、测试报告等） | Agent写入，按类型分类 |
| `docs/` | 生成的文档 | Agent写入 |
| `project.yaml` | 项目配置 | ProjectManager管理 |

**示例**:
```python
from src.project_manager import ProjectManager

manager = ProjectManager(user_id="user_alice")

# 创建项目（自动创建完整目录结构）
project = manager.create_project(
    project_name="todo-app",
    description="Todo应用"
)
# 创建: users/user_alice/projects/todo-app/
#       users/user_alice/projects/todo-app/workspace/
#       users/user_alice/projects/todo-app/sessions/
#       users/user_alice/projects/todo-app/artifacts/
#       users/user_alice/projects/todo-app/docs/

# 获取项目工作空间
workspace = manager.get_project_workspace("todo-app")
# 返回: users/user_alice/projects/todo-app/workspace/

# 获取项目会话目录
sessions_dir = manager.get_project_sessions_dir("todo-app")
# 返回: users/user_alice/projects/todo-app/sessions/

# 获取项目产物目录
artifacts_dir = manager.get_project_artifacts_dir("todo-app")
# 返回: users/user_alice/projects/todo-app/artifacts/
```

### 3. Agent级别文件管理

**路径**: `users/{user_id}/agents/{agent_name}/`

**管理器**: `AgentRegistration` (需要更新以支持用户层)

**规则**:
- 每个Agent有独立的配置和数据目录
- Agent的记忆、缓存完全隔离
- Agent在项目中工作时，只能访问该项目的workspace

**目录说明**:

| 目录 | 用途 | 管理方式 |
|------|------|----------|
| `config.yaml` | Agent配置 | AgentRegistration管理 |
| `metadata.yaml` | 元数据（是否公开、使用统计） | AgentRegistration管理 |
| `memory/` | Agent记忆 | Agent自己管理 |
| `cache/` | Agent缓存 | Agent自己管理 |
| `workspace/` | Agent临时工作空间 | Agent自己管理 |

## 文件访问控制

### Agent访问项目文件的流程

```python
# 1. 用户运行工作流
./mas workflow run --project todo-app --title "添加功能"

# 2. Orchestrator加载项目信息
project_manager = ProjectManager(user_id="user_alice")
project = project_manager.get_project("todo-app")

# 3. 获取项目工作空间路径
workspace_path = project_manager.get_project_workspace("todo-app")
# workspace_path = "users/user_alice/projects/todo-app/workspace/"

# 4. Agent初始化时传入项目上下文
agent = DeveloperAgent(
    name="Developer",
    config=agent_config,
    project_context={
        'project_name': 'todo-app',
        'workspace_path': workspace_path,
        'artifacts_path': project_manager.get_project_artifacts_dir("todo-app")
    }
)

# 5. Agent只能访问该项目的workspace
# Agent内部使用相对路径或受限的绝对路径
agent.write_file("src/app.py", code)
# 实际写入: users/user_alice/projects/todo-app/workspace/src/app.py
```

### 文件隔离保证机制

```python
class ProjectFileManager:
    """项目文件管理器（确保隔离）"""
    
    def __init__(self, project_workspace: Path):
        self.workspace = project_workspace.resolve()
    
    def write_file(self, relative_path: str, content: str):
        """写入文件（确保在workspace内）"""
        target = (self.workspace / relative_path).resolve()
        
        # 安全检查：确保目标路径在workspace内
        if not str(target).startswith(str(self.workspace)):
            raise SecurityError(f"不允许访问workspace外的文件: {target}")
        
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def read_file(self, relative_path: str) -> str:
        """读取文件（确保在workspace内）"""
        target = (self.workspace / relative_path).resolve()
        
        # 安全检查
        if not str(target).startswith(str(self.workspace)):
            raise SecurityError(f"不允许访问workspace外的文件: {target}")
        
        with open(target, 'r', encoding='utf-8') as f:
            return f.read()
```

## 会话管理

### 会话保存到项目目录

**旧方式**（无隔离）:
```python
# 所有会话混在一起
sessions/
  ├── session-001.json
  ├── session-002.json
  └── session-003.json
```

**新方式**（项目隔离）:
```python
# 每个项目的会话独立存储
users/user_alice/projects/todo-app/sessions/
  ├── 2026-05-21_001_requirement.json
  ├── 2026-05-21_002_add_auth.json
  └── 2026-05-22_003_fix_bug.json

users/user_alice/projects/blog-system/sessions/
  ├── 2026-05-21_001_initial.json
  └── 2026-05-22_002_add_comments.json
```

**SessionManager更新**（需要实现）:
```python
class SessionManager:
    def __init__(self, user_id: str, project_name: str):
        self.user_id = user_id
        self.project_name = project_name
        
        # 会话保存到项目目录
        project_manager = ProjectManager(user_id)
        self.sessions_dir = project_manager.get_project_sessions_dir(project_name)
    
    def save_session(self, session: Session):
        """保存会话到项目目录"""
        session_file = self.sessions_dir / f"{session.session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session.to_dict(), f, indent=2)
```

## 产物管理

### 产物分类存储

```
artifacts/
  ├── requirements/      # Requester的产物
  │   ├── v1_initial.md
  │   └── v2_refined.md
  │
  ├── designs/           # ProductManager和Architect的产物
  │   ├── prd_v1.md
  │   ├── architecture_v1.md
  │   └── api_design.yaml
  │
  ├── code/              # Developer的产物
  │   ├── iteration_1/
  │   │   ├── app.py
  │   │   └── models.py
  │   └── iteration_2/
  │       └── routes.py
  │
  ├── tests/             # Tester的产物
  │   ├── test_report_v1.md
  │   └── test_results.json
  │
  ├── reviews/           # CodeReviewer的产物
  │   ├── code_review_v1.md
  │   └── review_checklist.md
  │
  └── deployments/       # DevOps的产物
      ├── deployment_log.md
      └── deployment_config.yaml
```

### Agent保存产物

```python
class BaseAgent:
    def save_artifact(self, artifact_type: str, content: Any, filename: str):
        """保存产物到项目artifacts目录"""
        if not self.project_context:
            raise ValueError("未设置项目上下文")
        
        artifacts_dir = self.project_context['artifacts_path']
        artifact_subdir = artifacts_dir / artifact_type
        artifact_subdir.mkdir(parents=True, exist_ok=True)
        
        artifact_file = artifact_subdir / filename
        
        if isinstance(content, dict):
            with open(artifact_file, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2)
        else:
            with open(artifact_file, 'w', encoding='utf-8') as f:
                f.write(str(content))

# 使用示例
class RequesterAgent(BaseAgent):
    def process(self, task: Task):
        # 分析需求
        analysis = self.analyze_requirement(task.description)
        
        # 保存产物
        self.save_artifact(
            artifact_type="requirements",
            content=analysis,
            filename=f"requirement_v{task.iteration}.md"
        )
        # 保存到: users/user_alice/projects/todo-app/artifacts/requirements/requirement_v1.md
```

## 文件查询

### 查看项目文件

```bash
# 查看项目工作空间
ls users/user_alice/projects/todo-app/workspace/

# 查看项目会话
./mas project sessions todo-app

# 查看项目产物
ls users/user_alice/projects/todo-app/artifacts/

# 查看特定类型的产物
ls users/user_alice/projects/todo-app/artifacts/requirements/
```

### CLI命令（需要添加）

```bash
# 查看项目文件树
./mas project files todo-app

# 查看项目产物
./mas project artifacts todo-app

# 查看特定产物
./mas project artifacts todo-app --type requirements
```

## 文件清理

### 项目归档

```bash
# 归档项目（保留文件，标记为archived）
./mas project archive todo-app

# 项目状态变为archived，但文件保留
users/user_alice/projects/todo-app/  # 仍然存在
```

### 项目删除

```bash
# 删除项目（永久删除所有文件）
./mas project delete todo-app

# 整个项目目录被删除
users/user_alice/projects/todo-app/  # 不存在
```

## 备份和恢复

### 项目备份

```bash
# 备份整个项目
tar -czf todo-app-backup.tar.gz users/user_alice/projects/todo-app/

# 或使用Git
cd users/user_alice/projects/todo-app/workspace/
git init
git add .
git commit -m "Initial commit"
git remote add origin <repo-url>
git push
```

### 项目恢复

```bash
# 从备份恢复
tar -xzf todo-app-backup.tar.gz

# 或从Git克隆
cd users/user_alice/projects/
git clone <repo-url> todo-app-restored
```

## 总结

### 文件管理的三层隔离

1. **用户层**: `users/{user_id}/`
   - 每个用户独立命名空间
   - 用户之间完全隔离

2. **项目层**: `users/{user_id}/projects/{project_name}/`
   - 每个项目独立工作空间
   - 项目之间完全隔离
   - 包含：workspace、sessions、artifacts、docs

3. **Agent层**: `users/{user_id}/agents/{agent_name}/`
   - 每个Agent独立配置和数据
   - Agent在项目中工作时受限于项目workspace

### 关键特性

✅ **完全隔离**: 用户、项目、Agent三层隔离
✅ **清晰组织**: 代码、会话、产物、文档分类存储
✅ **安全访问**: Agent只能访问当前项目的workspace
✅ **易于管理**: 通过CLI命令管理所有文件
✅ **易于备份**: 每个项目是独立的目录树

### 下一步

需要更新现有系统以支持项目级文件管理：
1. 更新SessionManager保存到项目目录
2. 更新Agent添加project_context
3. 实现ProjectFileManager确保隔离
4. 添加文件查询CLI命令
