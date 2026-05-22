# CLI命令当前状态报告

## 命令可用性

| 命令组 | 状态 | 使用的目录 | 是否支持三层隔离 |
|--------|------|-----------|----------------|
| `user` | ✅ 可用 | `users/` | ✅ 是 |
| `project` | ✅ 可用 | `users/{user_id}/projects/` | ✅ 是 |
| `agent` | ⚠️ 部分可用 | `config/agents/` | ❌ 否（旧架构） |
| `task` | ⚠️ 部分可用 | `sessions/` | ❌ 否（旧架构） |
| `workflow` | ⚠️ 部分可用 | `sessions/` | ❌ 否（旧架构） |

## 详细说明

### ✅ user命令（完全可用）

```bash
./mas user init --username alice    # ✅ 工作正常
./mas user whoami                   # ✅ 工作正常
./mas user list                     # ✅ 工作正常
./mas user switch alice             # ✅ 工作正常
```

**使用的目录**: `users/`
**支持隔离**: ✅ 是

### ✅ project命令（完全可用）

```bash
./mas project create --name todo-app    # ✅ 工作正常
./mas project list                      # ✅ 工作正常
./mas project show todo-app             # ✅ 工作正常
./mas project use todo-app              # ✅ 工作正常
./mas project sessions todo-app         # ✅ 工作正常
```

**使用的目录**: `users/{user_id}/projects/`
**支持隔离**: ✅ 是

**注意**: 需要先运行`./mas user init`创建用户

### ⚠️ agent命令（部分可用，使用旧架构）

```bash
./mas agent list                    # ✅ 可用（显示旧Agent）
./mas agent show requester          # ✅ 可用
./mas agent register ...            # ✅ 可用（但保存到旧位置）
```

**使用的目录**: `config/agents/`（旧架构）
**支持隔离**: ❌ 否

**问题**:
- Agent不属于任何用户
- 所有用户共享同一套Agent
- 无法实现Agent的用户级隔离

**现有Agent**:
- requester
- product_manager
- architect
- developer
- code_reviewer
- tester
- devops

### ⚠️ task命令（部分可用，使用旧架构）

```bash
./mas task list                     # ✅ 可用（显示旧会话）
./mas task show --latest            # ✅ 可用
./mas task agents --latest          # ✅ 可用
```

**使用的目录**: `sessions/`（旧架构）
**支持隔离**: ❌ 否

**问题**:
- 会话不属于任何项目
- 所有会话混在一起
- 无法按项目查看会话

**现有会话**: 约150个历史会话文件

### ⚠️ workflow命令（部分可用，使用旧架构）

```bash
./mas workflow run --title "..."    # ✅ 可用（但保存到旧位置）
./mas workflow monitor --latest     # ✅ 可用
```

**使用的目录**: `sessions/`（旧架构）
**支持隔离**: ❌ 否

**问题**:
- 不支持`--project`参数
- 会话保存到`sessions/`而不是项目目录
- Agent工作在全局workspace，不是项目workspace

## 架构对比

### 旧架构（当前agent/task/workflow使用）

```
config/agents/
  ├── requester.yaml
  ├── developer.yaml
  └── ...

sessions/
  ├── session-001.json
  ├── session-002.json
  └── ...

data/agents/
  └── workspace/  # 所有项目混在一起
```

**问题**:
- ❌ 无用户概念
- ❌ 无项目隔离
- ❌ 所有文件混在一起

### 新架构（user/project使用）

```
users/
  └── user_alice/
      ├── agents/           # Alice的Agent
      └── projects/
          ├── todo-app/     # 项目1（完全隔离）
          │   ├── sessions/
          │   └── workspace/
          └── blog-system/  # 项目2（完全隔离）
```

**优势**:
- ✅ 用户隔离
- ✅ 项目隔离
- ✅ 清晰组织

## 需要做的工作

### 1. 更新Agent注册系统（高优先级）

**文件**: `src/agents/registration.py`

**需要修改**:
- 支持用户层：Agent保存到`users/{user_id}/agents/`
- 添加Agent元数据（是否公开、使用统计）
- 支持Agent共享机制

**影响的命令**:
- `./mas agent register`
- `./mas agent list`
- `./mas agent show`

### 2. 更新SessionManager（高优先级）

**文件**: `src/session_manager.py`

**需要修改**:
- 接受`user_id`和`project_name`参数
- 会话保存到`users/{user_id}/projects/{project_name}/sessions/`
- 支持按项目查询会话

**影响的命令**:
- `./mas task list`
- `./mas task show`
- `./mas workflow run`

### 3. 更新Workflow命令（高优先级）

**文件**: `cli/workflow_commands.py`

**需要修改**:
- 添加`--project`参数（必需）
- 从当前用户和项目获取上下文
- 传递项目workspace给Agent

**影响的命令**:
- `./mas workflow run`
- `./mas workflow monitor`

### 4. 更新Orchestrator（中优先级）

**文件**: `src/orchestrator.py`

**需要修改**:
- 接受项目上下文
- 传递项目workspace给Agent
- Agent工作在项目workspace而不是全局workspace

### 5. 更新BaseAgent（中优先级）

**文件**: `src/agents/base_agent.py`

**需要修改**:
- 接受`project_context`参数
- 文件操作限制在项目workspace内
- 产物保存到项目artifacts目录

### 6. 数据迁移工具（低优先级）

**新文件**: `tools/migrate.py`

**功能**:
- 迁移现有Agent到默认用户
- 迁移现有会话到默认项目
- 验证迁移结果

## 推荐的实施步骤

### 阶段1：核心系统更新（必需）

1. 更新Agent注册系统支持用户层
2. 更新SessionManager支持项目层
3. 更新Workflow命令添加--project参数

### 阶段2：Agent集成（必需）

4. 更新Orchestrator传递项目上下文
5. 更新BaseAgent支持项目workspace

### 阶段3：数据迁移（可选）

6. 创建迁移工具
7. 迁移现有数据到新架构

## 临时解决方案

在完成更新之前，可以这样使用：

### 使用新架构（推荐）

```bash
# 1. 创建用户
./mas user init --username alice

# 2. 创建项目
./mas project create --name todo-app

# 3. 手动注册Agent到用户目录（需要实现）
# 暂时无法使用，需要等待更新

# 4. 运行工作流（暂时还是旧方式）
./mas workflow run --title "..."  # 保存到sessions/
```

### 使用旧架构（临时）

```bash
# 直接使用，不需要创建用户和项目
./mas agent list
./mas workflow run --title "..."
./mas task show --latest
```

## 总结

### 当前可用性

- ✅ **user和project命令**: 完全可用，新架构
- ⚠️ **agent/task/workflow命令**: 部分可用，旧架构

### 核心问题

- Agent、Task、Workflow还在使用旧的目录结构
- 没有集成三层隔离架构
- 新旧系统并存，需要统一

### 下一步

**立即需要做的**:
1. 更新Agent注册系统支持用户层
2. 更新SessionManager支持项目层
3. 更新Workflow命令支持--project参数

**完成后**:
- 所有命令都支持三层隔离
- 可以完整使用新架构
- 提供数据迁移工具处理旧数据

## 测试命令

```bash
# 测试新命令
./mas user init --username alice
./mas project create --name test-project
./mas project list

# 测试旧命令（仍然可用）
./mas agent list
./mas task list
./mas workflow run --title "test"
```
