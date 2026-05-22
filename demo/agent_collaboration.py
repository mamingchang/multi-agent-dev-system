#!/usr/bin/env python3
"""
Agent协作演示脚本

演示如何使用注册系统的Agent进行协作
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

from src.orchestrator import Orchestrator
from src.workflow.task import Task
from src.session_manager import SessionManager


def demo_simple_workflow():
    """演示简单的工作流"""
    print("=" * 80)
    print("Agent协作演示 - 简单工作流")
    print("=" * 80)
    print()

    # 创建任务（需要提供task_id）
    import uuid
    task = Task(
        task_id=str(uuid.uuid4()),
        title="开发一个简单的Todo应用",
        description="""
        需求：
        1. 用户可以添加待办事项
        2. 用户可以标记待办事项为完成
        3. 用户可以删除待办事项
        4. 使用Web界面

        技术栈：
        - 后端：Python Flask
        - 前端：HTML + JavaScript
        - 数据库：SQLite
        """
    )

    # 创建会话管理器
    session_manager = SessionManager()
    session = session_manager.create_session(user_id="demo_user")

    # 创建Orchestrator（使用注册系统）
    orchestrator = Orchestrator(
        config={'max_iterations': 10},
        session_manager=session_manager,
        use_registration=True  # 使用注册系统
    )

    # 执行工作流
    result = orchestrator.execute_workflow(task, session=session)

    # 打印结果
    print("\n" + "=" * 80)
    print("执行结果")
    print("=" * 80)
    print(f"成功: {result['success']}")
    print(f"消息: {result['message']}")
    if result.get('session_id'):
        print(f"会话ID: {result['session_id']}")

    return result


def demo_agent_info():
    """演示查看Agent信息"""
    print("=" * 80)
    print("Agent信息查看")
    print("=" * 80)
    print()

    # 创建Orchestrator
    orchestrator = Orchestrator(use_registration=True)

    print("已加载的Agent:")
    for name, agent in orchestrator.agents.items():
        print(f"\n{name}:")
        print(f"  角色: {agent.role}")
        print(f"  配置: {agent.config.get('description', 'N/A')}")

        # 显示能力信息
        if hasattr(agent, 'tools'):
            print(f"  工具数: {len(agent.tools)}")
        if hasattr(agent, 'skills'):
            print(f"  技能数: {len(agent.skills)}")
        if hasattr(agent, 'data_paths'):
            print(f"  数据路径: {agent.data_paths.get('root', 'N/A')}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Agent协作演示')
    parser.add_argument('--mode', choices=['workflow', 'info'], default='info',
                       help='演示模式：workflow=执行工作流, info=查看Agent信息')

    args = parser.parse_args()

    try:
        if args.mode == 'workflow':
            demo_simple_workflow()
        elif args.mode == 'info':
            demo_agent_info()

    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
