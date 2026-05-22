# 项目导入/导出设计

## 核心需求

### 导入场景

1. **从Git仓库导入**
   - 克隆现有代码仓库
   - 自动分析项目结构
   - 生成初始进度

2. **从本地目录导入**
   - 导入本地项目代码
   - 保留原有文件结构

3. **从项目包导入**
   - 导入其他用户导出的项目包
   - 包含代码、配置、进度

4. **从模板导入**
   - 使用项目模板快速开始
   - 预设目录结构和配置

### 导出场景

1. **导出为项目包**
   - 打包整个项目（代码、配置、进度、记忆）
   - 可以分享给其他用户

2. **导出到Git仓库**
   - 推送代码到远程仓库
   - 保留项目配置

3. **导出进度报告**
   - 生成进度报告文档
   - 支持多种格式

## 设计方案

### 1. 项目导入

#### 从Git仓库导入

```bash
# 从GitHub导入
./mas project import --from-git https://github.com/user/repo.git --name my-project

# 指定分支
./mas project import --from-git https://github.com/user/repo.git \
  --branch develop --name my-project

# 私有仓库（需要认证）
./mas project import --from-git git@github.com:user/private-repo.git \
  --name my-project
```

**流程**：
1. 克隆仓库到临时目录
2. 分析项目结构（语言、框架、依赖）
3. 创建项目配置
4. 复制代码到项目workspace
5. 生成初始进度（根据文件分析）
6. 清理临时文件

#### 从本地目录导入

```bash
# 导入本地项目
./mas project import --from-dir /path/to/project --name my-project

# 排除某些文件
./mas project import --from-dir /path/to/project --name my-project \
  --exclude "node_modules,*.log,.git"
```

**流程**：
1. 扫描本地目录
2. 分析项目结构
3. 复制文件到项目workspace
4. 生成项目配置
5. 生成初始进度

#### 从项目包导入

```bash
# 导入项目包（.mas格式）
./mas project import --from-package project-backup.mas --name restored-project

# 只导入代码，不导入进度
./mas project import --from-package project-backup.mas --name restored-project \
  --code-only
```

**项目包格式（.mas）**：
```
project-backup.mas (ZIP格式)
  ├── manifest.json          # 项目元信息
  ├── project.yaml           # 项目配置
  ├── progress.yaml          # 进度数据
  ├── workspace/             # 代码
  ├── artifacts/             # 产物
  ├── docs/                  # 文档
  └── agent_memories/        # Agent记忆（可选）
```

#### 从模板导入

```bash
# 列出可用模板
./mas project templates

# 从模板创建项目
./mas project import --from-template web-app --name my-web-app

# 自定义模板参数
./mas project import --from-template web-app --name my-web-app \
  --param framework=react \
  --param language=typescript
```

**可用模板**：
- `web-app` - Web应用（React/Vue/Angular）
- `api-service` - API服务（REST/GraphQL）
- `mobile-app` - 移动应用（React Native/Flutter）
- `cli-tool` - 命令行工具
- `library` - 库/SDK
- `microservice` - 微服务

### 2. 项目导出

#### 导出为项目包

```bash
# 导出完整项目
./mas project export todo-app --output todo-app-backup.mas

# 只导出代码
./mas project export todo-app --output todo-app-code.mas --code-only

# 排除记忆
./mas project export todo-app --output todo-app.mas --no-memories

# 压缩级别
./mas project export todo-app --output todo-app.mas --compress-level 9
```

**包含内容**：
- ✅ 项目配置（project.yaml）
- ✅ 进度数据（progress.yaml）
- ✅ 代码（workspace/）
- ✅ 产物（artifacts/）
- ✅ 文档（docs/）
- ✅ Agent记忆（agent_memories/，可选）
- ✅ 会话记录（sessions/，可选）

#### 导出到Git仓库

```bash
# 初始化Git仓库并推送
./mas project export-git todo-app --remote https://github.com/user/todo-app.git

# 只推送代码，不推送配置
./mas project export-git todo-app --remote https://github.com/user/todo-app.git \
  --code-only

# 指定分支
./mas project export-git todo-app --remote https://github.com/user/todo-app.git \
  --branch main
```

