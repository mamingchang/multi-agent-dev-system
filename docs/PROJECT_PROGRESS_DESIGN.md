# 项目进度管理设计

## 核心需求

项目不仅是代码开发，还包括：
- 需求分析进度
- 设计进度
- 开发进度
- 测试进度
- 部署进度
- 文档进度

每个阶段都需要跟踪：
- 当前状态
- 完成度
- 负责Agent
- 产物
- 时间线

## 设计方案

### 1. 项目阶段（Phases）

```yaml
phases:
  - requirement_analysis:    # 需求分析
      status: completed
      progress: 100%
      agent: Requester
      artifacts:
        - requirements/requirement_doc.md
      start_time: "2026-05-20T10:00:00"
      end_time: "2026-05-20T11:00:00"
  
  - product_planning:        # 产品规划
      status: completed
      progress: 100%
      agent: Product Manager
      artifacts:
        - requirements/product_spec.md
        - requirements/user_stories.md
      start_time: "2026-05-20T11:00:00"
      end_time: "2026-05-20T12:00:00"
  
  - architecture_design:     # 架构设计
      status: in_progress
      progress: 60%
      agent: Architect
      artifacts:
        - designs/architecture.md
        - designs/api_design.md
      start_time: "2026-05-20T12:00:00"
      end_time: null
  
  - development:             # 开发
      status: pending
      progress: 0%
      agent: Developer
      artifacts: []
      start_time: null
      end_time: null
  
  - code_review:             # 代码审查
      status: pending
      progress: 0%
      agent: Code Reviewer
      artifacts: []
  
  - testing:                 # 测试
      status: pending
      progress: 0%
      agent: Tester
      artifacts: []
  
  - deployment:              # 部署
      status: pending
      progress: 0%
      agent: DevOps
      artifacts: []
```

### 2. 任务（Tasks）

每个阶段可以分解为多个任务：

```yaml
tasks:
  - id: task-001
    title: "设计用户认证模块"
    phase: architecture_design
    status: completed
    priority: high
    assigned_to: Architect
    progress: 100%
    created_at: "2026-05-20T12:00:00"
    completed_at: "2026-05-20T13:00:00"
    artifacts:
      - designs/auth_design.md
  
  - id: task-002
    title: "设计数据库Schema"
    phase: architecture_design
    status: in_progress
    priority: high
    assigned_to: Architect
    progress: 60%
    created_at: "2026-05-20T13:00:00"
    completed_at: null
    artifacts:
      - designs/database_schema.sql
  
  - id: task-003
    title: "实现用户注册功能"
    phase: development
    status: pending
    priority: high
    assigned_to: Developer
    progress: 0%
    dependencies: [task-001, task-002]
```

### 3. 里程碑（Milestones）

```yaml
milestones:
  - id: milestone-001
    title: "MVP版本"
    description: "最小可行产品"
    target_date: "2026-06-01"
    status: in_progress
    progress: 45%
    tasks: [task-001, task-002, task-003, ...]
  
  - id: milestone-002
    title: "Beta版本"
    description: "功能完整的测试版本"
    target_date: "2026-06-15"
    status: pending
    progress: 0%
```

### 4. 项目统计（Statistics）

```yaml
statistics:
  overall_progress: 35%
  
  phases_summary:
    completed: 2
    in_progress: 1
    pending: 4
    total: 7
  
  tasks_summary:
    completed: 5
    in_progress: 3
    pending: 12
    blocked: 1
    total: 21
  
  time_tracking:
    estimated_total_hours: 160
    actual_hours: 56
    remaining_hours: 104
  
  agent_workload:
    Requester: 
      completed_tasks: 2
      in_progress_tasks: 0
      hours_spent: 8
    Architect:
      completed_tasks: 1
      in_progress_tasks: 2
      hours_spent: 12
    Developer:
      completed_tasks: 0
      in_progress_tasks: 1
      hours_spent: 0
```

## 目录结构

```
users/user_alice/projects/todo-app/
  ├── project.yaml              # 项目基本信息
  ├── progress.yaml             # 进度跟踪（新增）✨
  │   ├── phases: [...]
  │   ├── tasks: [...]
  │   ├── milestones: [...]
  │   └── statistics: {...}
  ├── sessions/
  ├── workspace/
  ├── artifacts/
  │   ├── requirements/         # 需求产物
  │   ├── designs/              # 设计产物
  │   ├── code/                 # 代码产物
  │   ├── tests/                # 测试产物
  │   ├── reviews/              # 审查产物
  │   └── deployments/          # 部署产物
  ├── docs/
  └── agent_memories/
```

## CLI命令

### 查看项目进度

