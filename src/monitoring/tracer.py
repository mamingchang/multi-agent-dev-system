"""
链路追踪系统

实现分布式链路追踪，追踪请求在系统中的完整流程。

追踪范围：
- API请求 → 服务层 → Agent → LLM调用

每个请求生成唯一TraceID，贯穿整个执行流程。
"""

import uuid
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextvars import ContextVar
from enum import Enum


# 上下文变量，用于在异步环境中传递TraceID
current_trace_id: ContextVar[Optional[str]] = ContextVar('current_trace_id', default=None)
current_span_id: ContextVar[Optional[str]] = ContextVar('current_span_id', default=None)


class SpanKind(str, Enum):
    """Span类型"""
    SERVER = "server"  # 服务端处理
    CLIENT = "client"  # 客户端调用
    INTERNAL = "internal"  # 内部处理


class Span:
    """追踪Span"""

    def __init__(
        self,
        trace_id: str,
        span_id: str,
        parent_span_id: Optional[str],
        operation_name: str,
        kind: SpanKind = SpanKind.INTERNAL
    ):
        """
        初始化Span

        Args:
            trace_id: 追踪ID
            span_id: Span ID
            parent_span_id: 父Span ID
            operation_name: 操作名称
            kind: Span类型
        """
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.operation_name = operation_name
        self.kind = kind

        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.duration: Optional[float] = None

        self.tags: Dict[str, Any] = {}
        self.logs: List[Dict[str, Any]] = []
        self.error: Optional[str] = None

    def set_tag(self, key: str, value: Any):
        """设置标签"""
        self.tags[key] = value

    def log(self, message: str, level: str = "info"):
        """记录日志"""
        self.logs.append({
            "timestamp": time.time(),
            "level": level,
            "message": message
        })

    def set_error(self, error: str):
        """设置错误"""
        self.error = error
        self.tags["error"] = True

    def finish(self):
        """结束Span"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "operation_name": self.operation_name,
            "kind": self.kind.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "tags": self.tags,
            "logs": self.logs,
            "error": self.error
        }


class Tracer:
    """追踪器"""

    def __init__(self):
        """初始化追踪器"""
        self.spans: Dict[str, List[Span]] = {}  # trace_id -> spans

    def start_trace(self, operation_name: str) -> str:
        """
        开始新的追踪

        Args:
            operation_name: 操作名称

        Returns:
            str: TraceID
        """
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())

        # 设置上下文
        current_trace_id.set(trace_id)
        current_span_id.set(span_id)

        # 创建根Span
        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=None,
            operation_name=operation_name,
            kind=SpanKind.SERVER
        )

        if trace_id not in self.spans:
            self.spans[trace_id] = []
        self.spans[trace_id].append(span)

        return trace_id

    def start_span(
        self,
        operation_name: str,
        kind: SpanKind = SpanKind.INTERNAL
    ) -> Span:
        """
        开始新的Span

        Args:
            operation_name: 操作名称
            kind: Span类型

        Returns:
            Span: 新创建的Span
        """
        trace_id = current_trace_id.get()
        parent_span_id = current_span_id.get()

        if not trace_id:
            # 如果没有当前追踪，创建新的
            trace_id = self.start_trace(operation_name)
            parent_span_id = None

        span_id = str(uuid.uuid4())

        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            kind=kind
        )

        # 更新上下文
        current_span_id.set(span_id)

        if trace_id not in self.spans:
            self.spans[trace_id] = []
        self.spans[trace_id].append(span)

        return span

    def finish_span(self, span: Span):
        """
        结束Span

        Args:
            span: 要结束的Span
        """
        span.finish()

        # 恢复父Span的上下文
        if span.parent_span_id:
            current_span_id.set(span.parent_span_id)

    def get_trace(self, trace_id: str) -> List[Span]:
        """
        获取追踪的所有Span

        Args:
            trace_id: 追踪ID

        Returns:
            List[Span]: Span列表
        """
        return self.spans.get(trace_id, [])

    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """
        获取追踪摘要

        Args:
            trace_id: 追踪ID

        Returns:
            dict: 追踪摘要
        """
        spans = self.get_trace(trace_id)

        if not spans:
            return None

        # 找到根Span
        root_span = next((s for s in spans if s.parent_span_id is None), None)

        if not root_span or not root_span.duration:
            return None

        # 统计信息
        total_duration = root_span.duration
        span_count = len(spans)
        error_count = sum(1 for s in spans if s.error)

        return {
            "trace_id": trace_id,
            "operation_name": root_span.operation_name,
            "total_duration": total_duration,
            "span_count": span_count,
            "error_count": error_count,
            "has_error": error_count > 0,
            "start_time": root_span.start_time,
            "end_time": root_span.end_time
        }


class TracingContext:
    """追踪上下文管理器"""

    def __init__(self, tracer: Tracer, operation_name: str, kind: SpanKind = SpanKind.INTERNAL):
        """
        初始化上下文管理器

        Args:
            tracer: 追踪器
            operation_name: 操作名称
            kind: Span类型
        """
        self.tracer = tracer
        self.operation_name = operation_name
        self.kind = kind
        self.span: Optional[Span] = None

    def __enter__(self) -> Span:
        """进入上下文"""
        self.span = self.tracer.start_span(self.operation_name, self.kind)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if exc_type is not None:
            # 发生异常
            self.span.set_error(str(exc_val))

        self.tracer.finish_span(self.span)


# 全局追踪器实例
tracer = Tracer()


def trace_operation(operation_name: str, kind: SpanKind = SpanKind.INTERNAL):
    """
    追踪操作装饰器

    Args:
        operation_name: 操作名称
        kind: Span类型

    Returns:
        装饰器函数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with TracingContext(tracer, operation_name, kind) as span:
                # 记录函数参数
                span.set_tag("function", func.__name__)

                try:
                    result = func(*args, **kwargs)
                    span.set_tag("success", True)
                    return result
                except Exception as e:
                    span.set_error(str(e))
                    span.set_tag("success", False)
                    raise

        return wrapper
    return decorator
