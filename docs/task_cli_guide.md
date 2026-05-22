# 任务管理CLI使用指南

## 概述

任务管理CLI让你可以查看工作流执行状态和各个Agent的回复。

## 命令列表

### 1. 列出所有会话

```bash
./mas task list

# 限制显示数量
./mas task list --limit 5
```

**输出示例**：
```
+-------------+--------------+--------+-------+---------------------+
| 会话ID        | 用户           | 状态     |   任务数 | 创建时间                |
+=============+==============+========+=======+=====================+
| 084760cf... | demo_user    | failed |     1 | 2026-05-20T17:49:41 |
| 876847ad... | demo_user    | active |     1 | 2026-05-20T17:47:29 |
+-------------+--------------+--------+-------+---------------------+
```

### 2. 查看会话详情

```bash
# 查看最新会话
./mas task show --latest

# 查看指定会话（支持部分ID匹配）
./mas task show 084760cf
```

**显示内容**：
- 会话基本信息（ID、用户、状态、时间）
- 任务信息（标题、描述、状态、当前Agent）
- 所有Agent的回复（按时间顺序）
- 每个回复的详细内容：
  - 需求总结
  - 清晰度和完整度评分
  - 关键功能列表
  - 约束条件
  - 澄清问题
  - 可行性评估
  - 建议

### 3. 查看Agent状态摘要

```bash
# 查看最新会话的所有Agent状态
./mas task agents --latest

# 查看指定会话
./mas task agents 084760cf

# 只查看某个Agent的回复
./mas task agents --latest --agent Requester
```

**输出示例**：
```
================================================================================
会话: 084760cf-fc66-46... (failed)
================================================================================

任务: 开发一个简单的Todo应用

Agent状态:

  [Requester] - 10个回复
    总结: 开发一个基于Web的Todo待办事项管理应用...
    评分: 清晰度6/10, 完整度5/10
    问题: 10个澄清问题

  [ProductManager] - 3个回复
    总结: 产品设计方案...
    ...
```

## 使用场景

### 场景1：查看最新任务的执行情况

```bash
# 1. 列出所有会话，找到最新的
./mas task list

# 2. 查看最新会话的详细信息
./mas task show --latest

# 3. 查看各Agent的状态摘要
./mas task agents --latest
```

### 场景2：查看特定Agent的回复

```bash
# 只查看Requester的分析
./mas task agents --latest --agent Requester

# 只查看Developer的代码
./mas task agents --latest --agent Developer
```

### 场景3：追踪任务进度

```bash
# 运行工作流
python3 demo/agent_collaboration.py --mode workflow

# 在另一个终端查看实时进度
watch -n 5 './mas task agents --latest'
```

### 场景4：调试失败的任务

```bash
# 1. 找到失败的会话
./mas task list

# 2. 查看详细错误信息
./mas task show <session_id>

# 3. 查看哪个Agent失败了
./mas task agents <session_id>
```

## 完整命令参考

### task list

列出所有会话。

**选项**：
- `--limit N`: 显示最近N个会话（默认10）

**示例**：
```bash
./mas task list
./mas task list --limit 20
```

### task show

显示会话详情和所有Agent回复。

**参数**：
- `SESSION_ID`: 会话ID（可以是部分ID）

**选项**：
- `--latest`: 显示最新的会话

**示例**：
```bash
./mas task show --latest
./mas task show 084760cf
./mas task show 084760cf-fc66-4629-b200-517084a50a5a
```

### task agents

显示各个Agent的状态和回复摘要。

**参数**：
- `SESSION_ID`: 会话ID（可以是部分ID）

**选项**：
- `--latest`: 显示最新的会话
- `--agent NAME`: 只显示指定Agent的回复

**示例**：
```bash
./mas task agents --latest
./mas task agents 084760cf
./mas task agents --latest --agent Requester
./mas task agents --latest --agent Developer
```

## 会话状态说明

- `active`: 会话正在进行中
- `completed`: 工作流成功完成
- `failed`: 工作流失败（通常是需求不清晰或Agent处理失败）

## 任务状态说明

- `created`: 任务已创建
- `in_requirement`: 需求分析阶段（Requester）
- `in_design`: 设计阶段（ProductManager/Architect）
- `in_development`: 开发阶段（Developer）
- `in_review`: 审查阶段（CodeReviewer）
- `in_testing`: 测试阶段（Tester）
- `in_deployment`: 部署阶段（DevOps）
- `completed`: 任务完成
- `rejected`: 任务被拒绝

## Agent回复类型

- `requirement_analysis`: 需求分析（Requester）
- `product_design`: 产品设计（ProductManager）
- `architecture_design`: 架构设计（Architect）
- `code_implementation`: 代码实现（Developer）
- `code_review`: 代码审查（CodeReviewer）
- `test_report`: 测试报告（Tester）
- `deployment_report`: 部署报告（DevOps）

## 技巧

### 1. 使用部分ID匹配

不需要输入完整的会话ID：
```bash
# 完整ID
./mas task show 084760cf-fc66-4629-b200-517084a50a5a

# 部分ID（只要能唯一匹配）
./mas task show 084760cf
./mas task show 0847
```

### 2. 结合其他命令

```bash
# 查看最新会话的Agent状态，并保存到文件
./mas task agents --latest > task_status.txt

# 监控任务进度
watch -n 10 './mas task agents --latest'

# 查找失败的会话
./mas task list | grep failed
```

### 3. 快速查看最新状态

```bash
# 一行命令查看最新任务的Agent状态
./mas task agents --latest
```

## 常见问题

### Q: 如何查看正在运行的任务？

A: 使用 `./mas task agents --latest` 可以看到最新会话的Agent状态。

### Q: 如何查看某个Agent的详细回复？

A: 使用 `./mas task show --latest` 查看所有Agent的详细回复，或使用 `./mas task agents --latest --agent Requester` 查看特定Agent。

### Q: 会话文件存储在哪里？

A: 会话文件存储在 `sessions/` 目录下，每个会话一个JSON文件。

### Q: 如何删除旧的会话？

A: 直接删除 `sessions/` 目录下的JSON文件即可：
```bash
# 删除所有会话
rm sessions/*.json

# 删除特定会话
rm sessions/084760cf-fc66-4629-b200-517084a50a5a.json
```

## 总结

任务管理CLI提供了完整的任务追踪和Agent状态查看功能：
- ✅ 列出所有会话
- ✅ 查看会话详情
- ✅ 查看Agent回复
- ✅ 查看Agent状态摘要
- ✅ 支持部分ID匹配
- ✅ 支持过滤特定Agent

配合Agent管理CLI，你可以完整地管理和监控整个多Agent协作系统。
