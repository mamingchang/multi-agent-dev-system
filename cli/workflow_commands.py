"""
工作流交互CLI命令（支持项目层）

支持：
1. 实时查看Agent输出
2. 人工介入和反馈
3. 控制工作流执行
4. 项目级工作流隔离

改进：
- 支持--project参数（必需）
- 会话保存到项目目录
- Agent工作在项目workspace
"""
import click
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.workflow.task import Task, TaskStatus
from src.workflow.collaborative_orchestrator import CollaborativeOrchestrator
from src.interactive_orchestrator import InteractiveOrchestrator
from src.agents.registration import AgentRegistration
from src.agents.requester import RequesterAgent
from src.agents.product_manager import ProductManagerAgent
from src.agents.architect import ArchitectAgent
from src.agents.developer import DeveloperAgent
from src.agents.code_reviewer import CodeReviewerAgent
from src.agents.tester import TesterAgent
from src.agents.devops import DevOpsAgent
from src.session_manager import SessionManager, Session
from src.user_manager import UserManager
from src.project_manager import ProjectManager
import uuid


def get_current_user_id():
    """获取当前用户ID"""
    manager = UserManager()
    user = manager.get_current_user()
    if not user:
        click.echo("❌ 未设置当前用户", err=True)
        click.echo("请先运行: ./mas user init", err=True)
        sys.exit(1)
    return user.user_id


@click.group()
def workflow():
    """交互式工作流命令"""
    pass


# 导入watch命令
from cli.watch_workflow import watch
from cli.dynamic_workflow import dynamic

# 添加命令到workflow组
workflow.add_command(watch)
workflow.add_command(dynamic)


@workflow.command()
@click.option('--project', help='项目名称（如果未提供，使用当前项目）')
@click.option('--title', prompt='任务标题', help='任务标题')
@click.option('--description', prompt='需求描述', help='详细需求描述')
@click.option('--interactive/--no-interactive', default=True, help='是否启用交互模式')
def run(project: str, title: str, description: str, interactive: bool):
    """
    运行交互式工作流

    示例：
    \b
    # 在指定项目中运行
    workflow run --project todo-app --title "添加用户认证"

    \b
    # 在当前项目中运行
    workflow run --title "添加功能"

    \b
    # 非交互模式
    workflow run --project todo-app --title "..." --no-interactive
    """
    click.echo("=" * 80)
    click.echo("🚀 启动交互式工作流")
    click.echo("=" * 80)

    # 获取当前用户
    user_id = get_current_user_id()
    click.echo(f"当前用户: {user_id}")

    # 获取项目
    project_manager = ProjectManager(user_id)

    if project:
        # 使用指定项目
        project_obj = project_manager.get_project(project)
        if not project_obj:
            click.echo(f"❌ 项目不存在: {project}", err=True)
            click.echo("提示: 运行 './mas project list' 查看所有项目", err=True)
            return
    else:
        # 使用当前项目
        project_obj = project_manager.get_current_project()
        if not project_obj:
            click.echo("❌ 未设置当前项目", err=True)
            click.echo("请先运行: ./mas project create 或 ./mas project use <name>", err=True)
            return

    click.echo(f"当前项目: {project_obj.project_name}")
    click.echo(f"项目描述: {project_obj.description or 'N/A'}\n")

    # 创建任务
    task = Task(
        task_id=str(uuid.uuid4()),
        title=title,
        description=description
    )

    # 创建项目级会话管理器
    session_manager = SessionManager.get_project_session_manager(
        user_id=user_id,
        project_name=project_obj.project_name
    )
    session = session_manager.create_session()
    session.add_task(task)

    click.echo(f"任务ID: {task.task_id}")
    click.echo(f"会话ID: {session.session_id}")
    click.echo(f"交互模式: {'启用' if interactive else '禁用'}\n")

    # 获取项目上下文
    project_context = {
        'project_name': project_obj.project_name,
        'workspace_path': str(project_manager.get_project_workspace(project_obj.project_name)),
        'artifacts_path': str(project_manager.get_project_artifacts_dir(project_obj.project_name)),
        'docs_path': str(project_manager.get_project_docs_dir(project_obj.project_name)),
        'sessions_path': str(project_manager.get_project_sessions_dir(project_obj.project_name))
    }

    click.echo(f"项目工作空间: {project_context['workspace_path']}\n")

    # 加载Agent（传递项目上下文）
    agents = _load_agents(user_id, project_context)

    if not agents:
        click.echo("❌ 无法加载Agent，请先注册Agent", err=True)
        return

    click.echo(f"✓ 已加载 {len(agents)} 个Agent\n")

    # 创建人工输入回调函数
    def human_input_callback(task: Task, agent_name: str, reason: str) -> Dict[str, Any]:
        """
        人工输入回调函数

        当Agent需要人工介入时调用
        """
        return _prompt_human_decision(task, agent_name, reason)

    # 创建Orchestrator（根据交互模式选择）
    try:
        if interactive:
            # 使用交互式Orchestrator
            orchestrator = InteractiveOrchestrator(
                config={'max_iterations': 10},
                session_manager=session_manager,
                use_registration=True
            )

            # 设置Agent的项目上下文
            for agent in orchestrator.agents.values():
                agent.set_project_context(project_context)

            click.echo("🎮 交互模式已启用 - 你可以实时查看和介入Agent工作\n")

            # 执行交互式工作流
            result = orchestrator.execute_workflow_interactive(
                task=task,
                session=session,
                auto_save=True
            )
        else:
            # 使用协作式Orchestrator（原有逻辑）
            orchestrator = CollaborativeOrchestrator(
                agents=agents,
                max_iterations_per_agent=5,
                max_dispute_rounds=3,
                human_input_callback=human_input_callback
            )

            result = orchestrator.execute(task)

        # 保存会话
        if result['success']:
            session.status = "completed"
        else:
            session.status = "failed"

        session_manager.save_session(session)

        # 显示结果
        click.echo("\n" + "=" * 80)
        if result['success']:
            click.echo("✅ 工作流执行成功")
        else:
            click.echo("❌ 工作流执行失败")
        click.echo("=" * 80)

        click.echo(f"\n消息: {result['message']}")
        click.echo(f"最终状态: {result.get('final_status', 'unknown')}")
        click.echo(f"\n会话已保存: sessions/{session.session_id}.json")
        click.echo(f"查看详情: ./mas task show {session.session_id[:8]}")

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


