"""
项目导入CLI命令

支持从多种来源导入项目：
- Git仓库
- 本地目录
- 项目包(.mas)
- 模板
"""
import click
from pathlib import Path
import sys

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.project_importer import ProjectImporter


@click.group(name='import')
def import_group():
    """项目导入命令组"""
    pass


@import_group.command(name='git')
@click.option('--url', required=True, help='Git仓库URL')
@click.option('--name', required=True, help='项目名称')
@click.option('--branch', default=None, help='分支名称（可选）')
@click.option('--exclude', multiple=True, help='排除的文件模式（可多次指定）')
@click.option('--user', default='default_user', help='用户ID')
def import_from_git(url, name, branch, exclude, user):
    """从Git仓库导入项目"""
    importer = ProjectImporter(user)

    exclude_patterns = list(exclude) if exclude else None
    result = importer.import_from_git(url, name, branch, exclude_patterns)

    if result['success']:
        click.echo(f"\n✅ 项目导入成功！")
        click.echo(f"项目名称: {result['project_name']}")
        click.echo(f"工作空间: {result['workspace_path']}")
        click.echo(f"语言: {result['analysis']['language']}")
        if result['analysis']['framework']:
            click.echo(f"框架: {result['analysis']['framework']}")
        click.echo(f"文件数: {result['analysis']['file_count']}")
        click.echo(f"代码行数: {result['analysis']['code_lines']}")
        click.echo(f"初始进度: {result['progress']}%")
    else:
        click.echo(f"\n❌ 导入失败: {result['error']}", err=True)
        sys.exit(1)


@import_group.command(name='dir')
@click.option('--path', required=True, help='源目录路径')
@click.option('--name', required=True, help='项目名称')
@click.option('--exclude', multiple=True, help='排除的文件模式（可多次指定）')
@click.option('--user', default='default_user', help='用户ID')
def import_from_dir(path, name, exclude, user):
    """从本地目录导入项目"""
    importer = ProjectImporter(user)

    exclude_patterns = list(exclude) if exclude else None
    result = importer.import_from_dir(path, name, exclude_patterns)

    if result['success']:
        click.echo(f"\n✅ 项目导入成功！")
        click.echo(f"项目名称: {result['project_name']}")
        click.echo(f"工作空间: {result['workspace_path']}")
        click.echo(f"语言: {result['analysis']['language']}")
        if result['analysis']['framework']:
            click.echo(f"框架: {result['analysis']['framework']}")
        click.echo(f"文件数: {result['analysis']['file_count']}")
        click.echo(f"代码行数: {result['analysis']['code_lines']}")
        click.echo(f"初始进度: {result['progress']}%")
    else:
        click.echo(f"\n❌ 导入失败: {result['error']}", err=True)
        sys.exit(1)


@import_group.command(name='package')
@click.option('--file', required=True, help='项目包文件路径(.mas)')
@click.option('--name', required=True, help='项目名称')
@click.option('--code-only', is_flag=True, help='只导入代码（不导入进度和记忆）')
@click.option('--user', default='default_user', help='用户ID')
def import_from_package(file, name, code_only, user):
    """从项目包导入项目"""
    importer = ProjectImporter(user)

    result = importer.import_from_package(file, name, code_only)

    if result['success']:
        click.echo(f"\n✅ 项目导入成功！")
        click.echo(f"项目名称: {result['project_name']}")
        click.echo(f"工作空间: {result['workspace_path']}")
        click.echo(f"\n项目包信息:")
        click.echo(f"版本: {result['manifest']['version']}")
        click.echo(f"导出者: {result['manifest']['exported_by']}")
        click.echo(f"导出时间: {result['manifest']['exported_at']}")
    else:
        click.echo(f"\n❌ 导入失败: {result['error']}", err=True)
        sys.exit(1)


@import_group.command(name='template')
@click.option('--template', required=True, help='模板名称')
@click.option('--name', required=True, help='项目名称')
@click.option('--language', help='编程语言')
@click.option('--framework', help='框架')
@click.option('--user', default='default_user', help='用户ID')
def import_from_template(template, name, language, framework, user):
    """从模板创建项目"""
    importer = ProjectImporter(user)

    params = {}
    if language:
        params['language'] = language
    if framework:
        params['framework'] = framework

    result = importer.import_from_template(template, name, params)

    if result['success']:
        click.echo(f"\n✅ 项目创建成功！")
        click.echo(f"项目名称: {result['project_name']}")
        click.echo(f"工作空间: {result['workspace_path']}")
        click.echo(f"模板: {result['template']}")
    else:
        click.echo(f"\n❌ 创建失败: {result['error']}", err=True)
        sys.exit(1)


@import_group.command(name='templates')
@click.option('--user', default='default_user', help='用户ID')
def list_templates(user):
    """列出可用的项目模板"""
    importer = ProjectImporter(user)
    templates = importer.list_templates()

    if not templates:
        click.echo("没有可用的模板")
        return

    click.echo("\n可用的项目模板:\n")
    for template in templates:
        click.echo(f"📦 {template['name']}")
        click.echo(f"   名称: {template['display_name']}")
        click.echo(f"   描述: {template['description']}")
        if template['language']:
            click.echo(f"   语言: {template['language']}")
        if template['framework']:
            click.echo(f"   框架: {template['framework']}")
        click.echo()


if __name__ == '__main__':
    import_group()
