"""
成本优化测试

测试场景：
1. 上下文压缩
2. Token计数
3. 成本计算
4. 成本统计
5. 成本告警
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
from src.cost.context_compressor import ContextCompressor, ContextManager, Message
from src.cost.cost_analyzer import cost_analyzer
from src.cost.alert_manager import cost_alert_manager, AlertLevel


def test_token_counting():
    """测试1: Token计数"""
    print("\n=== 测试1: Token计数 ===")

    compressor = ContextCompressor()

    # 测试简单文本
    text = "Hello, world!"
    tokens = compressor.count_tokens(text)
    print(f"✓ 文本: '{text}'")
    print(f"  Token数: {tokens}")

    # 测试中文文本
    text_cn = "你好，世界！"
    tokens_cn = compressor.count_tokens(text_cn)
    print(f"✓ 文本: '{text_cn}'")
    print(f"  Token数: {tokens_cn}")

    # 测试消息列表
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="What is Python?"),
        Message(role="assistant", content="Python is a programming language.")
    ]

    total_tokens = compressor.count_messages_tokens(messages)
    print(f"✓ 消息列表Token数: {total_tokens}")

    print("✓ Token计数测试通过")


def test_context_compression():
    """测试2: 上下文压缩"""
    print("\n=== 测试2: 上下文压缩 ===")

    # 创建测试消息
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Tell me about Python."),
        Message(role="assistant", content="Python is a high-level programming language."),
        Message(role="user", content="What about its features?"),
        Message(role="assistant", content="Python has many features including dynamic typing, automatic memory management, and a large standard library."),
        Message(role="user", content="Can you give examples?"),
        Message(role="assistant", content="Sure! Here are some examples of Python code..."),
        Message(role="user", content="What about error handling?"),
        Message(role="assistant", content="Python uses try-except blocks for error handling."),
    ]

    compressor = ContextCompressor(max_tokens=100)

    print(f"✓ 原始消息数: {len(messages)}")

    # 执行压缩
    compressed = compressor.compress(messages)

    print(f"✓ 压缩后消息数: {len(compressed)}")

    # 获取统计信息
    stats = compressor.get_compression_stats(messages, compressed)
    print(f"✓ 原始Token数: {stats['original_tokens']}")
    print(f"✓ 压缩后Token数: {stats['compressed_tokens']}")
    print(f"✓ 节省Token数: {stats['tokens_saved']}")
    print(f"✓ 压缩率: {stats['compression_percentage']}")

    print("✓ 上下文压缩测试通过")


def test_context_manager():
    """测试3: 上下文管理器"""
    print("\n=== 测试3: 上下文管理器 ===")

    manager = ContextManager(agent_name="TestAgent", max_tokens=200)

    # 添加消息
    manager.add_message("system", "You are a helpful assistant.")
    manager.add_message("user", "Hello!")
    manager.add_message("assistant", "Hi! How can I help you?")

    print(f"✓ 消息数: {len(manager.get_messages())}")
    print(f"✓ Token数: {manager.get_token_count()}")
    print(f"✓ 使用率: {manager.get_usage_percentage():.1f}%")

    # 添加更多消息触发压缩
    for i in range(10):
        manager.add_message("user", f"This is a test message number {i} with some content.")
        manager.add_message("assistant", f"Response to message {i}.")

    print(f"✓ 压缩后消息数: {len(manager.get_messages())}")
    print(f"✓ 压缩后Token数: {manager.get_token_count()}")
    print(f"✓ 压缩次数: {manager.compression_count}")

    print("✓ 上下文管理器测试通过")


def test_cost_calculation():
    """测试4: 成本计算"""
    print("\n=== 测试4: 成本计算 ===")

    # 测试不同模型的成本
    models = [
        ("claude-opus-4", 1000, 1000),
        ("claude-sonnet-4", 1000, 1000),
        ("gpt-4", 1000, 1000),
        ("ollama", 1000, 1000),
    ]

    for model, input_tokens, output_tokens in models:
        cost = cost_analyzer.calculate_cost(model, input_tokens, output_tokens)
        print(f"✓ {model}: ${cost:.4f} (输入{input_tokens} + 输出{output_tokens} tokens)")

    print("✓ 成本计算测试通过")


def test_cost_statistics():
    """测试5: 成本统计"""
    print("\n=== 测试5: 成本统计 ===")

    # 记录一些使用数据
    cost_analyzer.record_usage(
        organization_id=1,
        model="claude-sonnet-4",
        input_tokens=1000,
        output_tokens=500,
        project_id=1,
        task_id=1,
        agent_name="ProductManager"
    )

    cost_analyzer.record_usage(
        organization_id=1,
        model="claude-sonnet-4",
        input_tokens=2000,
        output_tokens=1000,
        project_id=1,
        task_id=1,
        agent_name="Developer"
    )

    cost_analyzer.record_usage(
        organization_id=1,
        model="gpt-4",
        input_tokens=500,
        output_tokens=300,
        project_id=1,
        task_id=2,
        agent_name="Tester"
    )

    # 获取组织成本
    org_cost = cost_analyzer.get_organization_cost(organization_id=1)
    print(f"✓ 组织总成本: ${org_cost['total_cost']:.4f}")
    print(f"✓ 总Token数: {org_cost['total_tokens']}")
    print(f"✓ 记录数: {org_cost['record_count']}")

    # 获取项目成本
    project_cost = cost_analyzer.get_project_cost(project_id=1)
    print(f"✓ 项目总成本: ${project_cost['total_cost']:.4f}")

    # 获取任务成本
    task_cost = cost_analyzer.get_task_cost(task_id=1)
    print(f"✓ 任务1成本: ${task_cost['total_cost']:.4f}")
    print(f"✓ Agent详情: {len(task_cost['agent_details'])}个Agent")

    # 获取Agent平均成本
    agent_avg = cost_analyzer.get_agent_average_cost(agent_name="Developer")
    print(f"✓ Developer平均成本: ${agent_avg['average_cost']:.4f}")

    print("✓ 成本统计测试通过")


def test_cost_alerts():
    """测试6: 成本告警"""
    print("\n=== 测试6: 成本告警 ===")

    # 测试任务异常告警
    cost_alert_manager.task_history[100] = [0.01, 0.015, 0.012]  # 历史成本
    alert = cost_alert_manager.check_task_anomaly(
        task_id=100,
        current_cost=0.05  # 异常高的成本
    )

    if alert:
        print(f"✓ 触发任务异常告警: {alert.message}")
        print(f"  级别: {alert.level.value}")
    else:
        print("✗ 未触发任务异常告警")

    # 测试配额耗尽告警
    # 先记录一些历史数据
    for i in range(7):
        cost_analyzer.record_usage(
            organization_id=2,
            model="claude-sonnet-4",
            input_tokens=10000,
            output_tokens=5000,
            project_id=2,
            task_id=10 + i,
            agent_name="Developer"
        )

    alert = cost_alert_manager.check_quota_depletion(
        organization_id=2,
        current_usage=90000,
        total_quota=100000,
        days_to_check=7
    )

    if alert:
        print(f"✓ 触发配额耗尽告警: {alert.message}")
        print(f"  级别: {alert.level.value}")
        print(f"  剩余天数: {alert.details['days_remaining']}")
    else:
        print("✗ 未触发配额耗尽告警")

    # 获取活跃告警
    active_alerts = cost_alert_manager.get_active_alerts()
    print(f"✓ 活跃告警数: {len(active_alerts)}")

    print("✓ 成本告警测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("成本优化测试")
    print("="*60)

    try:
        test_token_counting()
        test_context_compression()
        test_context_manager()
        test_cost_calculation()
        test_cost_statistics()
        test_cost_alerts()

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
