"""
任务管理CLI命令（支持项目层）

查看任务执行状态和各个Agent的回复

改进：
- 支持--project参数过滤项目会话
- 自动检测会话所属项目
"""
import click
import json
import sys
from pathlib import Path
from datetime import datetime
from tabulate import tabulate

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.user_manager import UserManager
from src.project_manager import ProjectManager


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
def task():
    """任务管理命令"""
    pass


@task.command()
@click.option('--project', help='过滤指定项目的会话')
@click.option('--limit', default=10, help='显示最近N个会话')
def list(project, limit):
    """
    列出所有会话

    示例：
    \b
    # 列出所有会话
    task list

    \b
    # 列出指定项目的会话
    task list --project todo-app

    \b
    # 限制数量
    task list --limit 5
    """
    # 获取当前用户
    user_id = get_current_user_id()

    # 确定会话目录
    if project:
        # 项目级会话
        project_manager = ProjectManager(user_id)
        project_obj = project_manager.get_project(project)
        if not project_obj:
            click.echo(f"❌ 项目不存在: {project}", err=True)
            return

        sessions_dir = project_manager.get_project_sessions_dir(project)
        click.echo(f"📂 项目: {project}\n")
    else:
        # 所有项目的会话
        project_manager = ProjectManager(user_id)
        projects = project_manager.list_projects()

        if not projects:
            click.echo("❌ 没有找到任何项目", err=True)
            click.echo("提示: 运行 './mas project create' 创建项目", err=True)
            return

        # 收集所有项目的会话
        all_sessions = []
        for proj in projects:
            proj_sessions_dir = project_manager.get_project_sessions_dir(proj.project_name)
            if proj_sessions_dir.exists():
                for session_file in proj_sessions_dir.glob('*.json'):
                    all_sessions.append((proj.project_name, session_file))

        if not all_sessions:
            click.echo("没有找到任何会话")
            return

        # 按修改时间排序
        all_sessions.sort(key=lambda x: x[1].stat().st_mtime, reverse=True)
        all_sessions = all_sessions[:limit]

        sessions = []
        for project_name, session_file in all_sessions:
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session = json.load(f)

                # 获取任务数量
                task_count = len(session.get('tasks', {}))

                # 格式化时间
                created_at = session.get('created_at', '')[:19] if session.get('created_at') else 'N/A'

                sessions.append({
                    'session_id': session['session_id'][:8] + '...',
                    'project': project_name,
                    'status': session.get('status', 'N/A'),
                    'tasks': task_count,
                    'created_at': created_at
                })
            except Exception as e:
                click.echo(f"读取会话文件失败 {session_file}: {e}", err=True)

        # 显示表格
        headers = ['会话ID', '项目', '状态', '任务数', '创建时间']
        rows = [[s['session_id'], s['project'], s['status'], s['tasks'], s['created_at']] for s in sessions]

        click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
        click.echo(f"\n共 {len(sessions)} 个会话")
        return

    # 单个项目的会话列表
    if not sessions_dir.exists():
        click.echo("没有找到会话目录")
        return

    # 获取所有会话文件
    session_files = sorted(sessions_dir.glob('*.json'), key=lambda x: x.stat().st_mtime, reverse=True)

    if not session_files:
        click.echo("没有找到任何会话")
        return

    # 限制数量
    session_files = session_files[:limit]

    sessions = []
    for session_file in session_files:
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session = json.load(f)

            # 获取任务数量
            task_count = len(session.get('tasks', {}))

            # 格式化时间
            created_at = session.get('created_at', '')[:19] if session.get('created_at') else 'N/A'

            sessions.append({
                'session_id': session['session_id'][:8] + '...',
                'status': session.get('status', 'N/A'),
                'tasks': task_count,
                'created_at': created_at
            })
        except Exception as e:
            click.echo(f"读取会话文件失败 {session_file}: {e}", err=True)

    # 显示表格
    headers = ['会话ID', '状态', '任务数', '创建时间']
    rows = [[s['session_id'], s['status'], s['tasks'], s['created_at']] for s in sessions]

    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
    click.echo(f"\n共 {len(sessions)} 个会话")


