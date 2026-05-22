"""
Agent管理CLI命令

提供命令行接口来管理Agent的注册、更新、注销

命令：
- agent register: 注册新Agent
- agent list: 列出所有Agent
- agent show: 显示Agent详情
- agent update: 更新Agent配置
- agent unregister: 注销Agent

改进：
- 支持用户层：Agent属于当前用户
- 向后兼容：如果未设置用户，使用全局目录
"""
import click
import yaml
import sys
from pathlib import Path
from tabulate import tabulate

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.registration import AgentRegistration
from src.user_manager import UserManager


def get_current_user_id():
    """获取当前用户ID（如果有）"""
    manager = UserManager()
    user = manager.get_current_user()
    return user.user_id if user else None


@click.group()
def agent():
    """Agent管理命令"""
    pass


@agent.command()
@click.option('--method', type=click.Choice(['template', 'interactive', 'file', 'existing']),
              default='template', help='注册方式')
@click.option('--name', help='Agent名称')
@click.option('--template', help='模板名称（method=template时使用）')
@click.option('--file', type=click.Path(exists=True), help='YAML配置文件路径（method=file时使用）')
@click.option('--source', help='源Agent名称（method=existing时使用）')
@click.option('--override', multiple=True, help='覆盖配置项，格式：key=value')
@click.option('--visibility', type=click.Choice(['private', 'shared', 'public']),
              default='private', help='可见性')
def register(method, name, template, file, source, override, visibility):
    """
    注册新Agent

    示例：
    \b
    # 从模板创建
    agent register --method template --name pm1 --template product_manager

    \b
    # 交互式创建
    agent register --method interactive

    \b
    # 从文件导入
    agent register --method file --name my_agent --file config/my_agent.yaml

    \b
    # 从已有Agent复制
    agent register --method existing --name pm2 --source pm1

    \b
    # 公开Agent
    agent register --method template --name public_pm --template product_manager --visibility public
    """
    # 获取当前用户ID
    user_id = get_current_user_id()

    if user_id:
        click.echo(f"当前用户: {user_id}")
    else:
        click.echo("⚠️  未设置用户，Agent将保存到全局目录")
        click.echo("提示: 运行 './mas user init' 创建用户")

    registration = AgentRegistration(user_id=user_id)

    try:
        # 解析override参数
        overrides = {}
        for item in override:
            if '=' in item:
                key, value = item.split('=', 1)
                overrides[key] = value

        # 根据method调用不同的注册方法
        if method == 'template':
            if not name or not template:
                click.echo("错误：--name 和 --template 参数是必需的", err=True)
                return

            config = registration.register_from_template(name, template, overrides, visibility)
            click.echo(f"✓ 从模板 '{template}' 创建Agent '{name}' 成功")

        elif method == 'interactive':
            config = registration.register_interactive()
            click.echo(f"✓ Agent '{config['name']}' 注册成功")

        elif method == 'file':
            if not name or not file:
                click.echo("错误：--name 和 --file 参数是必需的", err=True)
                return

            config = registration.register_from_file(name, Path(file))
            click.echo(f"✓ 从文件导入Agent '{name}' 成功")

        elif method == 'existing':
            if not name or not source:
                click.echo("错误：--name 和 --source 参数是必需的", err=True)
                return

            config = registration.register_from_existing(name, source)
            click.echo(f"✓ 从Agent '{source}' 复制创建 '{name}' 成功")

        # 显示配置摘要
        click.echo(f"\n配置摘要：")
        click.echo(f"  名称: {config['name']}")
        click.echo(f"  角色: {config['role']}")
        click.echo(f"  描述: {config.get('description', 'N/A')}")
        if user_id:
            click.echo(f"  所有者: {user_id}")
        click.echo(f"  可见性: {visibility}")

    except ValueError as e:
        click.echo(f"错误：{e}", err=True)
    except Exception as e:
        click.echo(f"注册失败：{e}", err=True)


@agent.command()
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']), default='table',
              help='输出格式')
