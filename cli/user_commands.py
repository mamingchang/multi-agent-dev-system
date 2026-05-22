"""
用户管理CLI命令
"""
import click
import sys
from pathlib import Path
from tabulate import tabulate

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.user_manager import UserManager


@click.group()
def user():
    """用户管理命令"""
    pass


@user.command()
@click.option('--username', prompt='用户名', help='用户名')
@click.option('--email', prompt='邮箱（可选）', default='', help='邮箱地址')
def init(username: str, email: str):
    """
    初始化用户（首次使用）

    示例：
    \b
    user init --username alice --email alice@example.com
    """
    manager = UserManager()

    try:
        user_obj = manager.create_user(
            username=username,
            email=email if email else None
        )

        # 设置为当前用户
        manager.set_current_user(user_obj.user_id)

        click.echo(f"✓ 用户创建成功: {username}")
        click.echo(f"  用户ID: {user_obj.user_id}")
        click.echo(f"  邮箱: {user_obj.email or 'N/A'}")
        click.echo(f"  已设置为当前用户")

    except ValueError as e:
        click.echo(f"✗ 创建失败: {e}", err=True)


@user.command()
def whoami():
    """
    查看当前用户

    示例：
    \b
    user whoami
    """
    manager = UserManager()
    user_obj = manager.get_current_user()

    if not user_obj:
        click.echo("未设置当前用户")
        click.echo("请先运行: ./mas user init")
        return

    click.echo(f"当前用户: {user_obj.username}")
    click.echo(f"用户ID: {user_obj.user_id}")
    click.echo(f"邮箱: {user_obj.email or 'N/A'}")
    click.echo(f"创建时间: {user_obj.created_at}")


@user.command()
@click.argument('username')
def switch(username: str):
    """
    切换到指定用户

    示例：
    \b
    user switch alice
    """
    manager = UserManager()

    user_id = f"user_{username}"

    try:
        manager.set_current_user(user_id)
        click.echo(f"✓ 已切换到用户: {username}")

    except ValueError as e:
        click.echo(f"✗ 切换失败: {e}", err=True)


@user.command()
def list():
    """
    列出所有用户

    示例：
    \b
    user list
    """
    manager = UserManager()
    users = manager.list_users()

    if not users:
        click.echo("没有找到任何用户")
        click.echo("请先运行: ./mas user init")
        return

    # 获取当前用户
    current_user = manager.get_current_user()
    current_user_id = current_user.user_id if current_user else None

    # 准备表格数据
    rows = []
    for u in users:
        is_current = "✓" if u.user_id == current_user_id else ""
        rows.append([
            is_current,
            u.username,
            u.user_id,
            u.email or 'N/A',
            u.created_at[:19]
        ])

    headers = ['当前', '用户名', '用户ID', '邮箱', '创建时间']
    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
    click.echo(f"\n共 {len(users)} 个用户")


if __name__ == '__main__':
    user()
