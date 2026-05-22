# CLI命令完整测试指南

本文档提供所有CLI命令的测试步骤和预期结果。

## 测试环境准备

```bash
# 1. 确保在项目根目录
cd /home/mamingchang/multi-agent-dev-system

# 2. 确保CLI可执行
chmod +x cli/main.py

# 3. 创建测试用户
./cli/main.py user init --username test_user
```

## 1. 用户管理测试

### 1.1 创建用户
```bash
./cli/main.py user init --username alice
```
**预期结果**: 创建用户alice，显示用户目录路径

### 1.2 查看当前用户
```bash
./cli/main.py user whoami
```
**预期结果**: 显示当前用户信息

### 1.3 列出所有用户
```bash
./cli/main.py user list
```
**预期结果**: 显示所有用户列表

## 2. Agent管理测试

### 2.1 列出可用Agent
```bash
./cli/main.py agent list
```
**预期结果**: 显示所有已注册的Agent

### 2.2 从模板注册Agent
```bash
./cli/main.py agent register --method template --name my-pm --template product_manager
```
**预期结果**: 成功注册Agent，显示Agent ID

### 2.3 查看Agent详情
```bash
./cli/main.py agent show my-pm
```
**预期结果**: 显示Agent配置和元数据

### 2.4 删除Agent
```bash
./cli/main.py agent unregister my-pm
```
**预期结果**: 成功删除Agent

## 3. 项目管理测试

### 3.1 创建项目
```bash
./cli/main.py project create --name test-project --description "测试项目"
```
**预期结果**: 创建项目，显示项目路径

### 3.2 列出项目
```bash
./cli/main.py project list
```
**预期结果**: 显示所有项目列表

### 3.3 切换项目
```bash
./cli/main.py project use test-project
```
**预期结果**: 切换到指定项目

### 3.4 查看项目详情
```bash
./cli/main.py project show test-project
```
**预期结果**: 显示项目配置和状态

## 4. 项目导入测试

### 4.1 从模板创建项目
```bash
./cli/main.py import template --template web-app --name my-web-app
```
**预期结果**: 从模板创建项目，生成基础文件结构

### 4.2 列出可用模板
```bash
./cli/main.py import templates
```
**预期结果**: 显示所有可用的项目模板

### 4.3 从本地目录导入
```bash
# 先创建一个测试目录
mkdir -p /tmp/test-import
echo "print('hello')" > /tmp/test-import/main.py
echo "flask" > /tmp/test-import/requirements.txt

# 导入
./cli/main.py import dir --path /tmp/test-import --name imported-project
```
**预期结果**: 分析项目，创建项目，复制文件，初始化进度

### 4.4 从Git导入（需要网络）
```bash
./cli/main.py import git --url https://github.com/pallets/flask.git --name flask-project --branch main
```
**预期结果**: 克隆仓库，分析项目，初始化进度

## 5. 项目导出测试

### 5.1 导出为项目包
```bash
./cli/main.py export package test-project --output /tmp/test-project.mas
```
**预期结果**: 创建.mas文件，显示文件大小和包含内容

### 5.2 导出进度报告（Markdown）
```bash
./cli/main.py export report test-project --format markdown --output /tmp/report.md
```
**预期结果**: 生成Markdown格式的进度报告

### 5.3 导出进度报告（JSON）
```bash
./cli/main.py export report test-project --format json --output /tmp/report.json
```
**预期结果**: 生成JSON格式的进度报告

### 5.4 导出到Git（需要远程仓库）
```bash
# 需要先创建远程仓库
./cli/main.py export git test-project --remote https://github.com/user/repo.git --branch main
```
**预期结果**: 初始化git，提交，推送到远程

## 6. 进度管理测试

### 6.1 查看整体进度
```bash
./cli/main.py progress show test-project
```
**预期结果**: 显示整体进度、阶段进度、任务统计