def list(format):
    """
    列出所有已注册的Agent

    示例：
    \b
    # 表格格式
    agent list

    \b
    # JSON格式
    agent list --format json

    \b
    # YAML格式
    agent list --format yaml
    """
    # 获取当前用户ID
    user_id = get_current_user_id()

    if user_id:
        click.echo(f"当前用户: {user_id}\n")

    registration = AgentRegistration(user_id=user_id)

    try:
        agents = registration.list_agents()

        if not agents:
            click.echo("没有已注册的Agent")
            if not user_id:
                click.echo("提示: 运行 './mas user init' 创建用户")
            return

        if format == 'table':
            # 表格格式
            headers = ['名称', '角色', '描述', '创建时间', '可见性']
            rows = []
            for a in agents:
                metadata = a.get('_metadata', {})
                visibility = metadata.get('visibility', 'N/A')
                created_at = a.get('metadata', {}).get('created_at', 'N/A')
                if created_at != 'N/A':
                    created_at = created_at[:19]

                rows.append([
                    a['name'],
                    a['role'],
                    (a.get('description', '')[:40] + '...') if len(a.get('description', '')) > 40 else a.get('description', 'N/A'),
                    created_at,
                    visibility
                ])
            click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
            click.echo(f"\n共 {len(agents)} 个Agent")

        elif format == 'json':
            import json
            click.echo(json.dumps(agents, indent=2, ensure_ascii=False))

        elif format == 'yaml':
            click.echo(yaml.dump(agents, allow_unicode=True, default_flow_style=False))

    except Exception as e:
        click.echo(f"列出Agent失败：{e}", err=True)


@agent.command()
@click.argument('agent_name')
@click.option('--format', type=click.Choice(['yaml', 'json']), default='yaml',
              help='输出格式')
def show(agent_name, format):
    """
    显示Agent详细配置

    示例：
    \b
    # YAML格式
    agent show pm1

    \b
    # JSON格式
    agent show pm1 --format json
    """
    user_id = get_current_user_id()
    registration = AgentRegistration(user_id=user_id)

    try:
        config = registration.load_config(agent_name)

        if not config:
            click.echo(f"Agent '{agent_name}' 不存在", err=True)
            return

        if format == 'yaml':
            click.echo(yaml.dump(config, allow_unicode=True, default_flow_style=False, sort_keys=False))
        elif format == 'json':
            import json
            click.echo(json.dumps(config, indent=2, ensure_ascii=False))

    except ValueError as e:
        click.echo(f"错误：{e}", err=True)
    except Exception as e:
        click.echo(f"显示Agent配置失败：{e}", err=True)


@agent.command()
@click.argument('agent_name')
@click.option('--set', multiple=True, help='设置配置项，格式：key=value')
@click.option('--file', type=click.Path(exists=True), help='从YAML文件更新')
def update(agent_name, set, file):
    """
    更新Agent配置

    示例：
    \b
    # 更新单个配置项
    agent update pm1 --set description="新的描述"

    \b
    # 更新多个配置项
    agent update pm1 --set llm.temperature=0.8 --set llm.max_tokens=8192

    \b
    # 从文件更新
    agent update pm1 --file updates.yaml
    """
    registration = AgentRegistration()

    try:
        updates = {}

        # 从--set参数解析更新
        for item in set:
            if '=' in item:
                key, value = item.split('=', 1)

                # 支持嵌套键（如 llm.temperature）
                keys = key.split('.')
                current = updates
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]

                # 尝试转换值类型
                try:
                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    elif value.replace('.', '', 1).isdigit():
                        value = float(value)
                except:
                    pass

                current[keys[-1]] = value

        # 从文件加载更新
        if file:
            with open(file, 'r', encoding='utf-8') as f:
                file_updates = yaml.safe_load(f)
                updates.update(file_updates)

        if not updates:
            click.echo("错误：没有提供更新内容", err=True)
            return

        # 执行更新
        config = registration.update_config(agent_name, updates)

        click.echo(f"✓ Agent '{agent_name}' 更新成功")
        click.echo(f"  版本: {config['metadata']['version']}")
        click.echo(f"  更新时间: {config['metadata']['updated_at']}")

    except ValueError as e:
        click.echo(f"错误：{e}", err=True)
    except Exception as e:
        click.echo(f"更新Agent失败：{e}", err=True)


@agent.command()
@click.argument('agent_name')
@click.option('--no-backup', is_flag=True, help='不备份配置文件')
@click.confirmation_option(prompt='确定要注销这个Agent吗？')
def unregister(agent_name, no_backup):
    """
    注销Agent

    示例：
    \b
    # 注销Agent（会备份配置）
    agent unregister pm1

    \b
    # 注销Agent（不备份）
    agent unregister pm1 --no-backup
    """
    registration = AgentRegistration()

    try:
        registration.unregister(agent_name, backup=not no_backup)
        click.echo(f"✓ Agent '{agent_name}' 已注销")

        if not no_backup:
            click.echo(f"  配置已备份到 config/agents/backups/")

    except ValueError as e:
        click.echo(f"错误：{e}", err=True)
    except Exception as e:
        click.echo(f"注销Agent失败：{e}", err=True)


if __name__ == '__main__':
    agent()
