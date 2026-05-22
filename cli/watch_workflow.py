"""
实时观察工作流命令

允许用户实时观察Agent之间的协作对话，只在必要时介入
"""
import click
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.workflow.task import Task
from src.workflow.collaborative_orchestrator import CollaborativeOrchestrator
from src.agents.registration import AgentRegistration
from src.agents.requester import RequesterAgent
from src.agents.product_manager import ProductManagerAgent
from src.agents.architect import ArchitectAgent
from src.agents.developer import DeveloperAgent
from src.agents.code_reviewer import CodeReviewerAgent
from src.agents.tester import TesterAgent
from src.agents.devops import DevOpsAgent
from src.session_manager import SessionManager
from src.user_manager import UserManager
from src.project_manager import ProjectManager
import uuid
import time


@click.command()
@click.option('--project', help='项目名称')
@click.option('--title', prompt='任务标题', help='任务标题')
@click.option('--description', prompt='需求描述', help='详细需求描述')
@click.option('--auto-approve', is_flag=True, help='自动批准所有决策（观察模式）')
def watch(project: str, title: str, description: str, auto_approve: bool):
    """
    实时观察Agent协作工作流

    特点：
    - 实时显示Agent之间的对话和讨论
    - 显示反馈、质疑、修改过程
    - 只在Agent无法达成一致时需要人工介入
    - 可选自动批准模式（纯观察）

    示例：
    \b
    # 观察模式（需要时介入）
    workflow watch --project my-app

    \b
    # 纯观察模式（自动批准所有决策）
    workflow watch --project my-app --auto-approve
    """
    click.echo("\n" + "=" * 80)
    click.echo("👁️  实时观察模式 - Agent协作工作流")
    click.echo("=" * 80)

    if auto_approve:
        click.echo("🤖 自动批准模式：将自动批准所有决策，你只需观察")
    else:
        click.echo("👤 介入模式：Agent无法达成一致时会请求你的决策")

    click.echo()

    # 获取当前用户
    user_manager = UserManager()
    user = user_manager.get_current_user()
    if not user:
        click.echo("❌ 未设置当前用户", err=True)
        return

    user_id = user.user_id
    click.echo(f"当前用户: {user_id}")

    # 获取项目
    project_manager = ProjectManager(user_id)

    if project:
        project_obj = project_manager.get_project(project)
        if not project_obj:
            click.echo(f"❌ 项目不存在: {project}", err=True)
            return
    else:
        project_obj = project_manager.get_current_project()
        if not project_obj:
            click.echo("❌ 未设置当前项目", err=True)
            return

    click.echo(f"当前项目: {project_obj.project_name}\n")

    # 创建任务
    task = Task(
        task_id=str(uuid.uuid4()),
        title=title,
        description=description
    )

    # 创建会话
    session_manager = SessionManager.get_project_session_manager(
        user_id=user_id,
        project_name=project_obj.project_name
    )
    session = session_manager.create_session()
    session.add_task(task)

    click.echo(f"任务ID: {task.task_id}")
    click.echo(f"会话ID: {session.session_id}\n")

    # 获取项目上下文
    project_context = {
        'project_name': project_obj.project_name,
        'workspace_path': str(project_manager.get_project_workspace(project_obj.project_name)),
        'artifacts_path': str(project_manager.get_project_artifacts_dir(project_obj.project_name)),
        'docs_path': str(project_manager.get_project_docs_dir(project_obj.project_name)),
        'sessions_path': str(project_manager.get_project_sessions_dir(project_obj.project_name))
    }

    # 加载Agent
    agents = _load_agents(user_id, project_context)

    if not agents:
        click.echo("❌ 无法加载Agent", err=True)
        return

    click.echo(f"✓ 已加载 {len(agents)} 个Agent\n")
    click.echo("=" * 80)
    click.echo("🎬 工作流开始 - 观察Agent协作过程")
    click.echo("=" * 80)
    click.echo()

    # 创建人工输入回调（带观察者输出）
    def human_input_callback_with_observer(task, agent_name, reason):
        """人工输入回调 - 显示详细信息并请求决策"""

        click.echo("\n" + "🔔" * 40)
        click.echo("⚠️  需要人工介入")
        click.echo("🔔" * 40)
        click.echo(f"\n当前Agent: {agent_name}")
        click.echo(f"原因: {reason}")
        click.echo(f"\n任务: {task.title}")

        # 显示最近的对话
        if hasattr(task, 'conversation') and task.conversation:
            click.echo("\n📜 最近的对话:")
            recent_messages = task.conversation.get_recent_messages(5)
            for msg in recent_messages:
                click.echo(f"  [{msg.from_agent} → {msg.to_agent}] {msg.content[:100]}...")

        # 显示反馈
        if hasattr(task, 'feedback') and task.feedback:
            click.echo("\n💬 最近的反馈:")
            for feedback in task.feedback[-3:]:
                click.echo(f"  [{feedback.get('agent_name')}] {feedback.get('feedback', '')[:100]}...")

        if auto_approve:
            click.echo("\n🤖 自动批准模式：自动选择'继续'")
            time.sleep(1)  # 给用户时间看到信息
            return {
                'action': 'continue',
                'feedback': '自动批准'
            }

        # 请求用户决策
        click.echo("\n你的决策:")
        click.echo("  [c] 继续 - 接受当前状态，继续下一步")
        click.echo("  [r] 重试 - 让当前Agent重新执行")
        click.echo("  [s] 跳过 - 跳过当前Agent")
        click.echo("  [a] 终止 - 终止整个工作流")
        click.echo("  [f] 反馈 - 提供具体反馈")

        while True:
            choice = input("\n👉 你的选择: ").strip().lower()

            if choice == 'c':
                return {'action': 'continue', 'feedback': None}
            elif choice == 'r':
                return {'action': 'retry', 'feedback': None}
            elif choice == 's':
                return {'action': 'skip', 'feedback': None}
            elif choice == 'a':
                return {'action': 'abort', 'feedback': None}
            elif choice == 'f':
                feedback = input("📝 请输入反馈: ").strip()
                action = input("反馈后 [c]继续 / [r]重试: ").strip().lower()
                return {
                    'action': 'continue' if action == 'c' else 'retry',
                    'feedback': feedback
                }
            else:
                click.echo("❌ 无效选择，请重新输入")

    # 创建协作式Orchestrator
    orchestrator = CollaborativeOrchestrator(
        agents=agents,
        max_iterations_per_agent=5,
        max_dispute_rounds=3,
        human_input_callback=human_input_callback_with_observer
    )

    # 执行工作流
    try:
        result = orchestrator.execute(task)

        # 保存会话
        session.status = "completed" if result['success'] else "failed"
        session_manager.save_session(session)

        # 显示结果
        click.echo("\n" + "=" * 80)
        if result['success']:
            click.echo("✅ 工作流执行成功")
        else:
            click.echo("❌ 工作流执行失败")
        click.echo("=" * 80)

        click.echo(f"\n消息: {result['message']}")
        click.echo(f"会话已保存: {session.session_id}")

    except KeyboardInterrupt:
        click.echo("\n\n⚠️  工作流被用户中断")
        session.status = "cancelled"
        session_manager.save_session(session)
    except Exception as e:
        click.echo(f"\n\n❌ 工作流执行异常: {str(e)}", err=True)
        session.status = "failed"
        session_manager.save_session(session)
        import traceback
        traceback.print_exc()


