"""
错误处理和容错机制测试

测试场景：
1. 重试机制测试
2. 熔断器状态转换测试
3. 熔断器触发条件测试
4. 熔断器恢复测试
5. 补偿机制测试
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from src.utils.retry import retry_on_failure, RetryContext
from src.utils.circuit_breaker import CircuitBreaker, CircuitState
from src.utils.compensation import CompensationContext, CompensationHandler
from src.exceptions import (
    AgentExecutionError, LLMAPIError, CircuitOpenException
)


def test_retry_mechanism():
    """测试1: 重试机制"""
    print("\n=== 测试1: 重试机制 ===")

    # 测试成功场景
    attempt_count = [0]

    @retry_on_failure(max_attempts=3, delay=0)
    def flaky_function():
        attempt_count[0] += 1
        if attempt_count[0] < 3:
            raise Exception("临时失败")
        return "成功"

    result = flaky_function()
    assert result == "成功"
    assert attempt_count[0] == 3
    print(f"✓ 重试机制测试通过: 尝试 {attempt_count[0]} 次后成功")

    # 测试失败场景
    attempt_count[0] = 0

    @retry_on_failure(max_attempts=3, delay=0)
    def always_fail():
        attempt_count[0] += 1
        raise Exception("永久失败")

    try:
        always_fail()
        assert False, "应该抛出异常"
    except Exception as e:
        assert str(e) == "永久失败"
        assert attempt_count[0] == 3
        print(f"✓ 重试失败测试通过: 尝试 {attempt_count[0]} 次后失败")


def test_circuit_breaker_states():
    """测试2: 熔断器状态转换"""
    print("\n=== 测试2: 熔断器状态转换 ===")

    breaker = CircuitBreaker(
        organization_id=1,
        failure_threshold=3,
        success_threshold=2,
        timeout=2,
        window_size=10
    )

    # 初始状态应该是CLOSED
    assert breaker.state == CircuitState.CLOSED
    print("✓ 初始状态: CLOSED")

    # 模拟3次失败，触发熔断
    for i in range(3):
        try:
            breaker.call(lambda: (_ for _ in ()).throw(Exception("失败")))
        except Exception:
            pass

    assert breaker.state == CircuitState.OPEN
    print("✓ 3次失败后状态: OPEN")

    # 熔断状态下应该拒绝请求
    try:
        breaker.call(lambda: "成功")
        assert False, "应该抛出CircuitOpenException"
    except CircuitOpenException:
        print("✓ 熔断状态拒绝请求")

    # 等待超时后进入半开状态
    time.sleep(2.1)

    # 第一次调用会检查并转换到半开状态，然后执行成功
    result = breaker.call(lambda: "成功")
    assert result == "成功"
    print(f"✓ 超时后第一次调用成功，当前状态: {breaker.state.value}")

    # 再次调用成功，应该关闭熔断器（需要2次成功）
    if breaker.state == CircuitState.HALF_OPEN:
        result = breaker.call(lambda: "成功")
        assert result == "成功"
        print("✓ 半开状态第二次成功")

    assert breaker.state == CircuitState.CLOSED
    print("✓ 半开状态连续成功后关闭熔断器")


def test_circuit_breaker_trigger():
    """测试3: 熔断器触发条件"""
    print("\n=== 测试3: 熔断器触发条件 ===")

    breaker = CircuitBreaker(
        organization_id=2,
        failure_threshold=5,
        window_size=10
    )

    # 模拟连续5次失败，触发熔断
    for i in range(5):
        try:
            breaker.call(lambda: (_ for _ in ()).throw(Exception("失败")))
        except Exception:
            pass

    # 应该触发熔断
    assert breaker.state == CircuitState.OPEN
    print("✓ 连续5次失败后触发熔断")


def test_circuit_breaker_recovery():
    """测试4: 熔断器恢复"""
    print("\n=== 测试4: 熔断器恢复 ===")

    breaker = CircuitBreaker(
        organization_id=3,
        failure_threshold=3,
        success_threshold=2,
        timeout=1
    )

    # 触发熔断
    for i in range(3):
        try:
            breaker.call(lambda: (_ for _ in ()).throw(Exception("失败")))
        except Exception:
            pass

    assert breaker.state == CircuitState.OPEN
    print("✓ 熔断器已打开")

    # 手动重置
    breaker.reset()
    assert breaker.state == CircuitState.CLOSED
    print("✓ 手动重置后熔断器关闭")


def test_compensation_context():
    """测试5: 补偿上下文"""
    print("\n=== 测试5: 补偿上下文 ===")

    context = CompensationContext(task_id="test-task-1")

    # 添加资源
    context.add_temp_file("/tmp/test1.txt")
    context.add_temp_file("/tmp/test2.txt")
    context.add_temp_dir("/tmp/test_dir")
    context.add_redis_key("task:test-task-1")

    # 添加回滚操作
    rollback_executed = [False]

    def rollback_action():
        rollback_executed[0] = True

    context.add_rollback_action(rollback_action)

    # 获取摘要
    summary = context.get_summary()
    assert summary["temp_files_count"] == 2
    assert summary["temp_dirs_count"] == 1
    assert summary["redis_keys_count"] == 1
    assert summary["rollback_actions_count"] == 1

    print(f"✓ 补偿上下文创建成功: {summary}")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("错误处理和容错机制测试")
    print("="*60)

    try:
        test_retry_mechanism()
        test_circuit_breaker_states()
        test_circuit_breaker_trigger()
        test_circuit_breaker_recovery()
        test_compensation_context()

        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60)

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
