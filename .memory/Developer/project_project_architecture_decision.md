---
name: project_architecture_decision
description: 项目架构决策：使用单体架构
type: project
importance: critical
tags: architecture, decision
created_at: 2026-05-18T17:50:37.496721
---

团队决定使用单体架构而不是微服务

**Why:** 团队规模小，单体架构更简单，维护成本低

**Context:** 讨论了微服务的优缺点，考虑到当前团队只有3人

**How to apply:** 所有模块放在同一个代码库，使用模块化设计