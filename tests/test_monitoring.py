"""
监控系统测试

测试场景：
1. 指标收集
2. 链路追踪
3. 告警触发
4. 趋势分析
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from src.monitoring.metrics_collector import MetricsCollector, Counter, Gauge, Histogram
from src.monitoring.tracer import Tracer, TracingContext, SpanKind
from src.monitoring.alerting import AlertManager, AlertRule, AlertLevel, TrendAnalyzer


def test_metrics_collection():
    """测试1: 指标收集"""
    print("\n=== 测试1: 指标收集 ===")

    collector = MetricsCollector()

    # 测试计数器
    counter = collector.get_counter("test_counter")
    counter.inc()
    counter.inc(5)
    assert counter.get() == 6
    print(f"✓ 计数器: {counter.get()}")

    # 测试仪表盘
    gauge = collector.get_gauge("test_gauge")
    gauge.set(100)
    gauge.inc(20)
    gauge.dec(10)
    assert gauge.get() == 110
    print(f"✓ 仪表盘: {gauge.get()}")

    # 测试直方图
    histogram = collector.get_histogram("test_histogram")
    for value in [1.0, 2.0, 3.0, 4.0, 5.0]:
        histogram.observe(value)

    stats = histogram.get_stats()
    assert stats["count"] == 5
    assert stats["avg"] == 3.0
    print(f"✓ 直方图: 平均值={stats['avg']}, P95={stats['p95']}")

    print("✓ 指标收集测试通过")


def test_system_metrics():
    """测试2: 系统指标"""
    print("\n=== 测试2: 系统指标 ===")

    collector = MetricsCollector()

    # 收集系统指标
    system_metrics = collector.collect_system_metrics()

    print(f"CPU使用率: {system_metrics['cpu_percent']}%")
    print(f"内存使用率: {system_metrics['memory_percent']}%")
    print(f"磁盘使用率: {system_metrics['disk_percent']}%")

    # 验证指标存在
    assert "cpu_percent" in system_metrics
    assert "memory_percent" in system_metrics
    assert "disk_percent" in system_metrics

    print("✓ 系统指标测试通过")


def test_tracing():
    """测试3: 链路追踪"""
    print("\n=== 测试3: 链路追踪 ===")

    tracer_instance = Tracer()

    # 开始追踪
    trace_id = tracer_instance.start_trace("test_operation")
    print(f"✓ 开始追踪: {trace_id}")

    # 创建子Span
    with TracingContext(tracer_instance, "sub_operation_1", SpanKind.INTERNAL) as span1:
        span1.set_tag("step", 1)
        span1.log("执行步骤1")
        time.sleep(0.1)

    with TracingContext(tracer_instance, "sub_operation_2", SpanKind.INTERNAL) as span2:
        span2.set_tag("step", 2)
        span2.log("执行步骤2")
        time.sleep(0.1)

    # 结束根Span
    root_span = tracer_instance.get_trace(trace_id)[0]
    tracer_instance.finish_span(root_span)

    # 获取追踪
    spans = tracer_instance.get_trace(trace_id)
    assert len(spans) == 3  # 1个根Span + 2个子Span
    print(f"✓ 追踪包含 {len(spans)} 个Span")

    # 获取摘要
    summary = tracer_instance.get_trace_summary(trace_id)
    assert summary is not None
    print(f"✓ 追踪摘要: 总耗时={summary['total_duration']:.3f}s")

    print("✓ 链路追踪测试通过")


def test_alerting():
    """测试4: 告警系统"""
    print("\n=== 测试4: 告警系统 ===")

    alert_mgr = AlertManager()

    # 添加自定义规则
    alert_mgr.add_rule(AlertRule(
        name="test_high_value",
        metric_name="test_metric",
        condition=lambda x: x > 100,
        level=AlertLevel.WARNING,
        description="测试指标超过100"
    ))

    # 测试正常值（不触发告警）
    alerts = alert_mgr.check_metrics({"test_metric": 50})
    assert len(alerts) == 0
    print("✓ 正常值不触发告警")

    # 测试异常值（触发告警）
    alerts = alert_mgr.check_metrics({"test_metric": 150})
    assert len(alerts) == 1
    assert alerts[0].level == AlertLevel.WARNING
    print(f"✓ 异常值触发告警: {alerts[0].message}")

    # 获取活跃告警
    active_alerts = alert_mgr.get_active_alerts()
    assert len(active_alerts) == 1
    print(f"✓ 活跃告警数: {len(active_alerts)}")

    # 解决告警
    alert_mgr.resolve_alert("test_high_value")
    active_alerts = alert_mgr.get_active_alerts()
    assert len(active_alerts) == 0
    print("✓ 告警已解决")

    print("✓ 告警系统测试通过")


def test_trend_analysis():
    """测试5: 趋势分析"""
    print("\n=== 测试5: 趋势分析 ===")

    analyzer = TrendAnalyzer(window_size=10)

    # 添加上升趋势数据
    for i in range(10):
        analyzer.add_data_point("metric_up", i * 10)

    trend = analyzer.get_trend("metric_up")
    assert trend == "up"
    print(f"✓ 上升趋势检测: {trend}")

    # 添加下降趋势数据
    for i in range(10):
        analyzer.add_data_point("metric_down", 100 - i * 10)

    trend = analyzer.get_trend("metric_down")
    assert trend == "down"
    print(f"✓ 下降趋势检测: {trend}")

    # 添加稳定数据
    for i in range(10):
        analyzer.add_data_point("metric_stable", 50 + (i % 2))

    trend = analyzer.get_trend("metric_stable")
    assert trend == "stable"
    print(f"✓ 稳定趋势检测: {trend}")

    print("✓ 趋势分析测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("监控系统测试")
    print("="*60)

    try:
        test_metrics_collection()
        test_system_metrics()
        test_tracing()
        test_alerting()
        test_trend_analysis()

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
