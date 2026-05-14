"""
重试机制

提供重试装饰器和重试策略，用于处理临时性失败。

重试策略：
1. 固定重试：固定次数，立即重试
2. 指数退避：重试间隔指数增长
3. 条件重试：只对特定异常重试
"""

import time
import functools
from typing import Callable, Type, Tuple, Optional
from ..exceptions import BaseSystemException


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 0,
    backoff: float = 1,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    重试装饰器

    当函数执行失败时自动重试。

    Args:
        max_attempts: 最大尝试次数（包括首次执行）
        delay: 重试延迟（秒），0表示立即重试
        backoff: 退避系数，每次重试延迟乘以此系数
        exceptions: 需要重试的异常类型元组
        on_retry: 重试时的回调函数，接收(attempt, exception)参数

    Returns:
        装饰器函数

    Example:
        @retry_on_failure(max_attempts=3, delay=1, backoff=2)
        def call_api():
            # API调用代码
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    # 如果是最后一次尝试，直接抛出异常
                    if attempt == max_attempts:
                        break

                    # 调用重试回调
                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception as callback_error:
                            print(f"重试回调执行失败: {callback_error}")

                    # 延迟后重试
                    if current_delay > 0:
                        time.sleep(current_delay)
                        current_delay *= backoff

            # 所有重试都失败，抛出最后一个异常
            raise last_exception

        return wrapper

    return decorator


def retry_agent_execution(max_attempts: int = 3):
    """
    Agent执行重试装饰器

    专门用于Agent执行的重试，固定3次立即重试。

    Args:
        max_attempts: 最大尝试次数，默认3次

    Returns:
        装饰器函数

    Example:
        @retry_agent_execution()
        def execute_agent(agent, task):
            return agent.process(task)
    """
    from ..exceptions import AgentException

    def on_retry_callback(attempt: int, exception: Exception):
        """重试回调：记录重试信息"""
        print(f"Agent执行失败，第 {attempt} 次重试: {str(exception)}")

    return retry_on_failure(
        max_attempts=max_attempts,
        delay=0,  # 立即重试
        backoff=1,
        exceptions=(AgentException,),
        on_retry=on_retry_callback
    )


def retry_llm_call(max_attempts: int = 3, delay: float = 1, backoff: float = 2):
    """
    LLM调用重试装饰器

    专门用于LLM API调用的重试，支持指数退避。

    Args:
        max_attempts: 最大尝试次数，默认3次
        delay: 初始延迟（秒），默认1秒
        backoff: 退避系数，默认2（每次延迟翻倍）

    Returns:
        装饰器函数

    Example:
        @retry_llm_call(max_attempts=3, delay=1, backoff=2)
        def call_llm_api(prompt):
            return llm_client.generate(prompt)
    """
    from ..exceptions import LLMException, LLMRateLimitError

    def on_retry_callback(attempt: int, exception: Exception):
        """重试回调：记录重试信息"""
        if isinstance(exception, LLMRateLimitError):
            print(f"LLM速率限制，第 {attempt} 次重试，等待 {exception.retry_after}s")
        else:
            print(f"LLM调用失败，第 {attempt} 次重试: {str(exception)}")

    return retry_on_failure(
        max_attempts=max_attempts,
        delay=delay,
        backoff=backoff,
        exceptions=(LLMException,),
        on_retry=on_retry_callback
    )


class RetryContext:
    """
    重试上下文

    用于在重试过程中传递状态信息。
    """

    def __init__(self, max_attempts: int = 3):
        """
        初始化重试上下文

        Args:
            max_attempts: 最大尝试次数
        """
        self.max_attempts = max_attempts
        self.current_attempt = 0
        self.last_exception = None
        self.retry_history = []

    def record_attempt(self, success: bool, exception: Exception = None):
        """
        记录一次尝试

        Args:
            success: 是否成功
            exception: 异常对象（如果失败）
        """
        self.current_attempt += 1
        self.retry_history.append({
            "attempt": self.current_attempt,
            "success": success,
            "exception": str(exception) if exception else None
        })

        if not success:
            self.last_exception = exception

    def should_retry(self) -> bool:
        """
        判断是否应该继续重试

        Returns:
            bool: 是否应该重试
        """
        return self.current_attempt < self.max_attempts

    def get_summary(self) -> dict:
        """
        获取重试摘要

        Returns:
            dict: 重试摘要信息
        """
        return {
            "max_attempts": self.max_attempts,
            "total_attempts": self.current_attempt,
            "success": self.last_exception is None,
            "last_exception": str(self.last_exception) if self.last_exception else None,
            "history": self.retry_history
        }