```bash
# 查看项目整体进度
./mas project progress todo-app

# 输出：
# ========================================
# 项目进度: todo-app
# ========================================
# 整体进度: 35%
# 
# 阶段进度:
#   ✅ 需求分析      100%  (Requester)
#   ✅ 产品规划      100%  (Product Manager)
#   🔄 架构设计       60%  (Architect)
#   ⏳ 开发           0%  (Developer)
#   ⏳ 代码审查       0%  (Code Reviewer)
#   ⏳ 测试           0%  (Tester)
#   ⏳ 部署           0%  (DevOps)
# 
# 任务统计:
#   已完成: 5
#   进行中: 3
#   待处理: 12
#   已阻塞: 1
#   总计: 21
# 
# 里程碑:
#   🎯 MVP版本 (45%) - 目标: 2026-06-01
#   ⏳ Beta版本 (0%) - 目标: 2026-06-15
```

### 查看阶段详情

```bash
# 查看特定阶段
./mas project phase todo-app architecture_design

# 输出：
# ========================================
# 阶段: 架构设计
# ========================================
# 状态: 进行中
# 进度: 60%
# 负责Agent: Architect
# 开始时间: 2026-05-20 12:00:00
# 
# 任务列表:
#   ✅ task-001: 设计用户认证模块 (100%)
#   🔄 task-002: 设计数据库Schema (60%)
#   ⏳ task-003: 设计API接口 (0%)
# 
# 产物:
#   - designs/architecture.md
#   - designs/auth_design.md
#   - designs/database_schema.sql (进行中)
```

### 查看任务列表

```bash
# 查看所有任务
./mas project tasks todo-app

# 查看特定阶段的任务
./mas project tasks todo-app --phase development

# 查看特定状态的任务
./mas project tasks todo-app --status in_progress

# 查看特定Agent的任务
./mas project tasks todo-app --agent Developer
```

### 更新任务状态

```bash
# 标记任务为进行中
./mas project task-update todo-app task-002 --status in_progress

# 更新任务进度
./mas project task-update todo-app task-002 --progress 80

# 标记任务完成
./mas project task-update todo-app task-002 --status completed --progress 100

# 添加产物
./mas project task-update todo-app task-002 --add-artifact designs/database_schema.sql
```

### 创建任务

```bash
# 创建新任务
./mas project task-create todo-app \
  --title "实现用户注册API" \
  --phase development \
  --priority high \
  --agent Developer \
  --depends-on task-001,task-002
```

### 查看里程碑

```bash
# 查看所有里程碑
./mas project milestones todo-app

# 查看特定里程碑
./mas project milestone todo-app milestone-001
```

### 生成进度报告

```bash
# 生成Markdown格式的进度报告
./mas project report todo-app --format markdown > progress_report.md

# 生成JSON格式
./mas project report todo-app --format json > progress_report.json

# 生成HTML格式
./mas project report todo-app --format html > progress_report.html
```

## 自动进度跟踪

### 工作流集成

当Agent完成工作时，自动更新进度：

```python
class CollaborativeOrchestrator:
    def execute(self, task):
        # 开始阶段
        self.progress_tracker.start_phase('architecture_design', 'Architect')
        
        # Agent工作
        result = architect.process(task)
        
        # 更新进度
        if result['success']:
            self.progress_tracker.update_phase_progress('architecture_design', 30)
            self.progress_tracker.add_artifact('architecture_design', 
                                              'designs/architecture.md')
        
        # 完成阶段
        if all_tasks_completed:
            self.progress_tracker.complete_phase('architecture_design')
            self.progress_tracker.start_phase('development', 'Developer')
```

### 产物自动关联

当Agent生成产物时，自动关联到任务：

```python
class BaseAgent:
    def write_file(self, relative_path, content):
        result = super().write_file(relative_path, content)
        
        if result['success']:
            # 自动关联产物到当前任务
            if self.current_task_id:
                self.progress_tracker.add_artifact(
                    self.current_task_id,
                    relative_path
                )
        
        return result
```

## 进度可视化

### 甘特图

```bash
# 生成甘特图
./mas project gantt todo-app --output gantt.png
```

生成类似这样的图表：

```
需求分析    ████████████ 100%
产品规划      ████████████ 100%
架构设计        ██████░░░░ 60%
开发              ░░░░░░░░░░ 0%
代码审查            ░░░░░░░░░░ 0%
测试                  ░░░░░░░░░░ 0%
部署                    ░░░░░░░░░░ 0%
           |----|----|----|----|
          5/20 5/25 5/30 6/04 6/09
```

### 燃尽图

```bash
# 生成燃尽图
./mas project burndown todo-app --output burndown.png
```

显示剩余任务数随时间的变化。

### 进度仪表盘

```bash
# 启动Web仪表盘
./mas project dashboard todo-app --port 8080
```

在浏览器中查看实时进度。

## 实现清单

### Phase 1: 基础数据结构

- [ ] `src/progress_tracker.py` - 进度跟踪核心类
- [ ] `src/project_manager.py` - 添加进度管理方法
- [ ] `progress.yaml` - 进度数据结构

### Phase 2: CLI命令

