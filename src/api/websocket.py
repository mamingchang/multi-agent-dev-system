"""
WebSocket实时通知系统

功能：
1. 工作流执行进度推送
2. Agent状态变化通知
3. 对话消息实时推送
4. 产物生成通知
5. 错误和警告推送

设计：
- 使用FastAPI的WebSocket支持
- 连接管理器管理所有活跃连接
- 基于任务ID的订阅机制
- 支持广播和单播
- 自动心跳保持连接

为什么需要WebSocket：
- HTTP轮询效率低，延迟高
- 工作流执行时间长，用户需要实时反馈
- 多Agent协作过程复杂，需要可视化
"""

from typing import Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime
from enum import Enum


class NotificationType(Enum):
    """通知类型"""
    TASK_STARTED = "task_started"           # 任务开始
    TASK_COMPLETED = "task_completed"       # 任务完成
    TASK_FAILED = "task_failed"             # 任务失败
    AGENT_STARTED = "agent_started"         # Agent开始工作
    AGENT_COMPLETED = "agent_completed"     # Agent完成工作
    AGENT_FAILED = "agent_failed"           # Agent失败
    MESSAGE_SENT = "message_sent"           # 消息发送
    ARTIFACT_CREATED = "artifact_created"   # 产物创建
    ITERATION_UPDATE = "iteration_update"   # 迭代更新
    ERROR = "error"                         # 错误
    WARNING = "warning"                     # 警告
    HEARTBEAT = "heartbeat"                 # 心跳


class ConnectionManager:
    """
    WebSocket连接管理器

    职责：
    1. 管理所有活跃的WebSocket连接
    2. 支持按任务ID订阅
    3. 提供广播和单播功能
    4. 处理连接断开和清理
    """

    def __init__(self):
        # 所有活跃连接：{connection_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}

        # 任务订阅：{task_id: set(connection_ids)}
        self.task_subscriptions: Dict[str, Set[str]] = {}

        # 连接到任务的映射：{connection_id: set(task_ids)}
        self.connection_tasks: Dict[str, Set[str]] = {}

        # 心跳任务
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, connection_id: str):
        """
        接受新连接

        Args:
            websocket: WebSocket对象
            connection_id: 连接ID（通常是用户ID或会话ID）
        """
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.connection_tasks[connection_id] = set()

        # 启动心跳
        self.heartbeat_tasks[connection_id] = asyncio.create_task(
            self._heartbeat(connection_id)
        )

        print(f"[WebSocket] 连接建立: {connection_id}")

    def disconnect(self, connection_id: str):
        """
        断开连接

        Args:
            connection_id: 连接ID
        """
        # 取消心跳
        if connection_id in self.heartbeat_tasks:
            self.heartbeat_tasks[connection_id].cancel()
            del self.heartbeat_tasks[connection_id]

        # 清理订阅
        if connection_id in self.connection_tasks:
            for task_id in self.connection_tasks[connection_id]:
                if task_id in self.task_subscriptions:
                    self.task_subscriptions[task_id].discard(connection_id)
                    if not self.task_subscriptions[task_id]:
                        del self.task_subscriptions[task_id]
            del self.connection_tasks[connection_id]

        # 移除连接
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

        print(f"[WebSocket] 连接断开: {connection_id}")

    def subscribe_task(self, connection_id: str, task_id: str):
        """
        订阅任务通知

        Args:
            connection_id: 连接ID
            task_id: 任务ID
        """
        if task_id not in self.task_subscriptions:
            self.task_subscriptions[task_id] = set()

        self.task_subscriptions[task_id].add(connection_id)

        # 确保connection_tasks存在
        if connection_id not in self.connection_tasks:
            self.connection_tasks[connection_id] = set()

        self.connection_tasks[connection_id].add(task_id)

        print(f"[WebSocket] {connection_id} 订阅任务 {task_id}")

    def unsubscribe_task(self, connection_id: str, task_id: str):
        """
        取消订阅任务

        Args:
            connection_id: 连接ID
            task_id: 任务ID
        """
        if task_id in self.task_subscriptions:
            self.task_subscriptions[task_id].discard(connection_id)
            if not self.task_subscriptions[task_id]:
                del self.task_subscriptions[task_id]

        if connection_id in self.connection_tasks:
            self.connection_tasks[connection_id].discard(task_id)

        print(f"[WebSocket] {connection_id} 取消订阅任务 {task_id}")

    async def send_personal_message(self, message: Dict[str, Any], connection_id: str):
        """
        发送个人消息（单播）

        Args:
            message: 消息内容
            connection_id: 连接ID
        """
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_json(message)
            except Exception as e:
                print(f"[WebSocket] 发送消息失败: {connection_id}, {e}")
                self.disconnect(connection_id)

    async def broadcast_to_task(self, message: Dict[str, Any], task_id: str):
        """
        广播消息给订阅了特定任务的所有连接

        Args:
            message: 消息内容
            task_id: 任务ID
        """
        if task_id not in self.task_subscriptions:
            return

        # 复制集合避免迭代时修改
        subscribers = list(self.task_subscriptions[task_id])

        for connection_id in subscribers:
            await self.send_personal_message(message, connection_id)

    async def broadcast_all(self, message: Dict[str, Any]):
        """
        广播消息给所有连接

        Args:
            message: 消息内容
        """
        # 复制列表避免迭代时修改
        connections = list(self.active_connections.keys())

        for connection_id in connections:
            await self.send_personal_message(message, connection_id)

    async def _heartbeat(self, connection_id: str):
        """
        心跳保持连接

        Args:
            connection_id: 连接ID
        """
        try:
            while True:
                await asyncio.sleep(30)  # 每30秒发送一次心跳
                await self.send_personal_message(
                    {
                        "type": NotificationType.HEARTBEAT.value,
                        "timestamp": datetime.now().isoformat()
                    },
                    connection_id
                )
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[WebSocket] 心跳失败: {connection_id}, {e}")
            self.disconnect(connection_id)


