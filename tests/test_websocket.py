"""
测试WebSocket实时通知系统

验证内容：
1. WebSocket连接建立和断开
2. 任务订阅和取消订阅
3. 实时通知推送
4. 心跳机制
5. 工作流集成
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import json
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from src.api.main import app
from src.api.websocket import manager, NotificationType


def test_websocket_connection():
    """测试1：WebSocket连接"""
    print("\n" + "="*60)
    print("测试1：WebSocket连接建立和断开")
    print("="*60)

    client = TestClient(app)

    # 测试连接
    with client.websocket_connect("/ws/test-connection-1") as websocket:
        # 接收欢迎消息
        data = websocket.receive_json()
        print(f"✅ 收到欢迎消息: {data['type']}")
        assert data['type'] == 'connected'
        assert data['connection_id'] == 'test-connection-1'

    print("✅ 连接正常断开")
    print("✅ WebSocket连接测试通过")


def test_task_subscription():
    """测试2：任务订阅"""
    print("\n" + "="*60)
    print("测试2：任务订阅和取消订阅")
    print("="*60)

    client = TestClient(app)

    with client.websocket_connect("/ws/test-sub-1") as websocket:
        # 接收欢迎消息
        websocket.receive_json()

        # 订阅任务
        websocket.send_json({
            "action": "subscribe",
            "task_id": "task-001"
        })

        # 接收订阅确认
        data = websocket.receive_json()
        print(f"✅ 订阅确认: {data['type']}")
        assert data['type'] == 'subscribed'
        assert data['task_id'] == 'task-001'

        # 取消订阅
        websocket.send_json({
            "action": "unsubscribe",
            "task_id": "task-001"
        })

        # 接收取消订阅确认
        data = websocket.receive_json()
        print(f"✅ 取消订阅确认: {data['type']}")
        assert data['type'] == 'unsubscribed'
        assert data['task_id'] == 'task-001'

    print("✅ 任务订阅测试通过")


def test_notification_broadcast():
    """测试3：通知广播"""
    print("\n" + "="*60)
    print("测试3：通知广播到订阅者")
    print("="*60)

    client = TestClient(app)

    # 创建两个连接
    with client.websocket_connect("/ws/test-broadcast-1") as ws1, \
         client.websocket_connect("/ws/test-broadcast-2") as ws2:

        # 接收欢迎消息
        ws1.receive_json()
        ws2.receive_json()

        # 两个连接都订阅同一个任务
        ws1.send_json({"action": "subscribe", "task_id": "task-broadcast"})
        ws2.send_json({"action": "subscribe", "task_id": "task-broadcast"})

        # 接收订阅确认
        ws1.receive_json()
        ws2.receive_json()

        # 模拟发送通知
        async def send_notification():
            from src.api.websocket import notify_task_started
            await notify_task_started("task-broadcast", "测试任务")

        # 运行异步任务
        asyncio.run(send_notification())

        # 两个连接都应该收到通知
        data1 = ws1.receive_json()
        data2 = ws2.receive_json()

        print(f"✅ 连接1收到通知: {data1['type']}")
        print(f"✅ 连接2收到通知: {data2['type']}")

        assert data1['type'] == NotificationType.TASK_STARTED.value
        assert data2['type'] == NotificationType.TASK_STARTED.value
        assert data1['task_id'] == 'task-broadcast'
        assert data2['task_id'] == 'task-broadcast'

    print("✅ 通知广播测试通过")


def test_notification_types():
    """测试4：各种通知类型"""
    print("\n" + "="*60)
    print("测试4：各种通知类型")
    print("="*60)

    client = TestClient(app)

    with client.websocket_connect("/ws/test-types-1") as websocket:
        # 接收欢迎消息
        websocket.receive_json()

        # 订阅任务
        websocket.send_json({"action": "subscribe", "task_id": "task-types"})
        websocket.receive_json()  # 订阅确认

        # 测试各种通知类型
        async def send_notifications():
            from src.api.websocket import (
                notify_task_started,
                notify_agent_started,
                notify_agent_completed,
                notify_artifact_created,
                notify_iteration_update,
                notify_error,
                notify_warning
            )

            await notify_task_started("task-types", "测试任务")
            await notify_agent_started("task-types", "Developer", "开发工程师")
            await notify_agent_completed("task-types", "Developer", True, "代码完成")
            await notify_artifact_created("task-types", "code", "Developer", 1)
            await notify_iteration_update("task-types", "Developer", 1, 5)
            await notify_warning("task-types", "这是一个警告", "Developer")
            await notify_error("task-types", "这是一个错误", "Developer")

        asyncio.run(send_notifications())

        # 接收所有通知
        notifications = []
        for _ in range(7):
            data = websocket.receive_json()
            notifications.append(data)
            print(f"  收到通知: {data['type']}")

        # 验证通知类型
        types = [n['type'] for n in notifications]
        assert NotificationType.TASK_STARTED.value in types
        assert NotificationType.AGENT_STARTED.value in types
        assert NotificationType.AGENT_COMPLETED.value in types
        assert NotificationType.ARTIFACT_CREATED.value in types
        assert NotificationType.ITERATION_UPDATE.value in types
        assert NotificationType.WARNING.value in types
        assert NotificationType.ERROR.value in types

    print("✅ 通知类型测试通过")


def test_workflow_integration():
    """测试5：工作流集成"""
    print("\n" + "="*60)
    print("测试5：工作流集成测试")
    print("="*60)

    from src.workflow.task import Task
    from src.workflow.notifying_orchestrator import NotifyingOrchestrator
    from src.agents.base_agent import BaseAgent
    from src.llm.llm_client import create_llm_client
    from typing import Dict, Any

    # 创建Mock Agent
    llm_client = create_llm_client("mock", responses={
        "TestAgent": "测试完成"
    })

    class TestAgent(BaseAgent):
        def _get_responsibilities(self) -> str:
            return "测试Agent"

        def process(self, task) -> Dict[str, Any]:
            return {
                'success': True,
                'output': '测试输出'
            }

    agent = TestAgent("TestAgent", "测试员", llm_client=llm_client)

    # 创建编排器（禁用通知，避免实际发送）
    orchestrator = NotifyingOrchestrator(
        agents=[agent],
        max_iterations=5,
        enable_notifications=False  # 测试时禁用
    )

    # 创建任务
    task = Task("task-workflow", "测试任务", "测试工作流集成")

    # 执行
    result = orchestrator.execute(task)

    print(f"✅ 工作流执行结果: {result['success']}")
    assert result['success'] is True

    print("✅ 工作流集成测试通过")


def test_connection_manager():
    """测试6：连接管理器"""
    print("\n" + "="*60)
    print("测试6：连接管理器功能")
    print("="*60)

    from src.api.websocket import ConnectionManager

    manager = ConnectionManager()

    # 测试订阅管理
    manager.subscribe_task("conn-1", "task-1")
    manager.subscribe_task("conn-2", "task-1")
    manager.subscribe_task("conn-1", "task-2")

    print(f"✅ 任务订阅: {manager.task_subscriptions}")
    assert "task-1" in manager.task_subscriptions
    assert len(manager.task_subscriptions["task-1"]) == 2

    print(f"✅ 连接任务: {manager.connection_tasks}")
    assert len(manager.connection_tasks["conn-1"]) == 2

    # 测试取消订阅
    manager.unsubscribe_task("conn-1", "task-1")
    print(f"✅ 取消订阅后: {manager.task_subscriptions}")
    assert len(manager.task_subscriptions["task-1"]) == 1

    # 测试断开连接
    manager.disconnect("conn-1")
    print(f"✅ 断开连接后: {manager.connection_tasks}")
    assert "conn-1" not in manager.connection_tasks

    print("✅ 连接管理器测试通过")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("WebSocket实时通知系统测试")
    print("="*60)

    try:
        # 测试1：连接
        test_websocket_connection()

        # 测试2：订阅
        test_task_subscription()

        # 测试3：广播
        test_notification_broadcast()

        # 测试4：通知类型
        test_notification_types()

        # 测试5：工作流集成
        test_workflow_integration()

        # 测试6：连接管理器
        test_connection_manager()

        # 总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        print("✅ 所有测试通过")
        print("\n关键验证点:")
        print("  ✅ WebSocket连接建立和断开")
        print("  ✅ 任务订阅和取消订阅")
        print("  ✅ 通知广播到订阅者")
        print("  ✅ 各种通知类型")
        print("  ✅ 工作流集成")
        print("  ✅ 连接管理器功能")

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