- [ ] `cli/progress_commands.py` - 进度管理命令
  - [ ] `project progress` - 查看整体进度
  - [ ] `project phase` - 查看阶段详情
  - [ ] `project tasks` - 查看任务列表
  - [ ] `project task-create` - 创建任务
  - [ ] `project task-update` - 更新任务
  - [ ] `project milestones` - 查看里程碑
  - [ ] `project report` - 生成报告

### Phase 3: 自动跟踪

- [ ] 工作流集成 - 自动更新阶段进度
- [ ] 产物关联 - 自动关联产物到任务
- [ ] 时间跟踪 - 自动记录时间

### Phase 4: 可视化

- [ ] 甘特图生成
- [ ] 燃尽图生成
- [ ] Web仪表盘

## 数据模型

### ProgressTracker类

```python
class ProgressTracker:
    def __init__(self, project_name: str, user_id: str):
        self.project_name = project_name
        self.user_id = user_id
        self.progress_file = self._get_progress_file()
        self.data = self._load_progress()
    
    def start_phase(self, phase_name: str, agent_name: str):
        """开始一个阶段"""
        pass
    
    def update_phase_progress(self, phase_name: str, progress: int):
        """更新阶段进度"""
        pass
    
    def complete_phase(self, phase_name: str):
        """完成一个阶段"""
        pass
    
    def create_task(self, task: Task):
        """创建任务"""
        pass
    
    def update_task(self, task_id: str, updates: Dict):
        """更新任务"""
        pass
    
    def add_artifact(self, task_id: str, artifact_path: str):
        """添加产物"""
        pass
    
    def get_overall_progress(self) -> int:
        """获取整体进度"""
        pass
    
    def get_phase_progress(self, phase_name: str) -> Dict:
        """获取阶段进度"""
        pass
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        pass
    
    def generate_report(self, format: str = 'markdown') -> str:
        """生成进度报告"""
        pass
```

### Task类

```python
@dataclass
class Task:
    id: str
    title: str
    phase: str
    status: str  # pending, in_progress, completed, blocked
    priority: str  # low, medium, high, critical
    assigned_to: str  # Agent名称
    progress: int  # 0-100
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    dependencies: List[str]  # 依赖的任务ID
    artifacts: List[str]  # 产物路径
    description: str
    notes: List[str]
```

### Phase类

```python
@dataclass
class Phase:
    name: str
    display_name: str
    status: str  # pending, in_progress, completed
    progress: int  # 0-100
    agent: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    artifacts: List[str]
    tasks: List[str]  # 任务ID列表
```

## 使用示例

### 示例1：查看项目进度

```bash
$ ./mas project progress todo-app

========================================
项目进度: todo-app
========================================
整体进度: 35%

阶段进度:
  ✅ 需求分析      100%  (Requester)      [2h]
  ✅ 产品规划      100%  (Product Manager) [3h]
  🔄 架构设计       60%  (Architect)       [7h / 12h预计]
  ⏳ 开发           0%  (Developer)       [0h / 80h预计]
  ⏳ 代码审查       0%  (Code Reviewer)   [0h / 10h预计]
  ⏳ 测试           0%  (Tester)          [0h / 20h预计]
  ⏳ 部署           0%  (DevOps)          [0h / 5h预计]

任务统计:
  已完成: 5 (24%)
  进行中: 3 (14%)
  待处理: 12 (57%)
  已阻塞: 1 (5%)
  总计: 21

时间统计:
  已用时间: 12小时
  预计总时间: 132小时
  剩余时间: 120小时

里程碑:
  🎯 MVP版本 (45%) - 目标: 2026-06-01 (还有12天)
  ⏳ Beta版本 (0%) - 目标: 2026-06-15 (还有26天)

最近活动:
  [2026-05-20 14:30] Architect 完成了 task-001: 设计用户认证模块
  [2026-05-20 14:35] Architect 开始了 task-002: 设计数据库Schema
  [2026-05-20 15:00] task-002 进度更新: 60%
```

### 示例2：创建和跟踪任务

```bash
# 创建任务
$ ./mas project task-create todo-app \
  --title "实现用户注册API" \
  --phase development \
  --priority high \
  --agent Developer \
  --estimate 8h \
  --depends-on task-001,task-002

✓ 任务创建成功: task-003

# 开始任务
$ ./mas project task-update todo-app task-003 --status in_progress

✓ 任务状态已更新: in_progress

# 更新进度
$ ./mas project task-update todo-app task-003 --progress 50

✓ 任务进度已更新: 50%

# 完成任务
$ ./mas project task-update todo-app task-003 --status completed --progress 100

✓ 任务已完成: task-003
✓ 开发阶段进度: 25% → 30%
```

## 优势

1. **全面跟踪**：从需求到部署的全流程跟踪
2. **自动化**：Agent工作自动更新进度
3. **可视化**：多种图表展示进度
4. **灵活性**：支持自定义阶段和任务
5. **统计分析**：详细的时间和工作量统计

---

**设计完成时间**：2026-05-20
