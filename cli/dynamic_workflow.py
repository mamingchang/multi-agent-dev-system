"""
动态路由工作流CLI命令

Agent自主决定工作流路由
"""
import click
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.workflow.task import Task, TaskStatus
from src.dynamic_orchestrator import DynamicOrchestrator
from src.agents.registration import AgentRegistration
from src.session_manager import SessionManager
from src.user_manager import UserManager
from src.project_manager import ProjectManager
import uuid


@click.command()
@click.option('--project', help='项目名称')
@click.option('--task-id', help='继续已有任务（任务ID）')
@click.option('--title', help='新任务标题')
@click.option('--description', help='新任务描述')
@click.option('--start-agent', help='起始Agent（默认为第一个）')
def dynamic(project: str, task_id: str, title: str, description: str, start_agent: str):
    """
    动态路由工作流 - Agent自主决定下一步

    特点：
    - Agent在输出中指定next_agent
    - 灵活的工作流路由
    - 自动推断（如果未指定）
    - 防止无限循环

    示例：
    \b
    # 列出项目任务
    task list --project my-app

    \b
    # 继续已有任务
    workflow dynamic --project my-app --task-id abc123

    \b
    # 创建新任务
    workflow dynamic --project my-app --title "实现登录" --description "..."

    \b
    # 指定起始Agent
    workflow dynamic --project my-app --start-agent Developer
    """
    click.echo("\n" + "=" * 80)
    click.echo("🎯 动态路由工作流 - Agent自主决定")
    click.echo("=" * 80)
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

    # 导入TaskManager
    from src.task_manager import TaskManager
    task_manager = TaskManager(user_id, project_obj.project_name)

    # 选择或创建任务
    if task_id:
        # 继续已有任务
        tasks = task_manager.list_tasks()
        matching = [t for t in tasks if t['task_id'].startswith(task_id)]

        if not matching:
            click.echo(f"❌ 任务不存在: {task_id}", err=True)
            return

        task_data = matching[0]
        task = Task.from_dict(task_data)
        click.echo(f"📋 继续任务: {task.title}")
        click.echo(f"   状态: {task.status}")
        click.echo(f"   描述: {task.description}\n")
    else:
        # 列出现有任务
        existing_tasks = task_manager.list_tasks()

        if existing_tasks:
            click.echo("=" * 80)
            click.echo("📋 项目现有任务")
            click.echo("=" * 80)

            from tabulate import tabulate
            rows = []
            for t in existing_tasks[:5]:  # 只显示最近5个
                rows.append([
                    t['task_id'][:8],
                    t['title'][:40],
                    t['status'],
                    t.get('created_at', 'N/A')[:19]
                ])

            click.echo(tabulate(rows, headers=['ID', '标题', '状态', '创建时间'], tablefmt='simple'))
            click.echo("\n" + "=" * 80)
            click.echo("💡 接下来你可以:")
            click.echo("=" * 80)
            click.echo("  1️⃣  继续已有任务 - 输入任务ID的前8位（如: a6fa1f74）")
            click.echo("  2️⃣  创建新任务 - 直接输入新任务的标题")
            click.echo("  3️⃣  取消操作 - 按 Ctrl+C 或输入空行\n")

            user_input = click.prompt('👉 请选择', default='', show_default=False).strip()

            if not user_input:
                click.echo("✓ 已取消操作")
                return

            # 判断是任务ID还是新任务标题
            matching = [t for t in existing_tasks if t['task_id'].startswith(user_input)]

            if matching:
                # 找到匹配的任务，继续该任务
                task_data = matching[0]
                task = Task.from_dict(task_data)
                click.echo(f"\n✓ 继续任务: {task.title}")
                click.echo(f"  状态: {task.status}")
                click.echo(f"  描述: {task.description}\n")
            else:
                # 当作新任务标题
                title = user_input
                if not description:
                    description = click.prompt('📝 需求描述', default='', show_default=False).strip()
                    if not description:
                        click.echo("✓ 已取消操作")
                        return

                task = task_manager.create_task(title, description)
                click.echo(f"\n✓ 创建新任务: {task.title}\n")
        else:
            # 没有现有任务，直接创建新任务
            click.echo("=" * 80)
            click.echo("📝 创建新任务")
            click.echo("=" * 80)

            if not title:
                title = click.prompt('任务标题', default='', show_default=False).strip()
                if not title:
                    click.echo("✓ 已取消操作")
                    return

            if not description:
                description = click.prompt('需求描述', default='', show_default=False).strip()
                if not description:
                    click.echo("✓ 已取消操作")
                    return

            task = task_manager.create_task(title, description)
            click.echo(f"\n✓ 创建新任务: {task.title}\n")

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
    agents_dict = _load_agents_as_dict(user_id, project_obj, project_context)

    if not agents_dict:
        click.echo("❌ 无法加载Agent", err=True)
        return

    click.echo(f"✓ 已加载 {len(agents_dict)} 个Agent")
    click.echo(f"  可用Agent: {', '.join(agents_dict.keys())}\n")

    # 创建人工介入回调
    def human_input_callback(task, agent_name, reason):
        """人工介入回调"""
        click.echo("\n" + "🔔" * 40)
        click.echo("⚠️  需要人工介入")
        click.echo("🔔" * 40)
        click.echo(f"\n当前Agent: {agent_name}")
        click.echo(f"原因: {reason}")

        click.echo("\n你的决策:")
        click.echo("  [c] 继续 - 指定下一个Agent")
        click.echo("  [a] 终止 - 终止工作流")

        while True:
            try:
                choice = input("\n👉 你的选择: ").strip().lower()

                if choice == 'c':
                    click.echo(f"\n可用Agent: {', '.join(agents_dict.keys())}")
                    next_agent = input("指定下一个Agent: ").strip()

                    if next_agent in agents_dict:
                        return {
                            'action': 'continue',
                            'next_agent': next_agent
                        }
                    else:
                        click.echo(f"❌ Agent不存在: {next_agent}")
                        continue

                elif choice == 'a':
                    return {'action': 'abort'}
                else:
                    click.echo("❌ 无效选择，请重新输入")

            except (EOFError, KeyboardInterrupt):
                # 非交互式环境或用户中断，默认终止
                click.echo("\n\n⚠️  检测到非交互式环境或用户中断，自动终止工作流")
                return {'action': 'abort'}

    # 创建DynamicOrchestrator
    orchestrator = DynamicOrchestrator(
        agents=agents_dict,
        max_total_iterations=50,
        max_iterations_per_agent=10,
        human_input_callback=human_input_callback
    )

    # 执行工作流
    try:
        result = orchestrator.execute(task, start_agent=start_agent)

        # 保存任务状态
        if result['success']:
            task_manager.update_task_status(task.task_id, TaskStatus.COMPLETED)
        else:
            task_manager.update_task_status(task.task_id, TaskStatus.FAILED)

        # 保存会话
        session.status = "completed" if result['success'] else "failed"
        session_manager.save_session(session)

        # 显示结果
        click.echo("\n" + "=" * 80)
        if result['success']:
            click.echo("✅ 工作流执行成功")
            if 'completed_by' in result:
                click.echo(f"   完成者: {result['completed_by']}")
        else:
            click.echo("❌ 工作流执行失败")
        click.echo("=" * 80)

        click.echo(f"\n消息: {result['message']}")
        click.echo(f"总迭代次数: {result.get('total_iterations', 0)}")

        # 显示执行路径
        if 'execution_path' in result and result['execution_path']:
            click.echo(f"\n执行路径 ({len(result['execution_path'])}步):")
            for i, step in enumerate(result['execution_path'], 1):
                click.echo(f"  {i}. {step['agent']} (第{step['iteration']}次)")

        click.echo(f"\n会话已保存: {session.session_id}")

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


