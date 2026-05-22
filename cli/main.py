#!/usr/bin/env python3
"""
Multi-Agent Dev System CLI

主命令行入口，集成所有子命令
"""
import click
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cli.user_commands import user
from cli.project_commands import project
from cli.agent_commands import agent
from cli.task_commands import task
from cli.workflow_commands import workflow
from cli.import_commands import import_group
from cli.export_commands import export_group
from cli.progress_commands import progress_group


@click.group()
@click.version_option(version='1.0.0', prog_name='multi-agent-dev-system')
def cli():
    """
    Multi-Agent Dev System - AI驱动的自动化软件开发协作平台

    使用示例：
    \b
      # 用户管理
      cli user init --username alice
      cli user whoami
      cli user list

      # 项目管理
      cli project create --name todo-app
      cli project list
      cli project use todo-app

      # 项目导入
      cli import git --url https://github.com/user/repo.git --name my-project
      cli import dir --path /path/to/project --name my-project
      cli import package --file backup.mas --name restored-project
      cli import templates

      # 项目导出
      cli export package todo-app --output backup.mas
      cli export git todo-app --remote https://github.com/user/repo.git
      cli export report todo-app --format markdown

      # 进度管理
      cli progress show todo-app
      cli progress tasks todo-app
      cli progress task-create todo-app --title "实现API" --phase development --agent Developer

      # Agent管理
      cli agent list
      cli agent register --method template --name pm1 --template product_manager
      cli agent show pm1

      # 任务管理
      cli task list --project todo-app
      cli task show --latest

      # 交互式工作流
      cli workflow run --project todo-app --title "添加功能"
      cli workflow monitor --latest
    """
    pass


# 注册子命令组
cli.add_command(user)
cli.add_command(project)
cli.add_command(agent)
cli.add_command(task)
cli.add_command(workflow)
cli.add_command(import_group)
cli.add_command(export_group)
cli.add_command(progress_group)


if __name__ == '__main__':
    cli()
