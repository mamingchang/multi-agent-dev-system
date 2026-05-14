# 测试策略文档

## 概述

本文档描述多Agent开发系统的完整测试策略。

## 测试类型

### 1. 单元测试
- 覆盖率目标: 90%
- 工具: pytest
- Mock LLM响应

### 2. 集成测试
- 全流程测试
- Agent协作测试
- 错误处理测试

### 3. 压力测试
- 工具: Locust
- 目标: 100+并发

## 运行测试

```bash
# 单元测试
./run_tests.sh unit

# 集成测试
./run_tests.sh integration

# 所有测试
./run_tests.sh all

# 压力测试
./run_tests.sh stress
```

## CI/CD

GitHub Actions自动运行所有测试，测试失败阻断发布。