**流程**：
1. 在workspace中初始化Git（如果未初始化）
2. 添加.gitignore（排除配置文件）
3. 提交所有更改
4. 添加远程仓库
5. 推送到远程

#### 导出进度报告

```bash
# 导出Markdown报告
./mas project export-report todo-app --format markdown --output report.md

# 导出HTML报告
./mas project export-report todo-app --format html --output report.html

# 导出JSON数据
./mas project export-report todo-app --format json --output report.json

# 导出PDF报告（需要额外依赖）
./mas project export-report todo-app --format pdf --output report.pdf
```

### 3. 项目分析

导入时自动分析项目：

```python
class ProjectAnalyzer:
    def analyze(self, project_path: str) -> Dict:
        """分析项目结构"""
        return {
            'language': self._detect_language(),
            'framework': self._detect_framework(),
            'dependencies': self._detect_dependencies(),
            'structure': self._analyze_structure(),
            'estimated_progress': self._estimate_progress()
        }
    
    def _detect_language(self) -> str:
        """检测编程语言"""
        # 根据文件扩展名统计
        pass
    
    def _detect_framework(self) -> str:
        """检测框架"""
        # 检查package.json, requirements.txt等
        pass
    
    def _detect_dependencies(self) -> List[str]:
        """检测依赖"""
        pass
    
    def _analyze_structure(self) -> Dict:
        """分析目录结构"""
        pass
    
    def _estimate_progress(self) -> Dict:
        """估算初始进度"""
        # 根据文件数量、代码行数等估算
        pass
```

### 4. 进度初始化

导入项目后自动生成初始进度：

```python
class ProgressInitializer:
    def initialize(self, project_analysis: Dict) -> Dict:
        """根据项目分析生成初始进度"""
        
        # 检测已完成的阶段
        completed_phases = []
        
        # 如果有代码，说明开发已开始
        if project_analysis['has_code']:
            completed_phases.extend([
                'requirement_analysis',
                'product_planning',
                'architecture_design'
            ])
        
        # 如果有测试，说明测试已开始
        if project_analysis['has_tests']:
            completed_phases.append('development')
        
        # 如果有部署配置，说明部署已配置
        if project_analysis['has_deployment_config']:
            completed_phases.extend(['testing', 'code_review'])
        
        # 生成进度数据
        return {
            'phases': self._generate_phases(completed_phases),
            'tasks': self._generate_tasks(project_analysis),
            'statistics': self._calculate_statistics()
        }
```

## CLI命令完整列表

### 导入命令

```bash
# 从Git导入
./mas project import --from-git <url> --name <name> [--branch <branch>]

# 从本地目录导入
./mas project import --from-dir <path> --name <name> [--exclude <patterns>]

# 从项目包导入
./mas project import --from-package <file> --name <name> [--code-only]

# 从模板导入
./mas project import --from-template <template> --name <name> [--param key=value]

# 列出可用模板
./mas project templates
```

### 导出命令

```bash
# 导出为项目包
./mas project export <name> --output <file> [--code-only] [--no-memories]

# 导出到Git
./mas project export-git <name> --remote <url> [--branch <branch>] [--code-only]

# 导出进度报告
./mas project export-report <name> --format <format> --output <file>
```

### 进度管理命令

```bash
# 查看项目进度
./mas project progress <name>

# 查看阶段详情
./mas project phase <name> <phase>

# 查看任务列表
./mas project tasks <name> [--phase <phase>] [--status <status>] [--agent <agent>]

# 创建任务
./mas project task-create <name> --title <title> --phase <phase> [options]

# 更新任务
./mas project task-update <name> <task-id> [--status <status>] [--progress <n>]

# 查看里程碑
./mas project milestones <name>

# 生成甘特图
./mas project gantt <name> --output <file>

# 生成燃尽图
./mas project burndown <name> --output <file>

# 启动Web仪表盘
./mas project dashboard <name> [--port <port>]
```

## 目录结构

