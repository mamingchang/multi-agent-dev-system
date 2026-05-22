"""
进度管理CLI命令

支持：
- 查看整体进度
- 查看阶段详情
- 管理任务
- 查看里程碑
- 生成报告
"""
import click
from pathlib import Path
import sys
from datetime import datetime

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.progress_tracker import ProgressTracker, Task


@click.group(name='progress')
def progress_group():
    """进度管理命令组"""
    pass


@progress_group.command(name='show')
@click.argument('project_name')
@click.option('--user', default='default_user', help='用户ID')
def show_progress(project_name, user):
    """查看项目整体进度"""
    tracker = ProgressTracker(project_name, user)
    statistics = tracker.get_statistics()

    click.echo(f"\n{'='*50}")
    click.echo(f"项目进度: {project_name}")
    click.echo(f"{'='*50}")

    # 整体进度
    overall = statistics['overall_progress']
    progress_bar = '█' * (overall // 5) + '░' * (20 - overall // 5)
    click.echo(f"\n整体进度: {overall}% {progress_bar}\n")

    # 阶段进度
    click.echo("阶段进度:")
    phases = tracker.data['phases']
    for phase in phases:
        status_icon = {
            'completed': '✅',
            'in_progress': '🔄',
            'pending': '⏳'
        }.get(phase['status'], '❓')

        click.echo(f"  {status_icon} {phase['display_name']:12} {phase['progress']:3}%  ({phase['agent']})")

    # 任务统计
    click.echo(f"\n任务统计:")
    tasks_summary = statistics['tasks_summary']
    click.echo(f"  已完成: {tasks_summary['completed']}")
    click.echo(f"  进行中: {tasks_summary['in_progress']}")
    click.echo(f"  待处理: {tasks_summary['pending']}")
    click.echo(f"  已阻塞: {tasks_summary['blocked']}")
    click.echo(f"  总计: {tasks_summary['total']}")


@progress_group.command(name='phase')
@click.argument('project_name')
@click.argument('phase_name')
@click.option('--user', default='default_user', help='用户ID')
def show_phase(project_name, phase_name, user):
    """查看阶段详情"""
    tracker = ProgressTracker(project_name, user)
    phase = tracker.get_phase_progress(phase_name)

    if not phase:
        click.echo(f"❌ 阶段不存在: {phase_name}", err=True)
        sys.exit(1)

    click.echo(f"\n阶段详情: {phase['display_name']}")
    click.echo(f"{'='*50}")
    click.echo(f"状态: {phase['status']}")
    click.echo(f"进度: {phase['progress']}%")
    click.echo(f"负责Agent: {phase['agent']}")

    if phase.get('start_time'):
        click.echo(f"开始时间: {phase['start_time']}")
    if phase.get('end_time'):
        click.echo(f"结束时间: {phase['end_time']}")

    # 显示该阶段的任务
    tasks = tracker.get_all_tasks(phase=phase_name)
    if tasks:
        click.echo(f"\n任务列表 ({len(tasks)}个):")
        for task in tasks:
            status_icon = {
                'completed': '✅',
                'in_progress': '🔄',
                'pending': '⏳',
                'blocked': '🚫'
            }.get(task['status'], '❓')
            click.echo(f"  {status_icon} [{task['id']}] {task['title']} ({task['progress']}%)")


@progress_group.command(name='tasks')
@click.argument('project_name')
@click.option('--phase', help='过滤阶段')
@click.option('--status', help='过滤状态')
@click.option('--agent', help='过滤Agent')
@click.option('--user', default='default_user', help='用户ID')
def list_tasks(project_name, phase, status, agent, user):
    """查看任务列表"""
    tracker = ProgressTracker(project_name, user)
    tasks = tracker.get_all_tasks(phase=phase, status=status, agent=agent)

    if not tasks:
        click.echo("没有找到任务")
        return

    click.echo(f"\n任务列表 ({len(tasks)}个):\n")
    for task in tasks:
        status_icon = {
            'completed': '✅',
            'in_progress': '🔄',
            'pending': '⏳',
            'blocked': '🚫'
        }.get(task['status'], '❓')

        click.echo(f"{status_icon} [{task['id']}] {task['title']}")
        click.echo(f"   阶段: {task['phase']} | 状态: {task['status']} | 进度: {task['progress']}%")
        click.echo(f"   负责人: {task['assigned_to']} | 优先级: {task['priority']}")
        if task.get('description'):
            click.echo(f"   描述: {task['description']}")
        click.echo()


@progress_group.command(name='task-create')
@click.argument('project_name')
@click.option('--title', required=True, help='任务标题')
@click.option('--phase', required=True, help='所属阶段')
@click.option('--priority', type=click.Choice(['low', 'medium', 'high', 'critical']), default='medium', help='优先级')
@click.option('--agent', required=True, help='负责Agent')
@click.option('--description', default='', help='任务描述')
@click.option('--user', default='default_user', help='用户ID')
def create_task(project_name, title, phase, priority, agent, description, user):
    """创建任务"""
    tracker = ProgressTracker(project_name, user)

    # 生成任务ID
    task_count = len(tracker.data['tasks'])
    task_id = f"task-{task_count + 1:03d}"

    task = Task(
        id=task_id,
        title=title,
        phase=phase,
        status='pending',
        priority=priority,
        assigned_to=agent,
        progress=0,
        created_at=datetime.now().isoformat(),
        description=description
    )

    tracker.create_task(task)
    click.echo(f"\n✅ 任务创建成功！")
    click.echo(f"任务ID: {task_id}")
    click.echo(f"标题: {title}")
    click.echo(f"阶段: {phase}")
    click.echo(f"负责人: {agent}")


@progress_group.command(name='task-update')
@click.argument('project_name')
@click.argument('task_id')
@click.option('--status', type=click.Choice(['pending', 'in_progress', 'completed', 'blocked']), help='状态')
@click.option('--progress', type=click.IntRange(0, 100), help='进度(0-100)')
@click.option('--priority', type=click.Choice(['low', 'medium', 'high', 'critical']), help='优先级')
@click.option('--user', default='default_user', help='用户ID')
def update_task(project_name, task_id, status, progress, priority, user):
    """更新任务"""
    tracker = ProgressTracker(project_name, user)

    updates = {}
    if status:
        updates['status'] = status
    if progress is not None:
        updates['progress'] = progress
    if priority:
        updates['priority'] = priority

    if not updates:
        click.echo("❌ 没有指定要更新的内容", err=True)
        sys.exit(1)

    tracker.update_task(task_id, updates)
    click.echo(f"\n✅ 任务更新成功！")
    click.echo(f"任务ID: {task_id}")
    for key, value in updates.items():
        click.echo(f"{key}: {value}")


@progress_group.command(name='phase-start')
@click.argument('project_name')
@click.argument('phase_name')
@click.option('--agent', help='负责Agent（可选，使用默认Agent）')
@click.option('--user', default='default_user', help='用户ID')
def start_phase(project_name, phase_name, agent, user):
    """开始一个阶段"""
    tracker = ProgressTracker(project_name, user)
    tracker.start_phase(phase_name, agent)
    click.echo(f"\n✅ 阶段已开始: {phase_name}")


@progress_group.command(name='phase-complete')
@click.argument('project_name')
@click.argument('phase_name')
@click.option('--user', default='default_user', help='用户ID')
def complete_phase(project_name, phase_name, user):
    """完成一个阶段"""
    tracker = ProgressTracker(project_name, user)
    tracker.complete_phase(phase_name)
    click.echo(f"\n✅ 阶段已完成: {phase_name}")


if __name__ == '__main__':
    progress_group()
