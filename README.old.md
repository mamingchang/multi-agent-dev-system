# Multi-Agent Development System

一个模拟真实软件开发流程的多Agent协作系统，包含需求提出、产品设计、架构设计、开发、代码审查、测试和部署等完整环节。

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    协调层 (Orchestrator)                 │
│              负责任务分发、流程控制、冲突仲裁              │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
    需求阶段             开发阶段             质量阶段
```

## Agent角色

1. **需求提出者 (Requester)**: 提出原始需求
2. **产品经理 (Product Manager)**: 将需求细化为PRD
3. **架构师 (Architect)**: 设计技术方案和系统架构
4. **开发者 (Developer)**: 实现代码
5. **代码审查员 (Code Reviewer)**: 审查代码质量
6. **测试员 (Tester)**: 执行功能测试
7. **DevOps工程师 (DevOps)**: 负责部署和运维

## 项目结构

```
multi-agent-dev-system/
├── README.md                    # 项目说明
├── requirements.txt             # Python依赖
├── config/
│   └── agents_config.yaml      # Agent配置
├── src/
│   ├── orchestrator.py         # 协调器
│   ├── agents/                 # Agent实现
│   │   ├── base_agent.py       # Agent基类
│   │   ├── requester.py
│   │   ├── product_manager.py
│   │   ├── architect.py
│   │   ├── developer.py
│   │   ├── code_reviewer.py
│   │   ├── tester.py
│   │   └── devops.py
│   ├── workflow/               # 工作流
│   │   └── task.py             # 任务定义
│   └── utils/                  # 工具类
│       ├── logger.py
│       └── message.py
├── examples/
│   └── demo.py                 # 使用示例
└── tests/
    └── test_workflow.py        # 测试用例
```

## 文件关系

- **orchestrator.py** → 调用所有agents，控制workflow
- **base_agent.py** → 被所有具体agent继承
- **task.py** → 在agents间传递的任务对象
- **message.py** → agents间通信的消息格式
- **agents_config.yaml** → 配置每个agent的行为参数

## 安装

```bash
cd multi-agent-dev-system
pip install -r requirements.txt
```

## 使用方法

### 基本使用

```python
from src.orchestrator import Orchestrator
from src.workflow.task import Task

# 创建协调器
orchestrator = Orchestrator()

# 创建任务
task = Task(
    task_id="TASK-001",
    title="开发用户管理系统",
    description="需要一个用户管理系统，支持用户注册、登录、权限管理等功能"
)

# 执行工作流
result = orchestrator.execute_workflow(task)
```

### 运行示例

```bash
cd multi-agent-dev-system
python examples/demo.py
```

## 工作流程

1. **需求阶段**: 需求提出者 → 产品经理（细化需求、编写PRD）
2. **设计阶段**: 产品经理 → 架构师（技术方案设计）→ 开发者（确认可行性）
3. **开发阶段**: 开发者编写代码
4. **审查阶段**: 代码审查员（代码质量）+ 测试员（功能测试）并行进行
5. **部署阶段**: DevOps工程师负责上线
6. **反馈循环**: 任何阶段发现问题都可以回退到相应环节

## 特性

- ✅ 完整的软件开发生命周期模拟
- ✅ Agent间的协作和质疑机制
- ✅ 自动化的反馈循环
- ✅ 任务状态追踪
- ✅ 产物管理
- ✅ 可配置的工作流

## 扩展

可以通过继承 `BaseAgent` 类来添加新的Agent角色：

```python
from src.agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def process(self, task):
        # 实现你的逻辑
        return {'success': True, 'message': '处理完成'}
```

## License

MIT