### 6.2 查看阶段详情
```bash
./cli/main.py progress phase test-project development
```
**预期结果**: 显示开发阶段的详细信息和任务列表

### 6.3 开始阶段
```bash
./cli/main.py progress phase-start test-project development --agent Developer
```
**预期结果**: 标记阶段为进行中

### 6.4 完成阶段
```bash
./cli/main.py progress phase-complete test-project requirement_analysis
```
**预期结果**: 标记阶段为已完成

### 6.5 创建任务
```bash
./cli/main.py progress task-create test-project \
  --title "实现用户注册API" \
  --phase development \
  --priority high \
  --agent Developer \
  --description "实现用户注册功能的RESTful API"
```
**预期结果**: 创建任务，返回任务ID

### 6.6 查看任务列表
```bash
./cli/main.py progress tasks test-project
```
**预期结果**: 显示所有任务

### 6.7 过滤任务
```bash
# 按阶段过滤
./cli/main.py progress tasks test-project --phase development

# 按状态过滤
./cli/main.py progress tasks test-project --status in_progress

# 按Agent过滤
./cli/main.py progress tasks test-project --agent Developer
```
**预期结果**: 显示过滤后的任务列表

### 6.8 更新任务状态
```bash
./cli/main.py progress task-update test-project task-001 --status in_progress
```
**预期结果**: 更新任务状态

### 6.9 更新任务进度
```bash
./cli/main.py progress task-update test-project task-001 --progress 50
```
**预期结果**: 更新任务进度

### 6.10 完成任务
```bash
./cli/main.py progress task-update test-project task-001 --status completed --progress 100
```
**预期结果**: 标记任务为已完成

## 7. 工作流测试

### 7.1 运行工作流
```bash
./cli/main.py workflow run --project test-project --title "实现登录功能"
```
**预期结果**: 启动交互式工作流，各Agent依次工作

### 7.2 监控工作流
```bash
./cli/main.py workflow monitor --latest
```
**预期结果**: 显示最新工作流的执行状态

## 8. 完整流程测试

### 场景1：从零开始创建项目

```bash
# 1. 创建用户
./cli/main.py user init --username bob

# 2. 从模板创建项目
./cli/main.py import template --template web-app --name my-app

# 3. 查看初始进度
./cli/main.py progress show my-app

# 4. 开始开发阶段
./cli/main.py progress phase-start my-app development --agent Developer

# 5. 创建开发任务
./cli/main.py progress task-create my-app \
  --title "实现首页" \
  --phase development \
  --priority high \
  --agent Developer

# 6. 运行工作流
./cli/main.py workflow run --project my-app --title "开发首页功能"

# 7. 导出项目包
./cli/main.py export package my-app --output /tmp/my-app-backup.mas

# 8. 导出进度报告
./cli/main.py export report my-app --format markdown --output /tmp/my-app-report.md
```

### 场景2：导入现有项目

```bash
# 1. 从Git导入
./cli/main.py import git --url https://github.com/user/repo.git --name existing-project

# 2. 查看分析结果和初始进度
./cli/main.py progress show existing-project

# 3. 查看自动创建的任务
./cli/main.py progress tasks existing-project

# 4. 继续开发
./cli/main.py workflow run --project existing-project --title "添加新功能"
```

### 场景3：项目迁移

```bash
# 1. 导出项目A
./cli/main.py export package project-a --output /tmp/project-a.mas

# 2. 在另一个环境导入
./cli/main.py import package --file /tmp/project-a.mas --name project-a-restored

# 3. 验证进度和记忆都已恢复
./cli/main.py progress show project-a-restored
```

## 9. 错误处理测试

### 9.1 导入不存在的项目包
```bash
./cli/main.py import package --file /tmp/nonexistent.mas --name test
```
**预期结果**: 显示错误信息"项目包不存在"