def _load_agents(user_id: str, project_context: dict):
    """加载Agent并设置项目上下文"""
    registration = AgentRegistration(user_id=user_id)

    agent_configs = [
        ('requester', RequesterAgent),
        ('product_manager', ProductManagerAgent),
        ('architect', ArchitectAgent),
        ('developer', DeveloperAgent),
        ('code_reviewer', CodeReviewerAgent),
        ('tester', TesterAgent),
        ('devops', DevOpsAgent)
    ]

    agents = []

    for registered_name, agent_class in agent_configs:
        try:
            config = registration.load_config(registered_name)
            metadata = None

            if config:
                metadata = registration.load_metadata(registered_name)
            else:
                global_registration = AgentRegistration()
                config = global_registration.load_config(registered_name)
                if config:
                    metadata = global_registration.load_metadata(registered_name)

            if config:
                agent = agent_class(name=config.get('name', registered_name), config=config)

                if metadata and 'agent_id' in metadata:
                    agent.agent_id = metadata['agent_id']
                else:
                    agent.agent_id = agent.name

                agent.set_project_context(project_context)
                agents.append(agent)

        except Exception as e:
            click.echo(f"  ⚠️  加载Agent失败 {registered_name}: {e}")
            agent = agent_class()
            agent.set_project_context(project_context)
            agents.append(agent)

    return agents


if __name__ == '__main__':
    watch()