def _load_agents(user_id: str, project_context: Dict[str, Any]):
    """
    从注册系统加载Agent（支持用户层和项目上下文）

    Args:
        user_id: 用户ID
        project_context: 项目上下文（workspace_path等）

    Returns:
        List[BaseAgent]: Agent列表
    """
    # 优先从用户的Agent目录加载
    registration = AgentRegistration(user_id=user_id)

    # Agent配置（注册名 → Agent类）
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
    loaded_count = 0

    for registered_name, agent_class in agent_configs:
        try:
            # 加载配置和元数据
            config = registration.load_config(registered_name)
            metadata = None

            if config:
                # 从用户Agent加载
                click.echo(f"  ✓ 加载用户Agent: {registered_name}")
                loaded_count += 1
                # 加载元数据（获取agent_id）
                metadata = registration.load_metadata(registered_name)
            else:
                # 回退到全局Agent
                global_registration = AgentRegistration()  # 不传user_id
                config = global_registration.load_config(registered_name)
                if config:
                    click.echo(f"  ✓ 加载全局Agent: {registered_name}")
                    loaded_count += 1
                    metadata = global_registration.load_metadata(registered_name)

            if config:
                # 创建Agent实例（传递项目上下文）
                agent = agent_class(
                    name=config.get('name', registered_name),
                    config=config
                )

                # 设置agent_id（用于记忆目录命名）
                if metadata and 'agent_id' in metadata:
                    agent.agent_id = metadata['agent_id']
                else:
                    # 向后兼容：如果没有agent_id，使用name
                    agent.agent_id = agent.name

                # 设置项目上下文（Agent可以访问项目workspace）
                if hasattr(agent, 'set_project_context'):
                    agent.set_project_context(project_context)
                else:
                    # 如果Agent没有set_project_context方法，直接设置属性
                    agent.project_context = project_context

                agents.append(agent)
            else:
                # 使用默认实例
                click.echo(f"  ⚠️  使用默认Agent: {registered_name}")
                agent = agent_class()
                agent.agent_id = registered_name
                agent.project_context = project_context
                agents.append(agent)

        except Exception as e:
            click.echo(f"  ⚠️  加载 {registered_name} 失败: {e}", err=True)
            # 使用默认实例
            agent = agent_class()
            agent.agent_id = registered_name
            agent.project_context = project_context
            agents.append(agent)

    click.echo(f"\n已加载 {loaded_count}/{len(agent_configs)} 个配置的Agent")

    return agents


