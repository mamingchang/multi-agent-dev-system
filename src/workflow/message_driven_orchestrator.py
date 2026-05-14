"""
消息驱动的Orchestrator - 基于@提及的Agent协作系统

核心特性：
1. 不是线性流水线，而是消息驱动
2. 人工或Agent通过@提及来指定下一个工作的Agent
3. Agent完成后可以@其他Agent请求审查或继续工作
4. 支持随时人工介入
"""

from typing import List, Dict, Any, Optional
from enum import Enum
import asyncio
from ..workflow.task import Task, TaskStatus
from ..agents.base_agent import BaseAgent
from ..conversation import MessageType


class MessageDrivenOrchestrator:
    """
    消息驱动的工作流编排器

    工作模式：
    1. 人工@Agent -> Agent开始工作
    2. Agent完成 -> 可以@其他Agent继续
    3. Agent之间可以互相@进行讨论
    4. 人工随时可以@任何Agent介入
    """

    def __init__(
        self,
        agents: List[BaseAgent],
        task: Task,
        websocket_callback=None,
        db_instance=None
    ):
        """
        初始化消息驱动的Orchestrator

        Args:
            agents: Agent列表
            task: 任务对象
            websocket_callback: WebSocket回调函数
            db_instance: 数据库实例
        """
        self.agents = agents
        self.task = task
        self.websocket_callback = websocket_callback
        self.db_instance = db_instance

        # Agent映射
        self.agent_map = {agent.name: agent for agent in agents}

        # 消息队列
        self.message_queue = asyncio.Queue()

        # 运行状态
        self.running = False

    async def start(self):
        """启动orchestrator，开始处理消息"""
        self.running = True
        print("🚀 消息驱动Orchestrator已启动，等待@提及...")

        # 发送启动通知
        if self.websocket_callback:
            await self.websocket_callback({
                "type": "orchestrator_ready",
                "message": "系统已就绪，使用@提及Agent开始协作"
            })

        # 持续处理消息队列
        while self.running:
            try:
                print(f"⏳ 等待消息... (队列大小: {self.message_queue.qsize()}, running: {self.running})")

                # 直接等待消息，不设置超时
                # 这样当消息到达时会立即被唤醒
                message = await self.message_queue.get()

                print(f"✅ 收到队列消息，准备处理")
                await self._process_message(message)

            except Exception as e:
                print(f"❌ 处理消息出错: {e}")
                import traceback
                traceback.print_exc()

    async def stop(self):
        """停止orchestrator"""
        self.running = False
        print("🛑 消息驱动Orchestrator已停止")

    async def handle_human_message(self, message: Dict[str, Any]):
        """
        处理人工消息

        Args:
            message: {
                'content': str,
                'mentioned_agents': List[str],
                'user_id': int
            }
        """
        print(f"📨 收到人工消息: {message.get('content', '')[:50]}...")
        print(f"   提及Agent: {message.get('mentioned_agents', [])}")
        print(f"   队列当前大小: {self.message_queue.qsize()}")

        # 将消息放入队列
        await self.message_queue.put({
            'type': 'human',
            'from': 'Human',
            'content': message['content'],
            'mentioned_agents': message.get('mentioned_agents', []),
            'user_id': message.get('user_id')
        })

        print(f"   ✅ 消息已放入队列，新大小: {self.message_queue.qsize()}")

    async def handle_agent_message(self, agent_name: str, message: Dict[str, Any]):
        """
        处理Agent消息

        Args:
            agent_name: Agent名称
            message: {
                'content': str,
                'mentioned_agents': List[str],
                'message_type': str  # 'output', 'question', 'objection'
            }
        """
        print(f"📨 收到{agent_name}消息: {message.get('content', '')[:50]}...")

        await self.message_queue.put({
            'type': 'agent',
            'from': agent_name,
            'content': message['content'],
            'mentioned_agents': message.get('mentioned_agents', []),
            'message_type': message.get('message_type', 'output')
        })

    async def _process_message(self, message: Dict[str, Any]):
        """
        处理一条消息

        Args:
            message: 消息对象
        """
        print(f"🔄 开始处理消息: {message.get('content', '')[:50]}...")

        mentioned_agents = message.get('mentioned_agents', [])
        print(f"   提及的Agent: {mentioned_agents}")

        if not mentioned_agents:
            print("⚠️  消息未@任何Agent，忽略")
            return

        # 保存消息到对话历史
        if self.task.conversation:
            self.task.conversation.add_message(
                from_agent=message['from'],
                to_agent=','.join(mentioned_agents),
                content=message['content'],
                message_type=MessageType.INFO
            )

        # 依次唤醒被@的Agent
        for agent_name in mentioned_agents:
            if agent_name not in self.agent_map:
                print(f"⚠️  未知Agent: {agent_name}")
                continue

            print(f"🎯 准备调用Agent: {agent_name}")
            await self._invoke_agent(agent_name, message)

    async def _invoke_agent(self, agent_name: str, trigger_message: Dict[str, Any]):
        """
        调用Agent执行任务

        Args:
            agent_name: Agent名称
            trigger_message: 触发消息
        """
        agent = self.agent_map[agent_name]

        print(f"\n{'='*60}")
        print(f"👤 {agent.name} ({agent.role}) 被@提及，开始工作")
        print(f"{'='*60}\n")

        # 发送WebSocket通知
        if self.websocket_callback:
            await self.websocket_callback({
                "type": "agent_started",
                "agent_name": agent_name,
                "message": f"{agent.role}开始工作..."
            })

        # 更新任务状态
        self.task.update_status(self._get_task_status(agent_name), agent_name)

        try:
            # 执行Agent
            result = agent.process(self.task)

            if not result['success']:
                print(f"❌ {agent.name} 处理失败: {result.get('message', '未知错误')}")

                if self.websocket_callback:
                    await self.websocket_callback({
                        "type": "agent_error",
                        "agent_name": agent_name,
                        "message": result.get('message', '未知错误')
                    })
                return

            print(f"✅ {agent.name} 完成工作")

            # 保存产物
            if 'output' in result and result['output']:
                self.task.add_artifact(
                    artifact_type=self._get_artifact_type(agent_name),
                    content=result['output'],
                    agent=agent_name
                )

            # 发送Agent输出到WebSocket
            if self.websocket_callback:
                print(f"📤 发送WebSocket消息: agent={agent_name}, content_length={len(result.get('output', ''))}")
                await self.websocket_callback({
                    "type": "agent_message",
                    "agent_name": agent_name,
                    "content": result.get('output', ''),
                    "event_type": "output"
                })
                print(f"✅ WebSocket消息已发送")

            # 保存事件到数据库
            if self.db_instance:
                try:
                    with self.db_instance.get_session() as session:
                        from ..database.models import TaskEvent
                        event = TaskEvent(
                            task_id=self.task.task_id,
                            agent_name=agent_name,
                            agent_type=agent.role,
                            event_type="output",
                            content={"message": result.get('output', '')}
                        )
                        session.add(event)
                        session.commit()
                        print(f"💾 事件已保存到数据库")
                except Exception as e:
                    print(f"⚠️  保存事件失败: {e}")

            # 检查Agent输出中是否@了其他Agent
            output = result.get('output', '')
            mentioned_in_output = self._extract_mentions(output)

            if mentioned_in_output:
                print(f"🔔 {agent.name}在输出中@了: {mentioned_in_output}")
                # 自动触发被@的Agent
                await self.handle_agent_message(agent_name, {
                    'content': output,
                    'mentioned_agents': mentioned_in_output,
                    'message_type': 'output'
                })

        except Exception as e:
            print(f"💥 {agent.name} 执行异常: {str(e)}")
            import traceback
            traceback.print_exc()

            if self.websocket_callback:
                await self.websocket_callback({
                    "type": "agent_error",
                    "agent_name": agent_name,
                    "message": str(e)
                })

    def _extract_mentions(self, text: str) -> List[str]:
        """
        从文本中提取@提及的Agent

        Args:
            text: 文本内容

        Returns:
            List[str]: 被提及的Agent名称列表
        """
        import re
        mentions = re.findall(r'@(\w+)', text)
        # 只返回存在的Agent
        return [m for m in mentions if m in self.agent_map]

    def _get_task_status(self, agent_name: str) -> TaskStatus:
        """根据Agent名称获取任务状态"""
        status_map = {
            'RequirementAnalyst': TaskStatus.IN_REQUIREMENT,
            'ProductManager': TaskStatus.IN_DESIGN,
            'Architect': TaskStatus.IN_DESIGN,
            'Developer': TaskStatus.IN_DEVELOPMENT,
            'CodeReviewer': TaskStatus.IN_REVIEW,
            'Tester': TaskStatus.IN_TESTING,
            'DevOps': TaskStatus.IN_DEPLOYMENT
        }
        return status_map.get(agent_name, TaskStatus.IN_DEVELOPMENT)

    def _get_artifact_type(self, agent_name: str) -> str:
        """根据Agent名称获取产物类型"""
        artifact_map = {
            'RequirementAnalyst': 'requirement',
            'ProductManager': 'prd',
            'Architect': 'architecture',
            'Developer': 'code',
            'CodeReviewer': 'review',
            'Tester': 'test_report',
            'DevOps': 'deployment'
        }
        return artifact_map.get(agent_name, 'output')
