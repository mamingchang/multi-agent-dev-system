#!/bin/bash
# Agent配置管理演示

echo "=========================================="
echo "Agent配置管理演示"
echo "=========================================="
echo ""

echo "Agent的skill、tool、plugin、MCP都是可配置的"
echo ""

echo "1. 注册时配置"
echo "----------------------------------------"
cat << 'EOF'
# 从模板注册，使用默认配置
./mas agent register --method template --name my_pm --template product_manager

# 注册时覆盖配置
./mas agent register --method template --name my_dev --template developer \
  --override tools.whitelist=file_operations,code_analysis \
  --override skills.whitelist=code_generation

# 从文件注册（完全自定义配置）
cat > my_agent_config.yaml << 'YAML'
name: custom_agent
role: custom_role
description: 自定义Agent
llm:
  provider: claude
  model: claude-sonnet-4-5
tools:
  inherit_global: true
  whitelist:
    - file_operations
    - code_analysis
  blacklist:
    - dangerous_tool
  role_specific:
    - path: tools/roles/custom
skills:
  inherit_global: false
  whitelist:
    - code_generation
    - test_generation
  role_specific:
    - path: skills/roles/custom
plugins:
  enabled:
    - git_plugin
    - docker_plugin
mcp_servers:
  enabled:
    - filesystem
    - github
YAML

./mas agent register --method file --name custom_agent --file my_agent_config.yaml
EOF

echo ""
read -p "按Enter继续..."
echo ""

echo "2. 注册后修改配置"
echo "----------------------------------------"
cat << 'EOF'
# 查看当前配置
./mas agent show my_pm

# 更新工具配置
./mas agent update my_pm --set tools.whitelist=file_operations,code_analysis,git_operations

# 更新技能配置
./mas agent update my_pm --set skills.whitelist=code_generation,test_generation

# 添加插件
./mas agent update my_pm --set plugins.enabled=git_plugin,docker_plugin

# 启用MCP服务器
./mas agent update my_pm --set mcp_servers.enabled=filesystem,github,slack

# 更新LLM配置
./mas agent update my_pm --set llm.model=claude-opus-4-7

# 更新描述
./mas agent update my_pm --set description="增强版产品经理Agent"
EOF

echo ""
read -p "按Enter继续..."
echo ""

echo "3. Agent配置结构"
echo "----------------------------------------"
cat << 'EOF'
users/user_alice/agents/my_pm/
  ├── config.yaml          # Agent配置
  │   ├── name             # Agent名称
  │   ├── role             # 角色
  │   ├── description      # 描述
  │   ├── llm              # LLM配置
  │   │   ├── provider     # 提供商（claude/openai/ollama）
  │   │   ├── model        # 模型名称
  │   │   └── api_key      # API密钥（可选）
  │   ├── tools            # 工具配置
  │   │   ├── inherit_global    # 是否继承全局工具
  │   │   ├── whitelist         # 白名单（只加载这些）
  │   │   ├── blacklist         # 黑名单（排除这些）
  │   │   └── role_specific     # 角色专属工具路径
  │   ├── skills           # 技能配置
  │   │   ├── inherit_global
  │   │   ├── whitelist
  │   │   └── role_specific
  │   ├── plugins          # 插件配置
  │   │   └── enabled      # 启用的插件列表
  │   └── mcp_servers      # MCP服务器配置
  │       └── enabled      # 启用的MCP服务器
  │
  ├── metadata.yaml        # 元数据
  │   ├── owner            # 所有者
  │   ├── visibility       # 可见性
  │   └── usage_count      # 使用统计
  │
  ├── memory/              # Agent记忆
  ├── cache/               # Agent缓存
  └── workspace/           # Agent工作空间
EOF

echo ""
read -p "按Enter继续..."
echo ""

echo "4. 配置示例"
echo "----------------------------------------"
cat << 'EOF'
# 最小配置
name: simple_agent
role: developer
description: 简单的开发Agent
llm:
  provider: claude
  model: claude-sonnet-4-5

# 完整配置
name: advanced_agent
role: developer
description: 高级开发Agent，具有完整的工具和技能
llm:
  provider: claude
  model: claude-sonnet-4-5
  api_key: ${CLAUDE_API_KEY}
  base_url: https://api.anthropic.com
  temperature: 0.7
  max_tokens: 4096

tools:
  inherit_global: true          # 继承全局工具
  whitelist:                    # 只加载这些工具
    - file_operations
    - code_analysis
    - git_operations
  blacklist:                    # 排除这些工具
    - dangerous_tool
  role_specific:                # 角色专属工具
    - path: tools/roles/developer
      load_all: true

skills:
  inherit_global: false         # 不继承全局技能
  whitelist:                    # 只加载这些技能
    - code_generation
    - test_generation
    - refactoring
  role_specific:
    - path: skills/roles/developer

plugins:
  enabled:                      # 启用的插件
    - git_plugin
    - docker_plugin
    - kubernetes_plugin

mcp_servers:
  enabled:                      # 启用的MCP服务器
    - filesystem
    - github
    - slack
    - jira

data_paths:
  workspace: data/agents/{agent_name}/workspace
  memory: data/agents/{agent_name}/memory
  cache: data/agents/{agent_name}/cache
EOF

echo ""
read -p "按Enter继续..."
echo ""

echo "5. 配置优先级"
echo "----------------------------------------"
cat << 'EOF'
配置加载顺序（后面的覆盖前面的）：

1. 模板默认配置
   config/templates/developer.yaml

2. 注册时的overrides
   --override tools.whitelist=...

3. 注册后的更新
   ./mas agent update my_dev --set tools.whitelist=...

4. 运行时的环境变量
   CLAUDE_API_KEY=xxx ./mas workflow run
EOF

echo ""
read -p "按Enter继续..."
echo ""

echo "=========================================="
echo "演示完成"
echo "=========================================="
echo ""

echo "关键点："
echo "  ✅ Agent的所有配置都是可修改的"
echo "  ✅ 支持注册时配置和注册后修改"
echo "  ✅ 支持工具、技能、插件、MCP的灵活配置"
echo "  ✅ 支持白名单/黑名单过滤"
echo "  ✅ 支持角色专属工具和技能"
echo ""

echo "详细文档："
echo "  - Agent注册: docs/agent_cli_guide.md"
echo "  - 配置管理: docs/AGENT_CONFIGURATION.md"
echo ""
