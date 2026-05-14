"""
完整工作流测试

测试7个Agent的协作流程（简单模式，不使用LLM）
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.requester import RequesterAgent
from src.agents.product_manager import ProductManagerAgent
from src.agents.architect import ArchitectAgent
from src.agents.developer import DeveloperAgent
from src.agents.code_reviewer import CodeReviewerAgent
from src.agents.tester import TesterAgent
from src.agents.devops import DevOpsAgent
from src.workflow.task import Task


def test_complete_workflow():
    """测试完整的7个Agent工作流"""

    print("""
╔══════════════════════════════════════════════════════════════╗
║           完整工作流测试                                      ║
║                                                               ║
║  测试7个Agent的协作：需求→设计→开发→审查→测试→部署          ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # 创建任务
    task = Task(
        task_id="WORKFLOW-001",
        title="开发在线商城系统",
        description="""
需要开发一个在线商城系统，包含以下功能：
1. 用户注册和登录
2. 商品浏览和搜索
3. 购物车管理
4. 订单处理
5. 支付集成

技术要求：
- 支持1000并发用户
- 响应时间小于500ms
- 数据安全可靠
        """
    )

    # 创建所有Agent
    agents = {
        'Requester': RequesterAgent(),
        'ProductManager': ProductManagerAgent(),
        'Architect': ArchitectAgent(),
        'Developer': DeveloperAgent(),
        'CodeReviewer': CodeReviewerAgent(),
        'Tester': TesterAgent(),
        'DevOps': DevOpsAgent()
    }

    # 工作流顺序
    workflow = [
        'Requester',
        'ProductManager',
        'Architect',
        'Developer',
        'CodeReviewer',
        'Tester',
        'DevOps'
    ]

    print(f"\n任务：{task.title}")
    print(f"工作流：{' → '.join(workflow)}")
    print("=" * 80)

    # 执行工作流
    current_step = 0
    max_iterations = 20  # 防止无限循环
    iteration = 0

    while current_step < len(workflow) and iteration < max_iterations:
        iteration += 1
        agent_name = workflow[current_step]
        agent = agents[agent_name]

        print(f"\n第{iteration}轮 - 执行Agent: {agent_name}")
        print("-" * 80)

        try:
            result = agent.process(task)

            if result['success']:
                print(f"✓ {agent_name} 完成: {result['message']}")
                current_step += 1

                # 如果是最后一个Agent，工作流完成
                if current_step >= len(workflow):
                    print("\n" + "=" * 80)
                    print("🎉 工作流完成！所有Agent都成功执行")
                    print("=" * 80)
                    break

            else:
                print(f"✗ {agent_name} 失败: {result['message']}")

                # 检查是否需要回退
                next_agent = result.get('next_agent')
                if next_agent and next_agent in workflow:
                    # 回退到指定Agent
                    current_step = workflow.index(next_agent)
                    print(f"→ 回退到 {next_agent}")
                else:
                    print("→ 工作流中断")
                    break

        except Exception as e:
            print(f"✗ {agent_name} 异常: {str(e)}")
            break

    # 打印最终结果
    print("\n" + "=" * 80)
    print("工作流执行总结")
    print("=" * 80)
    print(f"总轮次：{iteration}")
    print(f"任务状态：{task.status.value}")
    print(f"生成产物：{len(task.artifacts)}个")

    print("\n产物列表：")
    for i, artifact in enumerate(task.artifacts, 1):
        artifact_type = artifact.get('type', 'unknown') if isinstance(artifact, dict) else 'unknown'
        artifact_agent = artifact.get('agent', 'unknown') if isinstance(artifact, dict) else 'unknown'
        print(f"  {i}. {artifact_type} (by {artifact_agent})")

    return task


if __name__ == "__main__":
    task = test_complete_workflow()

    print("\n" + "=" * 80)
    print("✓ 测试完成")
    print("=" * 80)
