#!/bin/bash
# 文件管理结构可视化脚本

echo "=========================================="
echo "三层隔离文件管理结构"
echo "=========================================="
echo ""

cat << 'EOF'
┌─────────────────────────────────────────────────────────────────┐
│                        系统根目录                                 │
│                  multi-agent-dev-system/                         │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ users/  │          │ shared_ │          │ config/ │
   │         │          │ agents/ │          │         │
   └─────────┘          └─────────┘          └─────────┘
        │
        │ 用户层隔离
        │
        ├── user_alice/
        │   │
        │   ├── profile.yaml          # 用户配置
        │   ├── .current_project      # 当前项目指针
        │   │
        │   ├── agents/               # Agent层隔离
        │   │   │
        │   │   ├── my_custom_pm/
        │   │   │   ├── config.yaml
        │   │   │   ├── metadata.yaml
        │   │   │   ├── memory/       # Agent私有记忆
        │   │   │   └── cache/        # Agent私有缓存
        │   │   │
        │   │   └── my_developer/
        │   │       └── ...
        │   │
        │   └── projects/             # 项目层隔离
        │       │
        │       ├── todo-app/         # 项目1（完全隔离）
        │       │   │
        │       │   ├── project.yaml
        │       │   │
        │       │   ├── sessions/     # 会话记录
        │       │   │   ├── 2026-05-21_001.json
        │       │   │   └── 2026-05-22_002.json
        │       │   │
        │       │   ├── workspace/    # 代码工作空间
        │       │   │   ├── src/
        │       │   │   │   ├── app.py
        │       │   │   │   └── models.py
        │       │   │   ├── tests/
        │       │   │   └── README.md
        │       │   │
        │       │   ├── artifacts/    # Agent产物
        │       │   │   ├── requirements/
        │       │   │   ├── designs/
        │       │   │   ├── code/
        │       │   │   ├── tests/
        │       │   │   ├── reviews/
        │       │   │   └── deployments/
        │       │   │
        │       │   └── docs/         # 生成的文档
        │       │       ├── API.md
        │       │       └── ARCHITECTURE.md
        │       │
        │       └── blog-system/      # 项目2（完全隔离）
        │           ├── project.yaml
        │           ├── sessions/
        │           ├── workspace/
        │           ├── artifacts/
        │           └── docs/
        │
        └── user_bob/                 # 用户bob（完全隔离）
            ├── profile.yaml
            ├── agents/
            └── projects/

EOF

echo ""
echo "=========================================="
echo "文件访问流程"
echo "=========================================="
echo ""

cat << 'EOF'
1. 用户运行工作流
   └─> ./mas workflow run --project todo-app --title "添加功能"

2. 系统加载项目上下文
   └─> ProjectManager.get_project("todo-app")
       └─> 返回: users/user_alice/projects/todo-app/

3. Agent获得项目工作空间
   └─> workspace_path = "users/user_alice/projects/todo-app/workspace/"
       artifacts_path = "users/user_alice/projects/todo-app/artifacts/"

4. Agent只能访问该项目的文件
   ├─> 读取: workspace/src/app.py
   ├─> 写入: workspace/src/new_feature.py
   └─> 保存产物: artifacts/code/iteration_1/

5. 会话保存到项目目录
   └─> sessions/2026-05-21_003_add_feature.json

EOF

echo ""
echo "=========================================="
echo "隔离保证"
echo "=========================================="
echo ""

cat << 'EOF'
✅ 用户隔离
   user_alice/ 和 user_bob/ 完全独立
   无法互相访问

✅ 项目隔离
   todo-app/ 和 blog-system/ 完全独立
   代码、会话、产物互不干扰

✅ Agent隔离
   每个Agent有独立的memory/和cache/
   Agent在项目中工作时只能访问该项目的workspace/

✅ 安全检查
   所有文件操作都会检查路径是否在允许范围内
   防止路径遍历攻击（../../../etc/passwd）

EOF

echo ""
echo "=========================================="
echo "文件管理命令"
echo "=========================================="
echo ""

cat << 'EOF'
# 查看项目详情（包含文件路径）
./mas project show todo-app

# 查看项目会话
./mas project sessions todo-app

# 查看项目文件（需要实现）
./mas project files todo-app

# 查看项目产物（需要实现）
./mas project artifacts todo-app --type requirements

# 直接访问文件
ls users/user_alice/projects/todo-app/workspace/
cat users/user_alice/projects/todo-app/artifacts/requirements/v1.md

EOF

echo ""
echo "详细文档: docs/FILE_MANAGEMENT.md"
echo ""
