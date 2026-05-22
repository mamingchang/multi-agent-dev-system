"""
演示人工介入机制

展示当Agent之间争议超过3轮时，如何升级到人工介入
"""

import sys
sys.path.insert(0, '/home/mamingchang/multi-agent-dev-system')

from src.workflow.task import Task
from src.workflow.collaborative_orchestrator import CollaborativeOrchestrator
from src.agents.requester import RequesterAgent
from src.agents.product_manager import ProductManagerAgent
from src.agents.architect import ArchitectAgent


def human_input_callback(task, agent_name, reason):
    """
    人工输入回调函数（模拟人工决策）

    在真实应用中，这个函数会：
    1. 在Web界面显示决策请求
    2. 等待用户输入
    3. 返回用户的决策

    这里我们模拟自动决策
    """
    print(f"\n{'='*60}")
    print(f"🤖 模拟人工决策")
    print(f"{'='*60}")
    print(f"Agent: {agent_name}")
    print(f"原因: {reason}")
    print(f"\n模拟决策: 继续执行")
    print(f"{'='*60}\n")

    # 模拟人工决策：继续执行
    return {
        'action': 'continue',
        'instruction': '已审查，可以继续',
        'note': '这是模拟的人工决策'
    }


def demo_human_intervention():
    """
    演示人工介入流程

    场景：
    1. 创建一个任务
    2. Agent之间产生争议
    3. 争议超过3轮
    4. 升级到人工介入
    5. 人工做出决策
    6. 流程继续执行
    """

    print("=" * 80)
    print("人工介入机制演示")
    print("=" * 80)

    # 创建任务
    task = Task(
        task_id="demo-002",
        title="复杂的用户管理系统",
        description="实现一个复杂的用户管理系统，包括权限控制、审计日志、多租户支持"
    )

    print(f"\n📋 任务: {task.title}")
    print(f"📝 描述: {task.description}")

    # 创建Agent列表
    agents = [
        RequesterAgent(),
        ProductManagerAgent(),
        ArchitectAgent()
    ]

    print(f"\n👥 参与Agent:")
    for i, agent in enumerate(agents, 1):
        print(f"  {i}. {agent.name} ({agent.role})")

    # 创建协作式Orchestrator，配置人工输入回调
    orchestrator = CollaborativeOrchestrator(
        agents=agents,
        max_iterations_per_agent=5,
        max_dispute_rounds=3,
        decision_queue=None,  # 不使用DecisionQueue（异步方式）
        human_input_callback=human_input_callback  # 使用回调函数（同步方式）
    )

    print(f"\n⚙️  配置:")
    print(f"  每个Agent最多迭代: 5次")
    print(f"  最多争议轮次: 3轮")
    print(f"  人工介入方式: 回调函数（同步）")

    # 执行工作流
    print(f"\n{'='*80}")
    print("开始执行...")
    print(f"{'='*80}\n")

    result = orchestrator.execute(task)

    # 打印结果
    print(f"\n{'='*80}")
    print("执行结果")
    print(f"{'='*80}")

    print(f"\n✅ 成功: {result['success']}")
    print(f"💬 消息: {result['message']}")

    if 'human_decision' in result and result['human_decision']:
        print(f"\n👤 人工决策:")
        for key, value in result['human_decision'].items():
            print(f"   {key}: {value}")

    # 打印对话历史（包含人工消息）
    if task.conversation and len(task.conversation) > 0:
        print(f"\n{'='*80}")
        print(f"对话历史 (共{len(task.conversation)}条消息)")
        print(f"{'='*80}\n")

        for msg in task.conversation.messages:
            icon_map = {
                'question': '❓',
                'suggestion': '💡',
                'objection': '⚠️',
                'revision_request': '🔄',
                'approval': '✅',
                'info': 'ℹ️',
                'clarification': '📝'
            }

            icon = icon_map.get(msg.message_type.value, '💬')

            # 高亮人工消息
            if msg.from_agent == "Human" or msg.to_agent == "Human":
                print(f"👤 {icon} [{msg.from_agent} → {msg.to_agent}] {msg.message_type.value}")
            else:
                print(f"{icon} [{msg.from_agent} → {msg.to_agent}] {msg.message_type.value}")

            if isinstance(msg.content, dict):
                for key, value in msg.content.items():
                    print(f"   {key}: {value}")
            else:
                print(f"   {msg.content}")

            print()


if __name__ == '__main__':
    demo_human_intervention()
