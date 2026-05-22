# 已注册的Agent总览

## 完整开发流程的7个Agent

### 1. Requester（需求分析师）
- **角色**: `requester`
- **描述**: 需求分析师，负责需求收集和澄清
- **温度**: 0.7（需要创造性理解用户需求）
- **协作**: product_manager
- **黑名单**: execute_code, deploy
- **配置文件**: `config/agents/requester.yaml`

### 2. Product Manager（产品经理）
- **角色**: `product_manager`
- **描述**: 产品经理，负责需求分析和产品设计
- **温度**: 0.7（需要创造性设计产品）
- **协作**: architect, developer, tester
- **黑名单**: execute_code, deploy
- **配置文件**: `config/agents/product_manager.yaml`

### 3. Architect（架构师）
- **角色**: `architect`
- **描述**: 架构师，负责系统架构设计和技术选型
- **温度**: 0.5（平衡创造性和精确性）
- **协作**: product_manager, developer, devops
- **黑名单**: deploy
- **配置文件**: `config/agents/architect.yaml`

### 4. Developer（开发工程师）
- **角色**: `developer`
- **描述**: 开发工程师，负责代码实现和单元测试
- **温度**: 0.3（需要精确的代码实现）
- **协作**: product_manager, architect, code_reviewer, tester
- **黑名单**: 无（需要完整工具集）
- **配置文件**: `config/agents/developer.yaml`

### 5. Code Reviewer（代码审查工程师）
- **角色**: `code_reviewer`
- **描述**: 代码审查工程师，负责代码质量检查
- **温度**: 0.2（需要严谨的审查）
- **协作**: developer, architect
- **黑名单**: deploy
- **配置文件**: `config/agents/code_reviewer.yaml`

### 6. Tester（测试工程师）
- **角色**: `tester`
- **描述**: 测试工程师，负责测试用例设计和执行
- **温度**: 0.4（平衡测试设计的创造性）
- **协作**: product_manager, developer, code_reviewer
- **黑名单**: deploy
- **配置文件**: `config/agents/tester.yaml`

### 7. DevOps（运维工程师）
- **角色**: `devops`
- **描述**: DevOps工程师，负责部署和运维
- **温度**: 0.3（需要精确的部署操作）
- **协作**: architect, developer, tester
- **黑名单**: 无（需要完整工具集）
- **配置文件**: `config/agents/devops.yaml`

## 工作流程

```
用户需求
   ↓
1. Requester（需求收集和澄清）
   ↓
2. Product Manager（需求分析和产品设计）
   ↓
3. Architect（系统架构设计和技术选型）
   ↓
4. Developer（代码实现和单元测试）
   ↓
5. Code Reviewer（代码质量检查）
   ↓
6. Tester（测试用例设计和执行）
   ↓
7. DevOps（部署和运维）
   ↓
交付产品
```

## 温度参数说明

温度参数控制LLM输出的创造性：
- **0.2-0.3**: 精确、确定性（代码实现、代码审查、部署）
- **0.4-0.5**: 平衡（测试设计、架构设计）
- **0.7**: 创造性（需求分析、产品设计）

## 数据隔离

每个Agent有独立的数据目录：
```
data/agents/
├── requester/
│   ├── memory/
│   ├── cache/
│   └── logs/
├── product_manager/
├── architect/
├── developer/
├── code_reviewer/
├── tester/
└── devops/
```

## CLI命令示例

```bash
# 列出所有Agent
./mas agent list

# 查看某个Agent的详细配置
./mas agent show developer

# 更新Agent配置
./mas agent update developer --set llm.temperature=0.4

# 从已有Agent复制创建新Agent
./mas agent register --method existing --name developer2 --source developer

# 注销Agent
./mas agent unregister developer2
```

## 下一步

1. **实现具体的工具和技能**：在 `src/tools/roles/` 和 `src/skills/roles/` 下实现各角色的专属能力
2. **集成到Orchestrator**：让Orchestrator使用这些注册的Agent执行工作流
3. **测试完整流程**：用真实案例测试7个Agent的协作
4. **优化配置**：根据实际使用情况调整各Agent的配置

## 配置文件位置

- **Agent配置**: `config/agents/*.yaml`
- **模板配置**: `config/templates/*.yaml`
- **备份配置**: `config/agents/backups/`

## 可用模板

- `requester.yaml`
- `product_manager.yaml`
- `architect.yaml`
- `developer.yaml`
- `code_reviewer.yaml`
- `tester.yaml`
- `devops.yaml`