@task.command()
@click.argument('session_id', required=False)
@click.option('--project', help='指定项目（如果未提供，搜索所有项目）')
@click.option('--latest', is_flag=True, help='显示最新的会话')
def show(session_id, project, latest):
    """
    显示会话详情和Agent回复

    示例：
    \b
    # 显示最新会话
    task show --latest

    \b
    # 显示指定项目的最新会话
    task show --project todo-app --latest

    \b
    # 显示指定会话
    task show 084760cf

    \b
    # 显示指定项目的指定会话
    task show 084760cf --project todo-app
    """
    # 获取当前用户
    user_id = get_current_user_id()
    project_manager = ProjectManager(user_id)

    # 查找会话文件
    session_file = None

    if project:
        # 在指定项目中查找
        project_obj = project_manager.get_project(project)
        if not project_obj:
            click.echo(f"❌ 项目不存在: {project}", err=True)
            return

        sessions_dir = project_manager.get_project_sessions_dir(project)

        if not sessions_dir.exists():
            click.echo(f"❌ 项目 {project} 没有会话目录", err=True)
            return

        if latest:
            session_files = sorted(sessions_dir.glob('*.json'), key=lambda x: x.stat().st_mtime, reverse=True)
            if not session_files:
                click.echo(f"❌ 项目 {project} 没有找到任何会话", err=True)
                return
            session_file = session_files[0]
        elif session_id:
            matching_files = [f for f in sessions_dir.glob('*.json') if f.stem.startswith(session_id)]
            if not matching_files:
                click.echo(f"❌ 在项目 {project} 中没有找到会话: {session_id}", err=True)
                return
            session_file = matching_files[0]
        else:
            click.echo("❌ 请指定会话ID或使用 --latest", err=True)
            return

    else:
        # 在所有项目中查找
        projects = project_manager.list_projects()

        if not projects:
            click.echo("❌ 没有找到任何项目", err=True)
            return

        if latest:
            # 查找最新的会话
            all_sessions = []
            for proj in projects:
                proj_sessions_dir = project_manager.get_project_sessions_dir(proj.project_name)
                if proj_sessions_dir.exists():
                    for sf in proj_sessions_dir.glob('*.json'):
                        all_sessions.append(sf)

            if not all_sessions:
                click.echo("❌ 没有找到任何会话", err=True)
                return

            session_file = max(all_sessions, key=lambda x: x.stat().st_mtime)

        elif session_id:
            # 在所有项目中搜索
            for proj in projects:
                proj_sessions_dir = project_manager.get_project_sessions_dir(proj.project_name)
                if proj_sessions_dir.exists():
                    matching_files = [f for f in proj_sessions_dir.glob('*.json') if f.stem.startswith(session_id)]
                    if matching_files:
                        session_file = matching_files[0]
                        project = proj.project_name
                        break

            if not session_file:
                click.echo(f"❌ 没有找到会话: {session_id}", err=True)
                return
        else:
            click.echo("❌ 请指定会话ID或使用 --latest", err=True)
            return

    # 读取会话
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            session = json.load(f)
    except Exception as e:
        click.echo(f"❌ 读取会话失败: {e}", err=True)
        return

    # 显示会话信息
    click.echo("=" * 80)
    click.echo(f"会话ID: {session['session_id']}")
    if project:
        click.echo(f"项目: {project}")
    click.echo(f"状态: {session.get('status', 'N/A')}")
    click.echo(f"创建时间: {session.get('created_at', 'N/A')}")
    click.echo(f"更新时间: {session.get('updated_at', 'N/A')}")
    click.echo("=" * 80)

    # 显示任务
    tasks = session.get('tasks', {})
    if not tasks:
        click.echo("\n没有任务")
        return

    for task_id, task in tasks.items():
        click.echo(f"\n任务: {task.get('title', 'N/A')}")
        click.echo(f"任务ID: {task_id}")
        click.echo(f"状态: {task.get('status', 'N/A')}")
        click.echo(f"当前Agent: {task.get('current_agent', 'N/A')}")
        click.echo(f"\n需求描述:")
        click.echo(task.get('description', 'N/A')[:200] + '...')

        # 显示Agent回复
        artifacts = task.get('artifacts', [])
        if artifacts:
            click.echo(f"\n" + "=" * 80)
            click.echo(f"Agent回复 (共{len(artifacts)}个)")
            click.echo("=" * 80)

            for i, artifact in enumerate(artifacts, 1):
                agent = artifact.get('agent', 'Unknown')
                artifact_type = artifact.get('type', 'unknown')
                timestamp = artifact.get('timestamp', '')[:19] if artifact.get('timestamp') else 'N/A'
                version = artifact.get('version', 1)

                click.echo(f"\n[{i}] {agent} - 版本{version} ({timestamp})")
                click.echo("-" * 80)

                content = artifact.get('content', {})

                if artifact_type == 'requirement_analysis':
                    click.echo(f"需求总结: {content.get('requirement_summary', 'N/A')}")
                    click.echo(f"清晰度评分: {content.get('clarity_score', 'N/A')}/10")
                    click.echo(f"完整度评分: {content.get('completeness_score', 'N/A')}/10")

                    click.echo(f"\n关键功能:")
                    for feature in content.get('key_features', [])[:5]:
                        click.echo(f"  • {feature}")

                    click.echo(f"\n约束条件:")
                    for constraint in content.get('constraints', [])[:5]:
                        click.echo(f"  • {constraint}")

                    questions = content.get('questions', [])
                    if questions:
                        click.echo(f"\n澄清问题 (共{len(questions)}个):")
                        for j, q in enumerate(questions[:5], 1):
                            click.echo(f"  {j}. {q}")
                        if len(questions) > 5:
                            click.echo(f"  ... 还有{len(questions) - 5}个问题")

                    click.echo(f"\n可行性评估:")
                    click.echo(f"  {content.get('feasibility', 'N/A')[:150]}...")

                    click.echo(f"\n建议:")
                    click.echo(f"  {content.get('recommendation', 'N/A')[:150]}...")

                else:
                    # 其他类型的artifact
                    click.echo(f"类型: {artifact_type}")
                    click.echo(f"内容: {str(content)[:200]}...")


