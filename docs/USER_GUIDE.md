# Multi-Agent系统使用指南

## 快速开始

### 方式1: 交互式创建项目（推荐）

```bash
cd /home/mamingchang/multi-agent-dev-system
python3 scripts/create_project_interactive.py
```

**这个脚本会引导你：**
1. 输入用户ID（默认：user_test）
2. 创建新项目或选择现有项目
3. 输入项目需求描述
4. 自动调用Agent团队开发
5. 生成可运行的代码

**示例对话：**
```
请输入用户ID [user_test]: 
  ✓ 用户ID: user_test

项目名称（英文，如: my_app）: todo_app
项目描述（中文）: 待办事项管理工具
  ✓ 项目创建成功: todo_app

请描述你想开发的项目（可以多行输入，输入空行结束）:
开发一个待办事项管理工具
支持添加、删除、标记完成任务
使用命令行界面
[按回车结束输入]

是否开始开发？(y/n) [y]: y
```

### 方式2: 直接运行示例

```bash
cd /home/mamingchang/multi-agent-dev-system

# 查看已有的象棋游戏
cd users/user_test/projects/chess_game/workspace
python3 main.py
```

## 详细使用步骤

### 1. 准备环境

确保系统已配置：
```bash
cd /home/mamingchang/multi-agent-dev-system

# 检查LLM配置
python3 scripts/test_llm_config.py

# 应该看到：
# ✓ 配置加载
# ✓ LLM客户端创建
# ✓ Agent创建
# ✓ LLM调用
```

### 2. 创建项目

#### 使用交互式脚本（推荐）

```bash
python3 scripts/create_project_interactive.py
```

按提示输入：
- 用户ID（默认user_test）
- 项目名称（英文，如：calculator）
- 项目描述（中文）
- 开发需求（详细描述你想要的功能）

#### 手动创建项目

```python
from src.project_manager import ProjectManager

# 创建项目管理器
proj_mgr = ProjectManager(user_id='your_user_id')

# 创建新项目
project = proj_mgr.create_project(
    project_name='my_app',
    description='我的应用描述',
    agents=['requester', 'product_manager', 'architect', 'developer']
)

print(f"项目创建成功: {project.project_id}")
print(f"工作空间: {proj_mgr.get_project_workspace('my_app')}")
```

### 3. 描述需求

**好的需求描述示例：**

```
开发一个简单的计算器程序

功能需求：
1. 支持加减乘除四则运算
2. 支持小括号优先级
3. 命令行界面
4. 支持连续计算

技术要求：
- Python 3.10+
- 代码清晰易懂
- 包含错误处理
```

**不好的需求描述：**
```
做个计算器
```

**提示：**
- 描述要具体明确
- 列出核心功能
- 说明技术要求
- 提供使用场景

### 4. 等待Agent工作

系统会自动执行以下流程：

```
[1/4] Requester (需求分析师)
  → 分析需求，识别核心功能
  → 评估可行性
  → 提供建议

[2/4] Product Manager (产品经理)
  → 规划功能模块
  → 定义优先级
  → 制定里程碑

[3/4] Architect (架构师)
  → 设计系统架构
  → 定义模块和类
  → 选择技术栈

[4/4] Developer (开发工程师)
  → 编写代码
  → 生成文件
  → 写入工作空间
```

**预计时间：** 2-5分钟（取决于项目复杂度）

### 5. 查看结果

项目完成后，代码会生成在：
```
users/{user_id}/projects/{project_name}/workspace/
```

**查看生成的文件：**
```bash
cd users/user_test/projects/my_app/workspace
ls -lh
```

**运行代码：**
```bash
python3 main.py
```

## 项目结构

```
users/{user_id}/projects/{project_name}/
├── project.yaml          # 项目配置
├── workspace/            # 代码工作空间
│   ├── main.py          # 主程序
│   ├── module1.py       # 模块1
│   ├── module2.py       # 模块2
│   └── README.md        # 项目文档
├── artifacts/            # 产物目录
│   ├── requirements/    # 需求文档
│   ├── designs/         # 设计文档
│   ├── code/            # 代码备份
│   ├── tests/           # 测试文件
│   ├── reviews/         # 审查记录
│   └── deployments/     # 部署文件
├── sessions/             # 会话记录
└── docs/                 # 项目文档
```

## 常见问题

### Q1: 如何查看我的所有项目？

```python
from src.project_manager import ProjectManager

proj_mgr = ProjectManager(user_id='user_test')
projects = proj_mgr.list_projects()

for proj in projects:
    print(f"- {proj.project_name}: {proj.description}")
```

或使用命令行：
```bash
ls -l users/user_test/projects/
```

### Q2: 如何修改生成的代码？

直接编辑工作空间中的文件：
```bash
cd users/user_test/projects/my_app/workspace
nano main.py  # 或使用你喜欢的编辑器
```

### Q3: 如果Agent执行失败怎么办？

**常见原因：**
1. **API超时** - 等待几分钟后重试
2. **网络问题** - 检查网络连接
3. **需求不清晰** - 提供更详细的需求描述

