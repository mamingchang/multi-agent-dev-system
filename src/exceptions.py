"""
自定义异常类

定义系统中使用的各种异常类型，用于错误处理和容错机制。

异常层次结构：
- BaseSystemException: 所有自定义异常的基类
  - AgentException: Agent相关异常
    - AgentExecutionError: Agent执行失败
    - AgentTimeoutError: Agent执行超时
  - LLMException: LLM相关异常
    - LLMAPIError: LLM API调用失败
    - LLMTimeoutError: LLM调用超时
    - LLMRateLimitError: LLM速率限制
  - TaskException: 任务相关异常
    - TaskExecutionError: 任务执行失败
    - TaskCancelledException: 任务被取消
  - QuotaException: 配额相关异常
    - QuotaExceededException: 配额超限
    - QuotaInsufficientException: 配额不足
  - CircuitBreakerException: 熔断相关异常
    - CircuitOpenException: 熔断器打开
"""


class BaseSystemException(Exception):
    """
    系统异常基类

    所有自定义异常都应该继承此类。
    """

    def __init__(self, message: str, details: dict = None):
        """
        初始化异常

        Args:
            message: 错误消息
            details: 错误详情（可选）
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


# ==================== Agent异常 ====================

class AgentException(BaseSystemException):
    """Agent相关异常基类"""
    pass


class AgentExecutionError(AgentException):
    """
    Agent执行失败

    当Agent执行过程中发生错误时抛出。
    """

    def __init__(self, agent_name: str, message: str, details: dict = None):
        super().__init__(
            message=f"Agent '{agent_name}' execution failed: {message}",
            details=details
        )
        self.agent_name = agent_name


class AgentTimeoutError(AgentException):
    """
    Agent执行超时

    当Agent执行时间超过配置的超时时间时抛出。
    """

    def __init__(self, agent_name: str, timeout_seconds: int):
        super().__init__(
            message=f"Agent '{agent_name}' execution timeout after {timeout_seconds}s",
            details={"timeout_seconds": timeout_seconds}
        )
        self.agent_name = agent_name
        self.timeout_seconds = timeout_seconds


# ==================== LLM异常 ====================

class LLMException(BaseSystemException):
    """LLM相关异常基类"""
    pass


class LLMAPIError(LLMException):
    """
    LLM API调用失败

    当调用LLM API时发生错误（如网络错误、API错误等）。
    """

    def __init__(self, provider: str, message: str, status_code: int = None, details: dict = None):
        error_details = details or {}
        if status_code:
            error_details["status_code"] = status_code

        super().__init__(
            message=f"LLM API error ({provider}): {message}",
            details=error_details
        )
        self.provider = provider
        self.status_code = status_code


class LLMTimeoutError(LLMException):
    """
    LLM调用超时

    当LLM API调用超时时抛出。
    """

    def __init__(self, provider: str, timeout_seconds: int):
        super().__init__(
            message=f"LLM API timeout ({provider}) after {timeout_seconds}s",
            details={"timeout_seconds": timeout_seconds}
        )
        self.provider = provider
        self.timeout_seconds = timeout_seconds


class LLMRateLimitError(LLMException):
    """
    LLM速率限制

    当触发LLM API的速率限制时抛出。
    """

    def __init__(self, provider: str, retry_after: int = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            message=f"LLM API rate limit exceeded ({provider})",
            details=details
        )
        self.provider = provider
        self.retry_after = retry_after


# ==================== 任务异常 ====================

class TaskException(BaseSystemException):
    """任务相关异常基类"""
    pass


class TaskExecutionError(TaskException):
    """
    任务执行失败

    当任务执行过程中发生错误时抛出。
    """

    def __init__(self, task_id: str, message: str, details: dict = None):
        super().__init__(
            message=f"Task '{task_id}' execution failed: {message}",
            details=details
        )
        self.task_id = task_id


class TaskCancelledException(TaskException):
    """
    任务被取消

    当任务被用户或系统取消时抛出。
    """

    def __init__(self, task_id: str, reason: str = None):
        details = {}
        if reason:
            details["reason"] = reason

        super().__init__(
            message=f"Task '{task_id}' was cancelled",
            details=details
        )
        self.task_id = task_id
        self.reason = reason


# ==================== 配额异常 ====================

class QuotaException(BaseSystemException):
    """配额相关异常基类"""
    pass


class QuotaExceededException(QuotaException):
    """
    配额超限

    当组织的Token使用量超过配额时抛出。
    """

    def __init__(self, organization_id: int, used: int, quota: int):
        super().__init__(
            message=f"Organization {organization_id} quota exceeded: {used}/{quota} tokens",
            details={
                "organization_id": organization_id,
                "used": used,
                "quota": quota,
                "exceeded_by": used - quota
            }
        )
        self.organization_id = organization_id
        self.used = used
        self.quota = quota


class QuotaInsufficientException(QuotaException):
    """
    配额不足

    当组织的剩余配额不足以执行操作时抛出。
    """

    def __init__(self, organization_id: int, required: int, available: int):
        super().__init__(
            message=f"Organization {organization_id} insufficient quota: need {required}, available {available}",
            details={
                "organization_id": organization_id,
                "required": required,
                "available": available,
                "shortage": required - available
            }
        )
        self.organization_id = organization_id
        self.required = required
        self.available = available


# ==================== 熔断异常 ====================

class CircuitBreakerException(BaseSystemException):
    """熔断相关异常基类"""
    pass


class CircuitOpenException(CircuitBreakerException):
    """
    熔断器打开

    当组织的熔断器处于打开状态时抛出，拒绝新的任务执行。
    """

    def __init__(self, organization_id: int, reason: str, retry_after: int = None):
        details = {"organization_id": organization_id, "reason": reason}
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            message=f"Circuit breaker open for organization {organization_id}: {reason}",
            details=details
        )
        self.organization_id = organization_id
        self.reason = reason
        self.retry_after = retry_after
