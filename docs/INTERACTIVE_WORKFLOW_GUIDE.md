# 交互式工作流使用指南

## 概述

交互式工作流允许你实时查看Agent的工作过程，并在每个Agent完成后介入，提供反馈或调整方向。

## 启动交互式工作流

```bash
./cli/main.py workflow run --project my-project --title "任务标题" --interactive
```

## 交互模式特性

### 1. 实时查看Agent工作

每个Agent工作时，你可以看到：
- 🔄 当前Agent名称和角色
- 📝 Agent即将执行的任务描述
- ⏳ Agent工作进度
- ⏱️  执行耗时
- ✅/❌ 执行结果
- 📦 生成的产物

### 2. 暂停和介入

每个Agent完成后，工作流会自动暂停，等待你的指令：

```
⏸️  工作流已暂停，等待你的指令...
👉 [c]继续 / [s]跳过 / [r]重试 / [f]反馈 / [q]退出:
```

### 3. 可用操作

#### c - 继续 (Continue)
继续执行下一个Agent

```
👉 c
```

#### s - 跳过 (Skip)
跳过当前Agent的后续步骤，直接进入下一个Agent

```
👉 s
```

#### r - 重试 (Retry)
重新执行当前Agent

```
👉 r
```

#### f - 反馈 (Feedback)
提供反馈给当前Agent，然后选择继续或重试

```
👉 f
📝 请输入你的反馈: 需要添加错误处理
反馈后的操作 [c]继续 / [r]重试: r
```

#### q - 退出 (Quit)
终止整个工作流

```
👉 q
🛑 用户终止工作流
```

## 完整示例

### 场景：开发一个登录功能

```bash
# 1. 启动交互式工作流
./cli/main.py workflow run --project my-app --interactive

# 系统提示输入
任务标题: 实现用户登录功能
需求描述: 支持邮箱和密码登录，包含记住我功能

# 2. Requester Agent 开始工作
==================================================
🔄 第1轮 - 当前Agent: Requester (需求分析师)
==================================================

📝 Requester 将要:
   收集和分析需求，明确项目目标

⏳ Requester 正在工作...

⏱️  耗时: 3.45秒
✅ Requester 处理成功
📄 消息: 需求分析完成

📦 产物:
   - requirements_doc: 需求文档已生成

⏸️  工作流已暂停，等待你的指令...
👉 [c]继续 / [s]跳过 / [r]重试 / [f]反馈 / [q]退出: c

# 3. Product Manager Agent 开始工作
==================================================
🔄 第2轮 - 当前Agent: ProductManager (产品经理)
==================================================

📝 ProductManager 将要:
   制定产品规划，定义功能和优先级

⏳ ProductManager 正在工作...

⏱️  耗时: 4.12秒
✅ ProductManager 处理成功
📄 消息: 产品规划完成

📦 产物:
   - prd: 产品需求文档
   - user_stories: 用户故事

⏸️  工作流已暂停，等待你的指令...
👉 [c]继续 / [s]跳过 / [r]重试 / [f]反馈 / [q]退出: f
📝 请输入你的反馈: 需要增加双因素认证功能
反馈后的操作 [c]继续 / [r]重试: r

# ProductManager 重新工作，考虑你的反馈...

# 4. 继续后续Agent...
# Architect → Developer → CodeReviewer → Tester → DevOps

# 5. 工作流完成
==================================================
🎉 工作流执行成功!
==================================================

📊 执行摘要:
  任务ID: abc-123-def
  标题: 实现用户登录功能
  状态: completed
  总轮次: 7

📦 产物:
    - requirements_doc: 由 Requester 创建
    - prd: 由 ProductManager 创建
    - architecture_design: 由 Architect 创建
    - source_code: 由 Developer 创建
    - code_review_report: 由 CodeReviewer 创建
    - test_report: 由 Tester 创建
    - deployment_config: 由 DevOps 创建

💬 反馈记录: 1条
    1. [ProductManager] 需要增加双因素认证功能...
```

## 高级用法

### 1. 非交互模式

如果你不需要介入，可以使用非交互模式：

```bash
./cli/main.py workflow run --project my-app --no-interactive
```

Agent会自动依次执行，不会暂停等待。

### 2. 中途中断

在任何时候按 `Ctrl+C` 可以暂停工作流：

```
⚠️  检测到 Ctrl+C，暂停工作流
是否要终止工作流？
[y]终止 / [n]继续: n
```

### 3. 查看工作流历史

```bash
# 查看最近的工作流
./cli/main.py workflow monitor --latest

# 查看特定会话
./cli/main.py task show <session-id>
```

## 最佳实践

### 1. 何时使用交互模式

✅ **适合使用交互模式的场景：**
- 复杂或关键的功能开发
- 需要频繁调整方向的探索性任务
- 学习和理解Agent工作流程
- 需要严格控制每个阶段的输出

❌ **不适合使用交互模式的场景：**
- 简单重复的任务
- 已经验证过的标准流程
- 批量处理多个类似任务

### 2. 提供有效反馈

好的反馈示例：
```
✅ "需要添加输入验证，防止SQL注入"
✅ "架构设计中缺少缓存层，建议使用Redis"
✅ "测试覆盖率不足，需要增加边界条件测试"
```

不好的反馈示例：
```
❌ "不好"
❌ "重做"
❌ "有问题"
```

### 3. 何时跳过Agent

某些情况下可以跳过特定Agent：
- 已经有现成的设计文档（跳过Architect）
- 代码非常简单（跳过CodeReviewer）
- 不需要部署（跳过DevOps）

### 4. 何时重试Agent

需要重试的情况：
- Agent输出不符合预期
- 提供了新的反馈信息
- Agent遇到了临时错误

## 工作流状态

工作流执行后会保存到项目的sessions目录：

```
users/
  your_user/
    projects/
      my-project/
        sessions/
          abc-123-def.json  # 会话记录
```

会话记录包含：
- 所有Agent的输入输出
- 用户的反馈记录
- 执行时间和状态
- 生成的产物路径

## 故障排除

### 问题1：Agent执行失败

```
❌ Developer 处理失败
📄 消息: 代码编译错误

是否继续执行下一个Agent？
[y]继续 / [n]终止:
```

**解决方案：**
- 选择 `n` 终止，检查错误原因
- 修复问题后重新运行工作流

### 问题2：工作流卡住

如果Agent长时间没有响应：
1. 按 `Ctrl+C` 中断
2. 检查Agent配置和LLM API连接
3. 重新运行工作流

### 问题3：反馈没有生效

确保：
1. 反馈内容清晰具体
2. 选择了"重试"而不是"继续"
3. Agent有能力理解和执行你的反馈

## 与进度管理集成

交互式工作流会自动更新项目进度：

```bash
# 查看工作流对进度的影响
./cli/main.py progress show my-project

# 查看自动创建的任务
./cli/main.py progress tasks my-project
```

每个Agent完成后，对应的阶段进度会自动更新。

## 总结

交互式工作流让你能够：
- ✅ 实时监控Agent工作
- ✅ 及时发现和纠正问题
- ✅ 提供人类专业知识
- ✅ 控制工作流方向
- ✅ 学习Agent工作方式

这是一个强大的工具，让AI Agent和人类能够真正协作完成复杂任务。