# 全局连接管理器
manager = ConnectionManager()


def create_notification(
    notification_type: NotificationType,
    task_id: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    创建通知消息

    Args:
        notification_type: 通知类型
        task_id: 任务ID
        data: 数据内容

    Returns:
        Dict: 通知消息
    """
    return {
        "type": notification_type.value,
        "task_id": task_id,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }


async def notify_task_started(task_id: str, task_title: str):
    """通知任务开始"""
    await manager.broadcast_to_task(
        create_notification(
            NotificationType.TASK_STARTED,
            task_id,
            {"title": task_title}
        ),
        task_id
    )


async def notify_task_completed(task_id: str, success: bool, message: str = ""):
    """通知任务完成"""
    await manager.broadcast_to_task(
        create_notification(
            NotificationType.TASK_COMPLETED,
            task_id,
            {"success": success, "message": message}
        ),
        task_id
    )


async def notify_agent_started(task_id: str, agent_name: str, agent_role: str):
    """通知Agent开始工作"""
    await manager.broadcast_to_task(
        create_notification(
            NotificationType.AGENT_STARTED,
            task_id,
            {"agent_name": agent_name, "agent_role": agent_role}
        ),
        task_id
    )


async def notify_agent_completed(
    task_id: str,
    agent_name: str,
    success: bool,
    output: Optional[str] = None
):
    """通知Agent完成工作"""
    await manager.broadcast_to_task(
        create_notification(
            NotificationType.AGENT_COMPLETED,
            task_id,
            {
                "agent_name": agent_name,
                "success": success,
                "output": output
            }
        ),
        task_id
    )


async def notify_message_sent(
    task_id: str,
    from_agent: str,
    to_agent: str,
    message_type: str,
    content: Any
):
    """通知消息发送"""
    await manager.broadcast_to_task(
        create_notification(
            NotificationType.MESSAGE_SENT,
            task_id,
            {
                "from_agent": from_agent,
                "to_agent": to_agent,
                "message_type": message_type,
                "content": str(content)[:500]  # 限制长度
            }
        ),
        task_id
    )


async def notify_artifact_created(
    task_id: str,
    artifact_type: str,
    agent_name: str,
    version: int
):
    """通知产物创建"""
    await manager.broadcast_to_task(
        create_notification(
            NotificationType.ARTIFACT_CREATED,
            task_id,
            {
                "artifact_type": artifact_type,
                "agent_name": agent_name,
                "version": version
            }
        ),
        task_id
    )


async def notify_iteration_update(
    task_id: str,
    agent_name: str,
    iteration: int,
    max_iterations: int
):
    """通知迭代更新"""
    await manager.broadcast_to_task(
        create_notification(
            NotificationType.ITERATION_UPDATE,
            task_id,
            {
                "agent_name": agent_name,
                "iteration": iteration,
                "max_iterations": max_iterations
            }
        ),
        task_id
    )


async def notify_error(task_id: str, error_message: str, agent_name: Optional[str] = None):
    """通知错误"""
    await manager.broadcast_to_task(
        create_notification(
            NotificationType.ERROR,
            task_id,
            {
                "error_message": error_message,
                "agent_name": agent_name
            }
        ),
        task_id
    )


async def notify_warning(task_id: str, warning_message: str, agent_name: Optional[str] = None):
    """通知警告"""
    await manager.broadcast_to_task(
        create_notification(
            NotificationType.WARNING,
            task_id,
            {
                "warning_message": warning_message,
                "agent_name": agent_name
            }
        ),
        task_id
    )
