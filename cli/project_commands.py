"""
项目管理CLI命令
"""
import click
import sys
from pathlib import Path
from tabulate import tabulate
from datetime import datetime

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
def project():
    """项目管理命令"""
    pass


@project.command()
@click.option('--name', prompt='项目名称', help='项目名称')
@click.option('--description', prompt='项目描述（可选）', default='', help='项目描述')
@click.option('--agents', help='指定Agent列表（逗号分隔），如: requester,developer,tester')
def create(name: str, description: str, agents: str):
    """
    创建新项目

    示例：
    \b
    # 创建项目（使用默认Agent）
    project create --name todo-app --description "Todo待办事项应用"

    \b
    # 创建项目并指定Agent
    project create --name my-app --agents requester,developer,tester
    """
    user_id = get_current_user_id()
    manager = ProjectManager(user_id)

    # 解析agents参数
    agent_list = None
    if agents:
        agent_list = [a.strip() for a in agents.split(',')]

    try:
        proj = manager.create_project(
            project_name=name,
            description=description,
            agents=agent_list
        )

        # 设置为当前项目
        manager.set_current_project(name)

        click.echo(f"✓ 项目创建成功: {name}")
        click.echo(f"  项目ID: {proj.project_id}")
        click.echo(f"  描述: {proj.description or 'N/A'}")
        click.echo(f"  工作空间: {manager.get_project_workspace(name)}")

        if agent_list:
            click.echo(f"  配置的Agent: {', '.join(agent_list)}")
        else:
            click.echo(f"  配置的Agent: 使用默认（所有标准Agent）")

        click.echo(f"  已设置为当前项目")

    except ValueError as e:
        click.echo(f"✗ 创建失败: {e}", err=True)


@project.command()
def list():
    """
    列出所有项目

    示例：
    \b
    project list
    """
    user_id = get_current_user_id()
    manager = ProjectManager(user_id)

    projects = manager.list_projects()

    if not projects:
        click.echo("没有找到任何项目")
        click.echo("请先运行: ./mas project create")
        return

    # 获取当前项目
    current_project = manager.get_current_project()
    current_project_name = current_project.project_name if current_project else None

    # 准备表格数据
    rows = []
    for p in projects:
        is_current = "✓" if p.project_name == current_project_name else ""

        # 统计会话数
        sessions = manager.list_project_sessions(p.project_name)
        session_count = len(sessions)

        rows.append([
            is_current,
            p.project_name,
            p.status,
            session_count,
            p.description[:40] + '...' if len(p.description) > 40 else p.description,
            p.created_at[:19]
        ])

    headers = ['当前', '项目名称', '状态', '会话数', '描述', '创建时间']
    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
    click.echo(f"\n共 {len(projects)} 个项目")


@project.command()
@click.argument('name')
def show(name: str):
    """
    查看项目详情

    示例：
    \b
    project show todo-app
    """
    user_id = get_current_user_id()
    manager = ProjectManager(user_id)

    proj = manager.get_project(name)

    if not proj:
        click.echo(f"❌ 项目不存在: {name}", err=True)
        return

    click.echo("=" * 80)
    click.echo(f"项目: {proj.project_name}")
    click.echo("=" * 80)
    click.echo(f"项目ID: {proj.project_id}")
    click.echo(f"所有者: {proj.owner}")
    click.echo(f"状态: {proj.status}")
    click.echo(f"描述: {proj.description or 'N/A'}")
    click.echo(f"创建时间: {proj.created_at}")
    click.echo(f"更新时间: {proj.updated_at}")

    if proj.tags:
        click.echo(f"标签: {', '.join(proj.tags)}")

    if proj.agents:
        click.echo(f"\n使用的Agent:")
        for agent in proj.agents:
            click.echo(f"  • {agent}")

    # 显示目录信息
    click.echo(f"\n目录:")
    click.echo(f"  工作空间: {manager.get_project_workspace(name)}")
    click.echo(f"  会话: {manager.get_project_sessions_dir(name)}")
    click.echo(f"  产物: {manager.get_project_artifacts_dir(name)}")
    click.echo(f"  文档: {manager.get_project_docs_dir(name)}")

    # 统计信息
    sessions = manager.list_project_sessions(name)
    click.echo(f"\n统计:")
    click.echo(f"  会话数: {len(sessions)}")

    # 工作空间文件
    workspace = manager.get_project_workspace(name)
    if workspace.exists():
        files = list(workspace.rglob("*"))
        file_count = len([f for f in files if f.is_file()])
        click.echo(f"  工作空间文件数: {file_count}")