### 9.2 导出不存在的项目
```bash
./cli/main.py export package nonexistent-project --output /tmp/test.mas
```
**预期结果**: 显示错误信息"项目不存在"

### 9.3 创建重复的项目
```bash
./cli/main.py project create --name test-project
./cli/main.py project create --name test-project
```
**预期结果**: 第二次显示错误信息"项目已存在"

### 9.4 更新不存在的任务
```bash
./cli/main.py progress task-update test-project task-999 --status completed
```
**预期结果**: 任务不存在，但不会报错（静默失败）

## 10. 性能测试

### 10.1 大型项目导入
```bash
# 导入一个大型开源项目
./cli/main.py import git --url https://github.com/django/django.git --name django-project
```
**预期结果**: 能够成功分析和导入，显示正确的统计信息

### 10.2 大量任务管理
```bash
# 创建100个任务
for i in {1..100}; do
  ./cli/main.py progress task-create test-project \
    --title "Task $i" \
    --phase development \
    --priority medium \
    --agent Developer
done

# 查看任务列表
./cli/main.py progress tasks test-project
```
**预期结果**: 能够正常创建和显示所有任务

## 11. 集成测试

### 11.1 完整开发流程
```bash
# 1. 初始化
./cli/main.py user init --username dev1
./cli/main.py import template --template web-app --name full-test

# 2. 需求分析阶段
./cli/main.py progress phase-start full-test requirement_analysis --agent Requester
./cli/main.py progress task-create full-test --title "收集需求" --phase requirement_analysis --agent Requester --priority high
./cli/main.py progress task-update full-test task-001 --status completed
./cli/main.py progress phase-complete full-test requirement_analysis

# 3. 产品规划阶段
./cli/main.py progress phase-start full-test product_planning --agent "Product Manager"
./cli/main.py progress task-create full-test --title "编写PRD" --phase product_planning --agent "Product Manager" --priority high
./cli/main.py progress task-update full-test task-002 --status completed
./cli/main.py progress phase-complete full-test product_planning

# 4. 架构设计阶段
./cli/main.py progress phase-start full-test architecture_design --agent Architect
./cli/main.py progress task-create full-test --title "设计系统架构" --phase architecture_design --agent Architect --priority critical
./cli/main.py progress task-update full-test task-003 --status completed
./cli/main.py progress phase-complete full-test architecture_design

# 5. 开发阶段
./cli/main.py progress phase-start full-test development --agent Developer
./cli/main.py progress task-create full-test --title "实现核心功能" --phase development --agent Developer --priority high
./cli/main.py progress task-update full-test task-004 --status in_progress --progress 50

# 6. 查看整体进度
./cli/main.py progress show full-test

# 7. 导出报告
./cli/main.py export report full-test --format markdown --output /tmp/full-test-report.md

# 8. 导出项目包
./cli/main.py export package full-test --output /tmp/full-test.mas
```

## 测试检查清单

- [ ] 用户管理：创建、查看、列出
- [ ] Agent管理：注册、查看、删除
- [ ] 项目管理：创建、列出、切换、查看
- [ ] 项目导入：模板、本地目录、Git、项目包
- [ ] 项目导出：项目包、Git、报告（3种格式）
- [ ] 进度管理：查看进度、阶段管理、任务CRUD
- [ ] 工作流：运行、监控
- [ ] 错误处理：各种异常情况
- [ ] 性能：大型项目、大量任务
- [ ] 集成：完整开发流程

## 已知问题

1. Git导入需要网络连接
2. Git导出需要远程仓库权限
3. 大型项目分析可能需要较长时间
4. 任务更新不存在的任务ID时静默失败（需要改进）

## 下一步改进

1. 添加进度可视化（甘特图、燃尽图）
2. 添加Web仪表盘
3. 添加任务依赖关系验证
4. 添加更多项目模板
5. 优化大型项目的分析性能
6. 添加任务评论和附件功能
7. 添加里程碑管理CLI命令