def _prompt_human_decision(task: Task, agent_name: str, reason: str) -> Dict[str, Any]:
    """
    提示用户做出决策

    Args:
        task: 任务对象
        agent_name: 当前Agent名称
        reason: 需要介入的原因

    Returns:
        Dict: 用户决策
    """
    click.echo("\n" + "=" * 80)
    click.echo("🙋 需要人工决策")
    click.echo("=" * 80)
    click.echo(f"Agent: {agent_name}")
    click.echo(f"原因: {reason}")
    click.echo("\n可用操作:")
    click.echo("  1. continue  - 继续执行下一个Agent")
    click.echo("  2. retry     - 重试当前Agent")
    click.echo("  3. skip      - 跳过当前Agent")
    click.echo("  4. abort     - 终止任务")
    click.echo("  5. feedback  - 提供反馈后继续")
    click.echo("=" * 80)

    while True:
        action = click.prompt("\n请选择操作", type=str, default="continue")
        action = action.strip().lower()

        if action in ['continue', 'retry', 'skip', 'abort']:
            return {
                'action': action,
                'instruction': ''
            }

        elif action == 'feedback':
            feedback = click.prompt("请输入反馈内容", type=str)
            return {
                'action': 'continue',
                'instruction': feedback
            }

        else:
            click.echo(f"❌ 无效操作: {action}，请重新选择")


@workflow.command()
@click.argument('session_id', required=False)
@click.option('--latest', is_flag=True, help='监控最新会话')
@click.option('--interval', default=2, help='刷新间隔（秒）')
def monitor(session_id: str, latest: bool, interval: int):
    """
    实时监控工作流执行

    示例：
    \b
    # 监控最新会话
    workflow monitor --latest

    \b
    # 监控指定会话
    workflow monitor 084760cf
    """
    import time
    import json
    from pathlib import Path

    sessions_dir = Path('sessions')

    if not sessions_dir.exists():
        click.echo("❌ 没有找到会话目录", err=True)
        return

    # 查找会话文件
    if latest:
        session_files = sorted(sessions_dir.glob('*.json'), key=lambda x: x.stat().st_mtime, reverse=True)
        if not session_files:
            click.echo("❌ 没有找到任何会话", err=True)
            return
        session_file = session_files[0]
    elif session_id:
        matching_files = [f for f in sessions_dir.glob('*.json') if f.stem.startswith(session_id)]
        if not matching_files:
            click.echo(f"❌ 没有找到会话: {session_id}", err=True)
            return
        session_file = matching_files[0]
    else:
        click.echo("❌ 请指定会话ID或使用 --latest", err=True)
        return

    click.echo(f"📊 监控会话: {session_file.stem[:16]}...")
    click.echo(f"刷新间隔: {interval}秒")
    click.echo("按 Ctrl+C 退出\n")

    last_artifact_count = 0

    try:
        while True:
            # 读取会话
            with open(session_file, 'r', encoding='utf-8') as f:
                session = json.load(f)

            # 获取任务
            tasks = session.get('tasks', {})
            if not tasks:
                click.echo("⚠️  会话中没有任务")
                time.sleep(interval)
                continue

            task = list(tasks.values())[0]

            # 显示状态
            click.echo(f"\r状态: {task.get('status', 'unknown')} | " +
                      f"当前Agent: {task.get('current_agent', 'N/A')} | " +
                      f"产物数: {len(task.get('artifacts', []))}", nl=False)

            # 检查是否有新产物
            artifacts = task.get('artifacts', [])
            if len(artifacts) > last_artifact_count:
                # 显示新产物
                for artifact in artifacts[last_artifact_count:]:
                    click.echo(f"\n\n{'='*80}")
                    click.echo(f"📦 新产物: {artifact.get('agent', 'Unknown')} - {artifact.get('type', 'unknown')}")
                    click.echo(f"{'='*80}")

                    content = artifact.get('content', {})

                    if artifact.get('type') == 'requirement_analysis':
                        click.echo(f"需求总结: {content.get('requirement_summary', 'N/A')[:200]}")
                        click.echo(f"清晰度: {content.get('clarity_score', 'N/A')}/10")
                        click.echo(f"完整度: {content.get('completeness_score', 'N/A')}/10")

                        questions = content.get('questions', [])
                        if questions:
                            click.echo(f"\n澄清问题 ({len(questions)}个):")
                            for i, q in enumerate(questions[:3], 1):
                                click.echo(f"  {i}. {q}")
                    else:
                        click.echo(f"内容: {str(content)[:200]}...")

                last_artifact_count = len(artifacts)

            # 检查是否完成
            if task.get('status') in ['completed', 'rejected', 'failed']:
                click.echo(f"\n\n✅ 任务已结束: {task.get('status')}")
                break

            time.sleep(interval)

    except KeyboardInterrupt:
        click.echo("\n\n⏹️  监控已停止")


if __name__ == '__main__':
    workflow()
