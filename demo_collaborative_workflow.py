"""
演示协作式工作流

展示Agent之间的多轮对话、质疑、修改过程
"""

import sys
sys.path.insert(0, '/home/mamingchang/multi-agent-dev-system')

from src.workflow.task import Task
from src.workflow.collaborative_orchestrator import CollaborativeOrchestrator
from src.agents.requester import RequesterAgent
from src.agents.product_manager import ProductManagerAgent
from src.agents.architect import ArchitectAgent
from src.agents.developer import DeveloperAgent
from src.agents.code_reviewer import CodeReviewerAgent


def demo_collaborative_workflow():
    """
    演示协作式工作流

    场景：开发一个用户登录功能

    预期流程：
    1. Requester整理需求
    2. ProductManager写PRD
    3. Architect设计架构
    4. Developer写代码
    5. CodeReviewer审查代码
       - 如果发现问题，要求Developer修改
       - Developer修改后，CodeReviewer再次审查
       - 通过后，流程结束
    """

    print("=" * 80)
    print("协作式工作流演示")
    print("=" * 80)

    # 创建任务
    task = Task(
        task_id="demo-001",
        title="用户登录功能",
        description="实现一个基本的用户登录功能，包括用户名密码验证、记住我选项、错误提示"
    )

    print(f"\n📋 任务: {task.title}")
    print(f"📝 描述: {task.description}")

    # 创建Agent列表（按执行顺序）
    agents = [
        RequesterAgent(),
        ProductManagerAgent(),
        ArchitectAgent(),
        DeveloperAgent(),
        CodeReviewerAgent()
    ]

    print(f"\n👥 参与Agent:")
    for i, agent in enumerate(agents, 1):
        print(f"  {i}. {agent.name} ({agent.role})")

    # 创建协作式Orchestrator
    orchestrator = CollaborativeOrchestrator(
        agents=agents,
        max_iterations_per_agent=5,  # 每个Agent最多执行5次
        max_dispute_rounds=3         # 最多争议3轮
    )

    print(f"\n⚙️  配置:")
    print(f"  每个Agent最多迭代: 5次")
    print(f"  最多争议轮次: 3轮")

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
    print(f"📊 最终状态: {result['final_status']}")
    print(f"💬 消息: {result['message']}")

    # 打印对话历史
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

            print(f"{icon} [{msg.from_agent} → {msg.to_agent}] {msg.message_type.value}")

            if isinstance(msg.content, dict):
                for key, value in msg.content.items():
                    print(f"   {key}: {value}")
            else:
                print(f"   {msg.content}")

            print()

    # 打印迭代统计
    if task.iteration_count:
        print(f"\n{'='*80}")
        print("迭代统计")
        print(f"{'='*80}\n")

        for agent_name, count in task.iteration_count.items():
            print(f"  {agent_name}: {count}次")

    # 打印产物
    if task.artifacts:
        print(f"\n{'='*80}")
        print(f"产物 (共{len(task.artifacts)}个)")
        print(f"{'='*80}\n")

        for artifact in task.artifacts:
            print(f"  📦 {artifact['type']}")
            print(f"     创建者: {artifact['agent']}")
            print(f"     版本: v{artifact['version']}")
            print(f"     时间: {artifact['timestamp']}")
            print()


if __name__ == '__main__':
    demo_collaborative_workflow()