@project.command()
@click.argument('name')
def use(name: str):
    """
    切换到指定项目

    示例：
    \b
    project use todo-app
    """
    user_id = get_current_user_id()
    manager = ProjectManager(user_id)

    try:
        manager.set_current_project(name)
        click.echo(f"✓ 已切换到项目: {name}")

    except ValueError as e:
        click.echo(f"✗ 切换失败: {e}", err=True)


@project.command()
def current():
    """
    查看当前项目

    示例：
    \b
    project current
    """
    user_id = get_current_user_id()
    manager = ProjectManager(user_id)

    proj = manager.get_current_project()

    if not proj:
        click.echo("未设置当前项目")
        click.echo("请先运行: ./mas project create 或 ./mas project use <name>")
        return

    click.echo(f"当前项目: {proj.project_name}")
    click.echo(f"描述: {proj.description or 'N/A'}")
    click.echo(f"状态: {proj.status}")


@project.command()
@click.argument('name')
def archive(name: str):
    """
    归档项目

    示例：
    \b
    project archive todo-app
    """
    user_id = get_current_user_id()
    manager = ProjectManager(user_id)

    try:
        proj = manager.archive_project(name)
        click.echo(f"✓ 项目已归档: {name}")

    except ValueError as e:
        click.echo(f"✗ 归档失败: {e}", err=True)


@project.command()
@click.argument('name')
def activate(name: str):
    """
    激活项目

    示例：
    \b
    project activate todo-app
    """
    user_id = get_current_user_id()
    manager = ProjectManager(user_id)

    try:
        proj = manager.activate_project(name)
        click.echo(f"✓ 项目已激活: {name}")

    except ValueError as e:
        click.echo(f"✗ 激活失败: {e}", err=True)


@project.command()
@click.argument('name')
@click.confirmation_option(prompt='确定要删除此项目吗？所有数据将被永久删除！')
def delete(name: str):
    """
    删除项目（谨慎使用）

    示例：
    \b
    project delete todo-app
    """
    user_id = get_current_user_id()
    manager = ProjectManager(user_id)

    try:
        manager.delete_project(name)
        click.echo(f"✓ 项目已删除: {name}")

    except ValueError as e:
        click.echo(f"✗ 删除失败: {e}", err=True)


@project.command()
@click.argument('name')
def sessions(name: str):
    """
    查看项目的所有会话

    示例：
    \b
    project sessions todo-app
    """
    user_id = get_current_user_id()
    manager = ProjectManager(user_id)

    sessions_list = manager.list_project_sessions(name)

    if not sessions_list:
        click.echo(f"项目 {name} 没有会话记录")
        return

    # 准备表格数据
    rows = []
    for s in sessions_list:
        session_id = s.get('session_id', 'N/A')[:16] + '...'
        status = s.get('status', 'N/A')
        tasks = s.get('tasks', {})
        task_count = len(tasks)
        created_at = s.get('created_at', 'N/A')[:19]

        rows.append([
            session_id,
            status,
            task_count,
            created_at
        ])

    headers = ['会话ID', '状态', '任务数', '创建时间']
    click.echo(f"项目: {name}")
    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
    click.echo(f"\n共 {len(sessions_list)} 个会话")