```
users/user_alice/projects/todo-app/
  ├── project.yaml              # 项目配置
  │   ├── name: todo-app
  │   ├── description: ...
  │   ├── language: python
  │   ├── framework: flask
  │   ├── created_at: ...
  │   ├── imported_from: git
  │   └── import_source: https://github.com/...
  │
  ├── progress.yaml             # 进度跟踪
  │   ├── phases: [...]
  │   ├── tasks: [...]
  │   ├── milestones: [...]
  │   └── statistics: {...}
  │
  ├── sessions/                 # 会话记录
  ├── workspace/                # 代码工作空间
  ├── artifacts/                # 产物
  ├── docs/                     # 文档
  └── agent_memories/           # Agent记忆
```

## 实现清单

### Phase 1: 项目导入（优先）

- [ ] `src/project_importer.py` - 项目导入核心类
  - [ ] `import_from_git()` - 从Git导入
  - [ ] `import_from_dir()` - 从本地目录导入
  - [ ] `import_from_package()` - 从项目包导入
  - [ ] `import_from_template()` - 从模板导入

- [ ] `src/project_analyzer.py` - 项目分析器
  - [ ] `detect_language()` - 检测语言
  - [ ] `detect_framework()` - 检测框架
  - [ ] `analyze_structure()` - 分析结构
  - [ ] `estimate_progress()` - 估算进度

- [ ] `cli/import_commands.py` - 导入命令
  - [ ] `project import` - 导入项目
  - [ ] `project templates` - 列出模板

### Phase 2: 项目导出

- [ ] `src/project_exporter.py` - 项目导出核心类
  - [ ] `export_to_package()` - 导出为项目包
  - [ ] `export_to_git()` - 导出到Git
  - [ ] `export_report()` - 导出报告

- [ ] `cli/export_commands.py` - 导出命令
  - [ ] `project export` - 导出项目包
  - [ ] `project export-git` - 导出到Git
  - [ ] `project export-report` - 导出报告

### Phase 3: 进度管理

- [ ] `src/progress_tracker.py` - 进度跟踪核心类
  - [ ] `start_phase()` - 开始阶段
  - [ ] `update_phase_progress()` - 更新阶段进度
  - [ ] `complete_phase()` - 完成阶段
  - [ ] `create_task()` - 创建任务
  - [ ] `update_task()` - 更新任务
  - [ ] `get_statistics()` - 获取统计

- [ ] `src/progress_initializer.py` - 进度初始化器
  - [ ] `initialize()` - 初始化进度
  - [ ] `generate_phases()` - 生成阶段
  - [ ] `generate_tasks()` - 生成任务

- [ ] `cli/progress_commands.py` - 进度管理命令
  - [ ] `project progress` - 查看进度
  - [ ] `project phase` - 查看阶段
  - [ ] `project tasks` - 查看任务
  - [ ] `project task-create` - 创建任务
  - [ ] `project task-update` - 更新任务
  - [ ] `project milestones` - 查看里程碑

### Phase 4: 可视化

- [ ] `src/progress_visualizer.py` - 进度可视化
  - [ ] `generate_gantt()` - 生成甘特图
  - [ ] `generate_burndown()` - 生成燃尽图
  - [ ] `generate_dashboard()` - 生成仪表盘

## 使用示例

### 示例1：从GitHub导入项目

```bash
# 导入开源项目
$ ./mas project import --from-git https://github.com/user/todo-app.git \
  --name todo-app

正在克隆仓库...
✓ 仓库克隆成功

正在分析项目...
✓ 检测到语言: Python
✓ 检测到框架: Flask
✓ 检测到依赖: 15个

正在创建项目...
✓ 项目创建成功: todo-app
✓ 代码已复制到workspace

正在生成初始进度...
✓ 检测到已完成阶段: 需求分析, 产品规划, 架构设计, 开发
✓ 估算整体进度: 65%
✓ 生成任务: 12个

项目导入完成！
  项目名称: todo-app
  工作空间: users/user_alice/projects/todo-app/workspace/
  整体进度: 65%
  
查看进度: ./mas project progress todo-app
```

### 示例2：从本地目录导入

```bash
# 导入本地项目
$ ./mas project import --from-dir ~/my-projects/blog-system \
  --name blog-system \
  --exclude "node_modules,*.log,.git"

正在扫描目录...
✓ 找到 156 个文件

正在分析项目...
✓ 检测到语言: JavaScript (TypeScript)
✓ 检测到框架: Next.js
✓ 检测到依赖: 42个

正在复制文件...
✓ 已复制 156 个文件 (排除 3 个目录)

正在生成初始进度...
✓ 估算整体进度: 45%

项目导入完成！
```

