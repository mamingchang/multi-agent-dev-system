# 项目代码统一管理方案

## 概述

所有项目的代码（无论是新建的还是导入的）都统一存储在一个规范的目录结构中，便于管理、备份和访问。

## 目录结构

```
/var/lib/multi-agent-dev/projects/
├── org_1/                          # 组织1的项目
│   ├── project_1/                  # 项目1的代码
│   │   ├── src/
│   │   ├── docs/
│   │   ├── tests/
│   │   └── README.md
│   ├── project_2/                  # 项目2的代码
│   │   └── ...
│   └── project_3/
│       └── ...
├── org_2/                          # 组织2的项目
│   ├── project_4/
│   └── project_5/
└── org_3/
    └── ...
```

## 设计原则

### 1. **组织隔离**
- 每个组织的项目存储在独立的目录下
- 目录命名：`org_{organization_id}`
- 便于按组织进行备份和管理

### 2. **项目唯一标识**
- 每个项目目录命名：`project_{project_id}`
- 使用数据库ID作为目录名，确保唯一性
- 避免项目名称冲突

### 3. **统一接口**
- 所有代码操作通过 `ProjectCodeManager` 统一管理
- 提供一致的API接口
- 自动处理路径安全检查

## 数据库字段

Project表新增字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `code_path` | VARCHAR(500) | 项目代码存储路径 |
| `repo_url` | VARCHAR(500) | Git仓库URL（导入项目） |
| `repo_branch` | VARCHAR(100) | Git分支（导入项目） |
| `project_type` | VARCHAR(50) | 项目类型：manual/imported |

## 项目类型

### 1. **手动创建项目** (manual)

**创建流程**：
1. 用户填写项目信息
2. 系统创建数据库记录
3. 自动创建代码目录：`/var/lib/multi-agent-dev/projects/org_{org_id}/project_{id}/`
4. 初始化基本结构：
   - `src/` - 源代码目录
   - `docs/` - 文档目录
   - `tests/` - 测试目录
   - `README.md` - 项目说明
5. 初始化Git仓库（可选）

**特点**：
- 从零开始的项目
- 可以通过Agent生成代码
- 支持版本控制

### 2. **导入项目** (imported)

**导入流程**：
1. 用户提供Git仓库URL
2. 系统创建数据库记录
3. 克隆代码到：`/var/lib/multi-agent-dev/projects/org_{org_id}/project_{id}/`
4. 记录Git信息（repo_url, repo_branch）
5. 支持后续拉取更新

**特点**：
- 从现有仓库导入
- 保留Git历史
- 可以拉取远程更新
- 可以进行代码分析

## ProjectCodeManager API

### 核心方法

```python
from src.project_code import ProjectCodeManager

code_manager = ProjectCodeManager()

# 1. 创建项目目录（手动创建）
code_path = code_manager.create_project_directory(
    organization_id=1,
    project_id=10,
    project_name="my-project"
)

# 2. 克隆Git仓库（导入项目）
result = code_manager.clone_repository(
    organization_id=1,
    project_id=11,
    repo_url="https://github.com/user/repo.git",
    branch="main",
    depth=1
)

# 3. 拉取更新
result = code_manager.pull_updates(
    organization_id=1,
    project_id=11
)

# 4. 获取项目路径
path = code_manager.get_project_path(
    organization_id=1,
    project_id=10
)

# 5. 列出文件
files = code_manager.list_files(
    organization_id=1,
    project_id=10,
    relative_path="src"
)

# 6. 读取文件
content = code_manager.read_file(
    organization_id=1,
    project_id=10,
    file_path="src/main.py"
)

# 7. 写入文件
code_manager.write_file(
    organization_id=1,
    project_id=10,
    file_path="src/new_file.py",
    content="print('Hello')"
)

# 8. 获取项目统计
stats = code_manager.get_project_stats(
    organization_id=1,
    project_id=10
)

# 9. 删除项目代码
code_manager.delete_project_code(
    organization_id=1,
    project_id=10
)
```

## 安全特性

### 1. **路径安全**
- 所有文件操作都会检查路径是否在项目目录内
- 防止路径遍历攻击（../ 等）
- 自动解析符号链接

### 2. **权限控制**
- 通过数据库项目成员关系验证权限
- 只有项目成员才能访问代码
- 支持不同角色的权限控制

### 3. **组织隔离**
- 不同组织的代码完全隔离
- 无法跨组织访问代码

## 使用场景

### 场景1：新建项目并生成代码

```python
# 1. 创建项目（自动创建代码目录）
project = create_project(name="my-app", org_id=1)

# 2. Agent生成代码
code_manager.write_file(
    organization_id=1,
    project_id=project.id,
    file_path="src/main.py",
    content=generated_code
)

# 3. 用户可以下载或查看代码
```

### 场景2：导入现有项目并分析

```python
# 1. 导入项目（自动克隆代码）
project = import_project(
    repo_url="https://github.com/user/repo.git",
    org_id=1
)

# 2. 分析代码
analysis = analyze_project(project.id)

# 3. 提取知识
knowledge = extract_knowledge(project.id)

# 4. 创建任务让Agent改进代码
task = create_task(project.id, "优化性能")
```

### 场景3：协作开发

```python
# 1. 多个成员访问同一项目代码
files = code_manager.list_files(org_id=1, project_id=10)

# 2. 成员A修改代码
code_manager.write_file(
    organization_id=1,
    project_id=10,
    file_path="src/feature.py",
    content=new_code
)

# 3. 成员B查看修改
content = code_manager.read_file(
    organization_id=1,
    project_id=10,
    file_path="src/feature.py"
)
```

## 备份和迁移

### 备份策略

```bash
# 备份整个组织的项目
tar -czf org_1_backup.tar.gz /var/lib/multi-agent-dev/projects/org_1/

# 备份单个项目
tar -czf project_10_backup.tar.gz /var/lib/multi-agent-dev/projects/org_1/project_10/
```

### 迁移到新服务器

```bash
# 1. 复制代码目录
rsync -avz /var/lib/multi-agent-dev/projects/ new-server:/var/lib/multi-agent-dev/projects/

# 2. 导出数据库
sqlite3 multi_agent_dev.db .dump > backup.sql

# 3. 在新服务器导入数据库
sqlite3 multi_agent_dev.db < backup.sql
```

## 优势总结

### 1. **统一管理**
- 所有项目代码在一个位置
- 便于备份和维护
- 清晰的目录结构

### 2. **安全可靠**
- 组织隔离
- 权限控制
- 路径安全检查

### 3. **功能完整**
- 支持手动创建和导入
- 支持Git操作
- 支持文件读写
- 支持代码分析

### 4. **易于扩展**
- 统一的API接口
- 可以添加更多功能
- 支持不同的存储后端（未来可以支持S3等）

## 未来扩展

### 1. **版本控制增强**
- 自动提交Agent生成的代码
- 支持分支管理
- 支持代码审查

### 2. **存储后端**
- 支持S3/OSS等对象存储
- 支持NFS等网络存储
- 支持分布式文件系统

### 3. **代码搜索**
- 全文搜索
- 语义搜索
- 跨项目搜索

### 4. **协作功能**
- 实时协作编辑
- 代码锁定
- 冲突解决
