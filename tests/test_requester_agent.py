"""
测试Requester Agent

演示如何使用改造后的Requester Agent进行需求分析
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.requester import RequesterAgent
from src.workflow.task import Task


def test_requester_with_clear_requirement():
    """
    测试1：清晰的需求

    这个需求描述得很清楚，Agent应该能够顺利分析
    """
    print("=" * 80)
    print("测试1：清晰的需求")
    print("=" * 80)

    # 创建Agent
    agent = RequesterAgent()

    # 创建一个清晰的需求任务
    task = Task(
        task_id="TEST-001",
        title="开发用户管理系统",
        description="""
我们需要开发一个用户管理系统，具体要求如下：

功能需求：
1. 用户注册：支持邮箱和手机号注册
2. 用户登录：支持密码登录和第三方登录（微信、支付宝）
3. 个人信息管理：用户可以修改昵称、头像、密码
4. 权限管理：分为普通用户、管理员、超级管理员三种角色

技术要求：
- 后端使用Python FastAPI
- 数据库使用PostgreSQL
- 前端使用React

性能要求：
- 支持10万并发用户
- 登录响应时间小于500ms
        """
    )

    # 处理任务
    result = agent.process(task)

    # 打印结果
    print("\n" + "=" * 80)
    print("处理结果:")
    print("=" * 80)
    print(f"成功: {result['success']}")
    print(f"消息: {result['message']}")
    print(f"下一个Agent: {result.get('next_agent', 'None')}")

    if 'analysis' in result:
        print("\n详细分析:")
        analysis = result['analysis']
        print(f"  需求总结: {analysis.get('requirement_summary', 'N/A')}")
        print(f"  清晰度: {analysis.get('clarity_score', 'N/A')}/10")
        print(f"  完整度: {analysis.get('completeness_score', 'N/A')}/10")
        print(f"  可行性: {analysis.get('feasibility', 'N/A')}")


def test_requester_with_vague_requirement():
    """
    测试2：模糊的需求

    这个需求描述得很模糊，Agent应该提出澄清问题
    """
    print("\n\n" + "=" * 80)
    print("测试2：模糊的需求")
    print("=" * 80)

    agent = RequesterAgent()

    # 创建一个模糊的需求任务
    task = Task(
        task_id="TEST-002",
        title="做一个网站",
        description="我想做一个网站，要好看，要快，要安全。"
    )

    result = agent.process(task)

    print("\n" + "=" * 80)
    print("处理结果:")
    print("=" * 80)
    print(f"成功: {result['success']}")
    print(f"消息: {result['message']}")
    print(f"下一个Agent: {result.get('next_agent', 'None')}")

    if 'analysis' in result:
        analysis = result['analysis']
        if analysis.get('questions'):
            print(f"\n需要澄清的问题 ({len(analysis['questions'])}个):")
            for i, q in enumerate(analysis['questions'], 1):
                print(f"  {i}. {q}")


def test_requester_without_llm():
    """
    测试3：不使用LLM（简单模式）

    模拟LLM不可用的情况
    """
    print("\n\n" + "=" * 80)
    print("测试3：简单模式（不使用LLM）")
    print("=" * 80)

    # 临时清空API密钥，模拟LLM不可用
    old_key = os.environ.get('ANTHROPIC_API_KEY')
    if old_key:
        del os.environ['ANTHROPIC_API_KEY']

    agent = RequesterAgent()

    task = Task(
        task_id="TEST-003",
        title="开发博客系统",
        description="需要一个简单的博客系统，支持文章发布和评论。"
    )

    result = agent.process(task)

    # 恢复API密钥
    if old_key:
        os.environ['ANTHROPIC_API_KEY'] = old_key

    print("\n" + "=" * 80)
    print("处理结果:")
    print("=" * 80)
    print(f"成功: {result['success']}")
    print(f"消息: {result['message']}")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║           Requester Agent 测试                                ║
║                                                               ║
║  测试改造后的Requester Agent的需求分析能力                   ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # 检查是否设置了API密钥
    if os.getenv("ANTHROPIC_API_KEY"):
        print("✓ 检测到ANTHROPIC_API_KEY，将使用LLM进行智能分析\n")

        # 运行测试
        test_requester_with_clear_requirement()
        test_requester_with_vague_requirement()

    else:
        print("⚠️  未检测到ANTHROPIC_API_KEY，将使用简单模式\n")
        print("提示：设置环境变量以启用LLM:")
        print("  export ANTHROPIC_API_KEY='your-api-key'\n")

        # 只运行简单模式测试
        test_requester_without_llm()

    print("\n" + "=" * 80)
    print("✓ 所有测试完成")
    print("=" * 80)