@task.command()
@click.argument('session_id', required=False)
@click.option('--project', help='指定项目（如果未提供，搜索所有项目）')
@click.option('--latest', is_flag=True, help='显示最新的会话')
@click.option('--agent', help='只显示指定Agent的回复')
def agents(session_id, project, latest, agent):
    """
    显示各个Agent的状态和回复摘要

    示例：
    \b
    # 显示最新会话的所有Agent状态
    task agents --latest

    \b
    # 显示指定项目的最新会话
    task agents --project todo-app --latest

    \b
    # 只显示Requester的回复
    task agents --latest --agent Requester
    """
    # 获取当前用户
    user_id = get_current_user_id()
    project_manager = ProjectManager(user_id)

    # 查找会话文件（复用show命令的逻辑）
    session_file = None

    if project:
        # 在指定项目中查找
        project_obj = project_manager.get_project(project)
        if not project_obj:
            click.echo(f"❌ 项目不存在: {project}", err=True)
            return

        sessions_dir = project_manager.get_project_sessions_dir(project)

        if not sessions_dir.exists():
            click.echo(f"❌ 项目 {project} 没有会话目录", err=True)
            return

        if latest:
            session_files = sorted(sessions_dir.glob('*.json'), key=lambda x: x.stat().st_mtime, reverse=True)
            if not session_files:
                click.echo(f"❌ 项目 {project} 没有找到任何会话", err=True)
                return
            session_file = session_files[0]
        elif session_id:
            matching_files = [f for f in sessions_dir.glob('*.json') if f.stem.startswith(session_id)]
            if not matching_files:
                click.echo(f"❌ 在项目 {project} 中没有找到会话: {session_id}", err=True)
                return
            session_file = matching_files[0]
        else:
            click.echo("❌ 请指定会话ID或使用 --latest", err=True)
            return

    else:
        # 在所有项目中查找
        projects = project_manager.list_projects()

        if not projects:
            click.echo("❌ 没有找到任何项目", err=True)
            return

        if latest:
            # 查找最新的会话
            all_sessions = []
            for proj in projects:
                proj_sessions_dir = project_manager.get_project_sessions_dir(proj.project_name)
                if proj_sessions_dir.exists():
                    for sf in proj_sessions_dir.glob('*.json'):
                        all_sessions.append(sf)

            if not all_sessions:
                click.echo("❌ 没有找到任何会话", err=True)
                return

            session_file = max(all_sessions, key=lambda x: x.stat().st_mtime)

        elif session_id:
            # 在所有项目中搜索
            for proj in projects:
                proj_sessions_dir = project_manager.get_project_sessions_dir(proj.project_name)
                if proj_sessions_dir.exists():
                    matching_files = [f for f in proj_sessions_dir.glob('*.json') if f.stem.startswith(session_id)]
                    if matching_files:
                        session_file = matching_files[0]
                        project = proj.project_name
                        break

            if not session_file:
                click.echo(f"❌ 没有找到会话: {session_id}", err=True)
                return
        else:
            click.echo("❌ 请指定会话ID或使用 --latest", err=True)
            return

    # 读取会话
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            session = json.load(f)
    except Exception as e:
        click.echo(f"❌ 读取会话失败: {e}", err=True)
        return

    click.echo("=" * 80)
    click.echo(f"会话: {session['session_id'][:16]}... ({session.get('status', 'N/A')})")
    if project:
        click.echo(f"项目: {project}")
    click.echo("=" * 80)

    # 统计各Agent的回复
    tasks = session.get('tasks', {})
    if not tasks:
        click.echo("\n没有任务")
        return

    for task_id, task in tasks.items():
        click.echo(f"\n任务: {task.get('title', 'N/A')}")

        artifacts = task.get('artifacts', [])
        if not artifacts:
            click.echo("  没有Agent回复")
            continue

        # 按Agent分组
        agent_artifacts = {}
        for artifact in artifacts:
            agent_name = artifact.get('agent', 'Unknown')
            if agent_name not in agent_artifacts:
                agent_artifacts[agent_name] = []
            agent_artifacts[agent_name].append(artifact)

        # 过滤指定Agent
        if agent:
            agent_artifacts = {k: v for k, v in agent_artifacts.items() if k == agent}

        # 显示各Agent状态
        click.echo(f"\nAgent状态:")
        for agent_name, agent_arts in agent_artifacts.items():
            click.echo(f"\n  [{agent_name}] - {len(agent_arts)}个回复")

            # 显示最新回复的摘要
            latest_artifact = agent_arts[-1]
            content = latest_artifact.get('content', {})

            if latest_artifact.get('type') == 'requirement_analysis':
                click.echo(f"    总结: {content.get('requirement_summary', 'N/A')[:80]}...")
                click.echo(f"    评分: 清晰度{content.get('clarity_score', 'N/A')}/10, 完整度{content.get('completeness_score', 'N/A')}/10")
                questions = content.get('questions', [])
                if questions:
                    click.echo(f"    问题: {len(questions)}个澄清问题")
            else:
                click.echo(f"    类型: {latest_artifact.get('type', 'unknown')}")


if __name__ == '__main__':
    task()
