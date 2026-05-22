---
name: testing_feedback
description: 测试必须使用真实数据库
type: feedback
importance: high
tags: testing, database
created_at: 2026-05-18T17:50:37.497164
---

集成测试必须使用真实数据库，不要使用mock

**Why:** 上次使用mock导致生产环境出现bug，mock和真实数据库行为不一致

**How to apply:** 在编写测试时，使用Docker启动测试数据库，不要mock数据库调用