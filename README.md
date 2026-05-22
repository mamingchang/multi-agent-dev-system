# Multi-Agent Dev System

AI驱动的自动化软件开发协作平台 - 让7个专业Agent协作完成从需求到部署的全流程开发。

## ✨ 核心特性

### 🏗️ 三层隔离架构
- **用户层**：每个用户独立命名空间，完全隔离
- **Agent层**：Agent属于用户，配置完全可定制
- **项目层**：项目完全隔离，独立的workspace和记忆

### 🤖 7个专业Agent
- **Requester** - 需求分析师：澄清需求，评估可行性
- **Product Manager** - 产品经理：规划功能，定义优先级
- **Architect** - 架构师：设计系统架构，技术选型
- **Developer** - 开发工程师：编写代码，实现功能
- **Code Reviewer** - 代码审查员：审查代码质量
- **Tester** - 测试工程师：编写测试，保证质量
- **DevOps** - 运维工程师：部署上线，监控运维

### 🔧 Agent完全可配置
- **工具（Tools）**：白名单/黑名单过滤
- **技能（Skills）**：自定义技能集
- **插件（Plugins）**：扩展Agent能力
- **MCP服务器**：连接外部服务

### 🔒 文件安全隔离
- Agent只能访问项目workspace
- 路径遍历攻击防护
- 详细的错误信息

### 💾 智能记忆系统
- 记忆保存在项目下，不跟随Agent
- 同一个Agent在不同项目中有独立记忆
- 支持短期/长期/工作记忆

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 创建用户

```bash
./mas user init --username alice --email alice@example.com
```

### 3. 注册Agent

```bash
# 从模板注册产品经理Agent
./mas agent register --method template --name pm --template product_manager

# 注册开发Agent（自定义配置）
./mas agent register --method template --name dev --template developer \
  --override tools.whitelist=file_operations,code_analysis
```

### 4. 创建项目

```bash
./mas project create --name todo-app --description "Todo应用开发项目"
```

### 5. 运行工作流（需要LLM API）

```bash
# 配置API密钥
export CLAUDE_API_KEY=your_key

# 运行工作流
./mas workflow run --title "开发用户认证功能"
```

## 📖 文档

- **[快速入门](docs/QUICK_START.md)** - 5分钟上手指南
- **[完整总结](docs/FINAL_SUMMARY.md)** - 系统完整介绍
- **[架构设计](docs/ISOLATION_ARCHITECTURE.md)** - 三层隔离架构
- **[记忆管理](docs/AGENT_MEMORY_DESIGN.md)** - Agent记忆和ID管理

## 📊 系统状态

- ✅ **完成度**：100%
- ✅ **用户层**：完全实现
- ✅ **Agent层**：完全实现
- ✅ **项目层**：完全实现
- ✅ **文件安全**：完全实现
- ✅ **记忆管理**：完全实现

---

**开始使用**：`./mas user init --username your_name`

**详细文档**：[docs/QUICK_START.md](docs/QUICK_START.md)