@project.command(name='add-agent')
@click.argument('project_name')
@click.option('--agent', required=True, help='Agent名称')
@click.option('--from-user', help='使用其他用户的公开Agent（格式：user_id）')
def add_agent(project_name: str, agent: str, from_user: str):
    """
    添加Agent到项目

    示例：
    \b
    # 添加自己的Agent
    project add-agent my-app --agent developer

    \b
    # 使用其他用户的公开Agent
    project add-agent my-app --agent devops --from-user user_bob
    """
    user_id = get_current_user_id()
    manager = ProjectManager(user_id)

    try:
        # 构建agent_source
        if from_user:
            agent_source = f"{from_user}_{agent}"
        else:
            agent_source = None

        success = manager.add_agent_to_project(project_name, agent, agent_source)

        if success:
            if from_user:
                click.echo(f"✓ 已添加Agent: {agent} (来自用户 {from_user})")
            else:
                click.echo(f"✓ 已添加Agent: {agent}")
        else:
            click.echo(f"⚠️  Agent已存在: {agent}")

    except ValueError as e:
        click.echo(f"✗ 添加失败: {e}", err=True)


@project.command(name='remove-agent')
@click.argument('project_name')
@click.option('--agent', required=True, help='Agent名称')
def remove_agent(project_name: str, agent: str):
    """
    从项目移除Agent

    示例：
    \b
    project remove-agent my-app --agent developer
    """
    user_id = get_current_user_id()
    manager = ProjectManager(user_id)

    try:
        success = manager.remove_agent_from_project(project_name, agent)

        if success:
            click.echo(f"✓ 已移除Agent: {agent}")
        else:
            click.echo(f"⚠️  Agent不存在: {agent}")

    except ValueError as e:
        click.echo(f"✗ 移除失败: {e}", err=True)


@project.command(name='list-agents')
@click.argument('project_name')
def list_agents(project_name: str):
    """
    列出项目的所有Agent

    示例：
    \b
    project list-agents my-app
    """
    user_id = get_current_user_id()
    manager = ProjectManager(user_id)

    agents = manager.list_project_agents(project_name)

    if not agents:
        click.echo(f"项目 {project_name} 没有配置Agent")
        click.echo("提示: 使用 'project add-agent' 添加Agent")
        return

    click.echo(f"项目: {project_name}")
    click.echo(f"配置的Agent ({len(agents)}个):\n")

    for agent_id in agents:
        # 解析agent_id
        if '_' in agent_id and agent_id.count('_') >= 2:
            # 格式: user_xxx_agent_name
            parts = agent_id.split('_')
            user_part = '_'.join(parts[:-1])
            agent_name = parts[-1]
            click.echo(f"  • {agent_name} (来自 {user_part})")
        else:
            click.echo(f"  • {agent_id}")


@project.command(name='update-agents')
@click.argument('project_name')
@click.option('--agents', required=True, help='Agent列表（逗号分隔），如: requester,developer,tester')
def update_agents(project_name: str, agents: str):
    """
    更新项目的Agent配置（替换现有配置）

    示例：
    \b
    # 更新Agent列表
    project update-agents my-app --agents requester,developer,tester,devops
    """
    user_id = get_current_user_id()
    manager = ProjectManager(user_id)

    try:
        # 解析Agent列表
        agent_list = [a.strip() for a in agents.split(',') if a.strip()]

        if not agent_list:
            click.echo("✗ Agent列表不能为空", err=True)
            return

        # 获取项目
        proj = manager.get_project(project_name)
        if not proj:
            click.echo(f"✗ 项目不存在: {project_name}", err=True)
            return

        # 更新Agent列表
        proj.agents = agent_list
        proj.updated_at = datetime.now().isoformat()
        manager._save_project(proj)

        click.echo(f"✓ 已更新项目Agent配置")
        click.echo(f"  新的Agent列表: {', '.join(agent_list)}")

    except Exception as e:
        click.echo(f"✗ 更新失败: {e}", err=True)



if __name__ == '__main__':
    project()