**解决方案：**
```bash
# 重新运行交互式脚本
python3 scripts/create_project_interactive.py

# 选择"使用现有项目"
# 输入更详细的需求
```

### Q4: 如何删除项目？

```python
from src.project_manager import ProjectManager

proj_mgr = ProjectManager(user_id='user_test')
proj_mgr.delete_project('project_name')
```

或手动删除：
```bash
rm -rf users/user_test/projects/project_name
```

### Q5: 生成的代码质量如何？

**当前版本：**
- ✅ 代码语法正确
- ✅ 结构清晰
- ✅ 包含基本注释
- ⚠️ 功能可能简化（演示版本）
- ⚠️ 需要人工审查和完善

**建议：**
1. 将生成的代码作为起点
2. 根据需要修改和完善
3. 添加更多功能和测试
4. 进行代码审查

### Q6: 可以开发什么类型的项目？

**适合的项目类型：**
- ✅ 命令行工具
- ✅ 简单的应用程序
- ✅ 数据处理脚本
- ✅ 小型游戏
- ✅ 实用工具

**不太适合的项目类型：**
- ❌ 大型复杂系统
- ❌ 需要图形界面的应用
- ❌ 需要外部依赖的项目
- ❌ 实时性要求高的系统

### Q7: 如何提高生成代码的质量？

**提供更详细的需求：**
```
好的需求示例：

开发一个文件管理器

功能需求：
1. 列出目录下的所有文件
2. 支持按名称、大小、时间排序
3. 支持搜索文件（支持通配符）
4. 支持复制、移动、删除文件
5. 显示文件详细信息（大小、修改时间、权限）

技术要求：
- Python 3.10+
- 使用pathlib处理路径
- 使用argparse处理命令行参数
- 包含错误处理和用户提示
- 代码要有详细注释

用户界面：
- 命令行界面
- 支持交互式操作
- 提供帮助信息

示例用法：
python3 file_manager.py list /path/to/dir
python3 file_manager.py search "*.txt"
python3 file_manager.py copy file1.txt /dest/
```

## 高级用法

### 自定义Agent配置

```python
from src.agents.generic_agent import GenericAgent

# 创建自定义Agent
custom_agent = GenericAgent(
    name='my_agent',
    config={
        'role': '我的角色',
        'system_prompt': '你是一个...',
        'llm': {
            'provider': 'claude',
            'model': 'claude-sonnet-4-5'
        },
        'tools': {
            'inherit_global': False,
            'whitelist': ['tool1', 'tool2']
        }
    }
)
```

### 手动执行工作流

```python
from src.workflow.task import Task
from src.agents.generic_agent import GenericAgent

# 创建任务
task = Task(
    task_id='my_task',
    title='我的任务',
    description='任务描述'
)

# 创建Agent
agent = GenericAgent(name='agent1', config={...})

# 执行任务
result = agent.process(task)
print(result)
```

## 示例项目

### 示例1: 待办事项管理

```bash
python3 scripts/create_project_interactive.py

# 输入：
项目名称: todo_app
项目描述: 待办事项管理工具

需求描述:
开发一个待办事项管理工具
支持添加、删除、标记完成任务
支持按优先级排序
使用命令行界面
数据保存到JSON文件
```

### 示例2: 简单计算器

```bash
python3 scripts/create_project_interactive.py

# 输入：
项目名称: calculator
项目描述: 简单计算器

需求描述:
开发一个命令行计算器
支持加减乘除四则运算
支持小括号
支持连续计算
包含错误处理
```

### 示例3: 文件搜索工具

```bash
python3 scripts/create_project_interactive.py

# 输入：
项目名称: file_search
项目描述: 文件搜索工具

需求描述:
开发一个文件搜索工具
支持按文件名搜索（支持通配符）
支持按文件大小过滤
支持按修改时间过滤
显示搜索结果的详细信息
使用命令行参数
```

## 获取帮助

**查看文档：**
```bash
cd /home/mamingchang/multi-agent-dev-system/docs
ls *.md
```

**重要文档：**
- `LLM_CONFIGURATION_GUIDE.md` - LLM配置指南
- `CHESS_GAME_DEVELOPMENT_REPORT.md` - 象棋游戏开发报告
- `FULL_SYSTEM_TEST_REPORT.md` - 系统测试报告

**测试脚本：**
```bash
# 测试LLM配置
python3 scripts/test_llm_config.py

# 测试Agent
python3 scripts/test_agent_with_llm.py

# 查看象棋游戏示例
cd users/user_test/projects/chess_game/workspace
python3 main.py
```

## 提示和技巧

1. **需求要具体** - 越详细越好
2. **分步骤描述** - 列出核心功能
3. **说明技术要求** - Python版本、依赖等
4. **提供示例** - 说明如何使用
5. **耐心等待** - Agent工作需要时间
6. **检查结果** - 生成后测试代码
7. **手动完善** - 根据需要修改代码

## 开始使用

```bash
cd /home/mamingchang/multi-agent-dev-system
python3 scripts/create_project_interactive.py
```

祝你使用愉快！🚀