### 示例3：从模板创建项目

```bash
# 列出可用模板
$ ./mas project templates

可用项目模板:
  1. web-app        - Web应用 (React/Vue/Angular)
  2. api-service    - API服务 (REST/GraphQL)
  3. mobile-app     - 移动应用 (React Native/Flutter)
  4. cli-tool       - 命令行工具
  5. library        - 库/SDK
  6. microservice   - 微服务

# 从模板创建
$ ./mas project import --from-template web-app --name my-web-app \
  --param framework=react \
  --param language=typescript

正在创建项目...
✓ 使用模板: web-app
✓ 框架: React
✓ 语言: TypeScript

正在生成项目结构...
✓ 创建目录结构
✓ 生成配置文件
✓ 初始化依赖

项目创建完成！
  项目名称: my-web-app
  模板: web-app (React + TypeScript)
  
下一步:
  1. 查看项目: ./mas project show my-web-app
  2. 开始开发: ./mas workflow run --title "开发首页"
```

### 示例4：导出项目

```bash
# 导出完整项目包
$ ./mas project export todo-app --output todo-app-backup.mas

正在打包项目...
✓ 收集项目配置
✓ 收集进度数据
✓ 打包代码 (156 个文件)
✓ 打包产物 (23 个文件)
✓ 打包文档 (8 个文件)
✓ 打包Agent记忆 (5 个目录)

正在压缩...
✓ 压缩完成 (12.5 MB → 3.2 MB)

项目导出完成！
  输出文件: todo-app-backup.mas
  文件大小: 3.2 MB
  包含内容:
    - 项目配置
    - 进度数据
    - 代码 (156 个文件)
    - 产物 (23 个文件)
    - 文档 (8 个文件)
    - Agent记忆 (5 个Agent)
```

### 示例5：查看和管理进度

```bash
# 查看项目进度
$ ./mas project progress todo-app

========================================
项目进度: todo-app
========================================
整体进度: 65%
导入来源: Git (https://github.com/user/todo-app.git)
导入时间: 2026-05-20 16:00:00

阶段进度:
  ✅ 需求分析      100%  (Requester)      [已完成]
  ✅ 产品规划      100%  (Product Manager) [已完成]
  ✅ 架构设计      100%  (Architect)       [已完成]
  ✅ 开发           80%  (Developer)       [进行中]
  ⏳ 代码审查       0%  (Code Reviewer)   [待开始]
  ⏳ 测试           0%  (Tester)          [待开始]
  ⏳ 部署           0%  (DevOps)          [待开始]

任务统计:
  已完成: 8 (67%)
  进行中: 2 (17%)
  待处理: 2 (16%)
  总计: 12

下一步建议:
  1. 完成开发阶段剩余任务
  2. 开始代码审查
  3. 准备测试环境

# 创建新任务
$ ./mas project task-create todo-app \
  --title "添加用户权限管理" \
  --phase development \
  --priority high \
  --agent Developer

✓ 任务创建成功: task-013
✓ 开发阶段进度: 80% → 73% (新增任务)
```

## 项目包格式（.mas）

### manifest.json

```json
{
  "version": "1.0",
  "project_name": "todo-app",
  "exported_by": "user_alice",
  "exported_at": "2026-05-20T16:30:00",
  "mas_version": "1.0.0",
  "contents": {
    "project_config": true,
    "progress_data": true,
    "workspace": true,
    "artifacts": true,
    "docs": true,
    "agent_memories": true,
    "sessions": false
  },
  "statistics": {
    "total_files": 187,
    "total_size": 12582912,
    "compressed_size": 3355443
  }
}
```

## 优势

1. **灵活导入**：支持Git、本地、项目包、模板多种方式
2. **智能分析**：自动检测语言、框架、依赖
3. **进度估算**：根据代码分析自动生成初始进度
4. **完整导出**：可以导出完整项目包，包含所有数据
5. **版本控制**：支持导出到Git仓库
6. **进度跟踪**：全流程进度管理
7. **可视化**：甘特图、燃尽图、仪表盘

---

**设计完成时间**：2026-05-20
