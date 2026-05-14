"""
WebSocket路由

提供WebSocket端点供客户端连接和订阅任务通知。

端点：
- /ws/{connection_id} - WebSocket连接端点

消息协议：
客户端发送：
{
    "action": "subscribe" | "unsubscribe",
    "task_id": "task-xxx"
}

服务端推送：
{
    "type": "task_started" | "agent_started" | ...,
    "task_id": "task-xxx",
    "timestamp": "2026-05-09T10:00:00",
    "data": {...}
}
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import json

from .websocket import manager

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/{connection_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    connection_id: str
):
    """
    WebSocket连接端点

    客户端连接后可以：
    1. 订阅任务通知
    2. 取消订阅
    3. 接收实时推送

    Args:
        websocket: WebSocket对象
        connection_id: 连接ID（建议使用用户ID或会话ID）

    消息格式：
        客户端 -> 服务端：
        {
            "action": "subscribe",
            "task_id": "task-123"
        }

        服务端 -> 客户端：
        {
            "type": "task_started",
            "task_id": "task-123",
            "timestamp": "2026-05-09T10:00:00",
            "data": {"title": "实现登录功能"}
        }
    """
    # 建立连接
    await manager.connect(websocket, connection_id)

    try:
        # 发送欢迎消息
        await manager.send_personal_message(
            {
                "type": "connected",
                "connection_id": connection_id,
                "message": "WebSocket连接成功"
            },
            connection_id
        )

        # 持续接收消息
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                action = message.get("action")
                task_id = message.get("task_id")

                if not action or not task_id:
                    await manager.send_personal_message(
                        {
                            "type": "error",
                            "message": "缺少action或task_id参数"
                        },
                        connection_id
                    )
                    continue

                # 处理订阅
                if action == "subscribe":
                    manager.subscribe_task(connection_id, task_id)
                    await manager.send_personal_message(
                        {
                            "type": "subscribed",
                            "task_id": task_id,
                            "message": f"已订阅任务 {task_id}"
                        },
                        connection_id
                    )

                # 处理取消订阅
                elif action == "unsubscribe":
                    manager.unsubscribe_task(connection_id, task_id)
                    await manager.send_personal_message(
                        {
                            "type": "unsubscribed",
                            "task_id": task_id,
                            "message": f"已取消订阅任务 {task_id}"
                        },
                        connection_id
                    )

                else:
                    await manager.send_personal_message(
                        {
                            "type": "error",
                            "message": f"未知操作: {action}"
                        },
                        connection_id
                    )

            except json.JSONDecodeError:
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "message": "无效的JSON格式"
                    },
                    connection_id
                )

    except WebSocketDisconnect:
        # 客户端断开连接
        manager.disconnect(connection_id)

    except Exception as e:
        # 其他异常
        print(f"[WebSocket] 异常: {connection_id}, {e}")
        manager.disconnect(connection_id)


@router.websocket("/tasks/{task_id}")
async def task_websocket_endpoint(
    websocket: WebSocket,
    task_id: str,
    token: str = Query(...)
):
    """
    任务专用WebSocket端点

    用于实时推送Agent协作对话和任务状态更新。

    Args:
        websocket: WebSocket对象
        task_id: 任务ID
        token: JWT认证token

    服务端推送消息类型：
        - agent_message: Agent发送的消息
        - status_update: 任务状态更新
        - workflow_complete: 工作流完成
        - error: 错误信息

    客户端发送消息类型：
        - user_intervention: 用户介入消息
    """
    # TODO: 验证token和权限
    # 这里简化处理，实际应该验证JWT token

    connection_id = f"task-{task_id}-{id(websocket)}"

    # 建立连接
    await manager.connect(websocket, connection_id)

    # 订阅任务
    manager.subscribe_task(connection_id, task_id)

    try:
        # 发送连接成功消息
        await manager.send_personal_message(
            {
                "type": "connected",
                "task_id": task_id,
                "message": "已连接到任务实时通道"
            },
            connection_id
        )

        # 持续接收消息
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                msg_type = message.get("type")

                # 处理用户介入消息
                if msg_type == "user_intervention":
                    content = message.get("content", "")

                    # 广播用户消息给所有订阅此任务的连接
                    await manager.broadcast_to_task(
                        {
                            "type": "user_message",
                            "sender": "User",
                            "content": content,
                            "timestamp": json.dumps({"$date": None})  # 会被替换为实际时间
                        },
                        task_id
                    )

                    # TODO: 将用户消息传递给工作流引擎
                    # 这里需要实现一个机制让正在执行的工作流能接收用户输入

            except json.JSONDecodeError:
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "message": "无效的JSON格式"
                    },
                    connection_id
                )

    except WebSocketDisconnect:
        manager.unsubscribe_task(connection_id, task_id)
        manager.disconnect(connection_id)

    except Exception as e:
        print(f"[Task WebSocket] 异常: {task_id}, {e}")
        manager.unsubscribe_task(connection_id, task_id)
        manager.disconnect(connection_id)

