"""
项目导出CLI命令

支持导出到多种格式：
- 项目包(.mas)
- Git仓库
- 进度报告(Markdown/HTML/JSON)
"""
import click
from pathlib import Path
import sys

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.project_exporter import ProjectExporter


@click.group(name='export')
def export_group():
    """项目导出命令组"""
    pass


@export_group.command(name='package')
@click.argument('project_name')
@click.option('--output', required=True, help='输出文件路径')
@click.option('--code-only', is_flag=True, help='只导出代码')
@click.option('--no-memories', is_flag=True, help='排除Agent记忆')
@click.option('--no-sessions', is_flag=True, help='排除会话记录')
@click.option('--compress-level', default=6, type=click.IntRange(0, 9), help='压缩级别(0-9)')
@click.option('--user', default='default_user', help='用户ID')
def export_to_package(project_name, output, code_only, no_memories, no_sessions, compress_level, user):
    """导出项目为项目包(.mas)"""
    exporter = ProjectExporter(user)

    result = exporter.export_to_package(
        project_name,
        output,
        code_only=code_only,
        no_memories=no_memories,
        no_sessions=no_sessions,
        compress_level=compress_level
    )

    if result['success']:
        click.echo(f"\n✅ 项目导出成功！")
        click.echo(f"输出文件: {result['output_file']}")
        click.echo(f"文件大小: {result['file_size'] / 1024 / 1024:.2f} MB")
        click.echo(f"\n包含内容:")
        for key, value in result['manifest']['contents'].items():
            status = '✓' if value else '✗'
            click.echo(f"  {status} {key}")
    else:
        click.echo(f"\n❌ 导出失败: {result['error']}", err=True)
        sys.exit(1)


@export_group.command(name='git')
@click.argument('project_name')
@click.option('--remote', required=True, help='远程仓库URL')
@click.option('--branch', default='main', help='分支名称')
@click.option('--code-only', is_flag=True, default=True, help='只推送代码（默认）')
@click.option('--user', default='default_user', help='用户ID')
def export_to_git(project_name, remote, branch, code_only, user):
    """导出项目到Git仓库"""
    exporter = ProjectExporter(user)

    result = exporter.export_to_git(project_name, remote, branch, code_only)

    if result['success']:
        click.echo(f"\n✅ 项目导出成功！")
        click.echo(f"远程仓库: {result['remote_url']}")
        click.echo(f"分支: {result['branch']}")
    else:
        click.echo(f"\n❌ 导出失败: {result['error']}", err=True)
        sys.exit(1)


@export_group.command(name='report')
@click.argument('project_name')
@click.option('--format', type=click.Choice(['markdown', 'html', 'json']), default='markdown', help='报告格式')
@click.option('--output', help='输出文件路径（可选，默认输出到终端）')
@click.option('--user', default='default_user', help='用户ID')
def export_report(project_name, format, output, user):
    """导出进度报告"""
    exporter = ProjectExporter(user)

    report = exporter.export_report(project_name, format)

    if report.startswith('错误'):
        click.echo(f"\n❌ {report}", err=True)
        sys.exit(1)

    if output:
        # 保存到文件
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        click.echo(f"\n✅ 报告已保存到: {output}")
    else:
        # 输出到终端
        click.echo(report)


if __name__ == '__main__':
    export_group()