def _load_agents_as_dict(user_id: str, project_obj, project_context: dict):
    """
    加载Agent为字典格式（统一使用GenericAgent）

    所有Agent（包括7个标准Agent）都通过GenericAgent加载，
    不再使用专门的Python类。这样实现完全统一的Agent管理。

    Args:
        user_id: 用户ID
        project_obj: 项目对象
        project_context: 项目上下文

    Returns:
        Dict[str, BaseAgent]: Agent字典
    """
    registration = AgentRegistration(user_id=user_id)
    from src.agents.generic_agent import GenericAgent

    agents_dict = {}

    # 获取项目配置的Agent列表
    # 如果没有配置，默认使用7个标准Agent
    default_agents = ['requester', 'product_manager', 'architect', 'developer', 'code_reviewer', 'tester', 'devops']
    project_agents = project_obj.agents if project_obj.agents else default_agents

    click.echo(f"项目配置的Agent: {', '.join(project_agents)}\n")

    for agent_name in project_agents:
        try:
            # 解析agent_name（可能是user_id_agent_name格式）
            if '_' in agent_name and agent_name.count('_') >= 2:
                # 来自其他用户的Agent
                parts = agent_name.split('_')
                source_user = '_'.join(parts[:-1])
                actual_agent_name = parts[-1]

                # 从指定用户加载
                source_registration = AgentRegistration(user_id=source_user)
                config = source_registration.load_config(actual_agent_name)
                metadata = source_registration.load_metadata(actual_agent_name)

                click.echo(f"  ✓ 加载Agent: {actual_agent_name} (来自 {source_user})")
            else:
                # 当前用户的Agent
                actual_agent_name = agent_name
                config = registration.load_config(agent_name)
                metadata = registration.load_metadata(agent_name)

                if not config:
                    # 尝试全局Agent
                    global_registration = AgentRegistration()
                    config = global_registration.load_config(agent_name)
                    metadata = global_registration.load_metadata(agent_name)

                click.echo(f"  ✓ 加载Agent: {agent_name}")

            if config:
                # 使用配置文件中的name（保持一致性）
                agent_name_from_config = config.get('name', actual_agent_name)

                # 统一使用GenericAgent加载所有Agent
                # 不再区分标准Agent和自定义Agent
                agent = GenericAgent(
                    name=agent_name_from_config,
                    config=config,
                    project_context=project_context
                )

                # 判断是否为标准Agent（仅用于显示）
                is_standard = config.get('metadata', {}).get('is_standard_agent', False)
                original_class = config.get('metadata', {}).get('original_class', 'N/A')

                if is_standard:
                    click.echo(f"    类型: 标准Agent (原{original_class}，现GenericAgent)")
                else:
                    click.echo(f"    类型: 自定义Agent (GenericAgent)")

                # 设置agent_id
                if metadata and 'agent_id' in metadata:
                    agent.agent_id = metadata['agent_id']
                else:
                    agent.agent_id = agent_name

                agent.set_project_context(project_context)

                # 关键：使用配置文件中的name作为key（小写+下划线格式）
                # 这样Agent在输出next_agent时使用的名称就能匹配上
                agents_dict[agent_name_from_config] = agent

        except Exception as e:
            click.echo(f"  ⚠️  加载Agent失败 {agent_name}: {e}")

    return agents_dict


if __name__ == '__main__':
    dynamic()
